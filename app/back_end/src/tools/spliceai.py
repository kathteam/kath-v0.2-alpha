"""
SpliceAI Integration Module

This module provides functionality to integrate SpliceAI predictions into a genomic variant dataset.
It includes utilities for parsing variant data, generating VCF files, running SpliceAI, and merging
predicted splicing effects into a Pandas DataFrame.

Main Features:
--------------
- **Variant Parsing:** Extracts chromosome, position, reference, and alternative alleles from variant identifiers.
- **VCF File Handling:** Writes a VCF file from a DataFrame and parses SpliceAI-annotated VCF output.
- **SpliceAI Execution:** Runs SpliceAI to predict splicing effects and extracts relevant scores.
- **Data Integration:** Merges SpliceAI predictions into the input DataFrame.

Functions:
----------
- `parse_variant(variant_str)`: Parses a variant string to extract genomic coordinates and alleles.
- `write_vcf(dataframe, output_filename)`: Generates a VCF file from a DataFrame containing variant information.
- `run_spliceai(input_vcf, output_vcf, fasta, annotation)`: Executes SpliceAI on the input VCF file.
- `parse_spliceai_vcf(vcf_file)`: Parses a SpliceAI-annotated VCF file to extract delta scores and positions.
- `get_variant_value(row)`: Retrieves a variant identifier from a DataFrame row.
- `merge_spliceai_scores(data, spliceai_scores)`: Merges SpliceAI scores into a DataFrame based on variant values.
- `add_spliceai_eval_columns(data, fasta_path, spliceai_dir)`: Adds SpliceAI evaluation columns to a DataFrame.

Exceptions:
-----------
- `SpliceAIError`: Custom exception class for errors related to SpliceAI execution and processing.
"""
import os
import subprocess
import pandas as pd
from datetime import datetime
from src import env



class SpliceAIError(Exception):
    """Custom exception for SpliceAI errors."""


def parse_variant(variant_str):
    """
    Parses a variant string to extract chromosome, position, reference, and alternative alleles.

    This function processes a variant string in the format `chrom-pos-ref-alt` (e.g., `1-123-A-G`),
    splitting it into its respective components. If parsing fails, the function returns `None`.

    Args:
        variant_str (str): A string representing a genomic variant in the format `chrom-pos-ref-alt`.
    Returns:
        tuple: A tuple containing:
            - chrom (str): The chromosome part of the variant string.
            - pos (str): The position part of the variant string.
            - ref (str): The reference allele.
            - alt (str): The alternative allele.
            - `None` if the input format is invalid.
    """
    try:
        chrom, pos, ref, alt = variant_str.split("-")

        if not chrom or not pos or not ref or not alt:
            return None

        return chrom, pos, ref, alt
    except Exception:
        return None



def write_vcf(dataframe:pd.DataFrame, output_filename:str)-> str:
    """
    Writes a VCF (Variant Call Format) file without header
    from the given DataFrame.

    This function extracts specific variant information
    from a pandas DataFrame and writes it to a VCF file.
    For each row, the function extracts the first valid variant value
    found in these columns, parses it, and writes the corresponding VCF line.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing the variant data.
        output_filepath (str): The path where the VCF file will be saved.

    Returns:
        str: The file path where the VCF file has been written.
    """
    today_date = datetime.today().strftime("%Y%m%d")
    header = (
        "##fileformat=VCFv4.2\n"
        f"##fileDate={today_date}\n"
        "##reference=GRCh38\n"
        "##contig=<ID=6,length=171115067>\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    )
    with open(output_filename, 'w') as f:
        f.write(header)
        variant_columns = ["gen_pos"]
        for row in dataframe.itertuples(index=False):
            variant_value = next(
                (getattr(row, col) for col in variant_columns if hasattr(row, col)
                 and pd.notna(getattr(row, col)) and getattr(row, col) != "?"),
                None
            )
            if variant_value:
                parsed_variant = parse_variant(variant_value)
                if parsed_variant:
                    chrom, pos, ref, alt = parsed_variant
                    f.write(f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t.\t.\t.\n")
    return output_filename



def run_spliceai(input_vcf: str, ouput_vcf: str, fasta: str, annotation="grch38"):
    """
    Runs SpliceAI on the provided VCF file.

    This function constructs and executes a SpliceAI command to analyze
    the variants in the input VCF file and writes the results to a
    output VCF file.

    Required parameters for spliceai:
    -I: Input VCF with variants of interest.
    -O: Output VCF with SpliceAI predictions
    -R: Reference genome fasta file
    -A: Gene annotation file(grch37 or grch38)
    Optional parameters:
    !! Only for Nvidia graphics videocard
    -B: Number of predictions to collect before running models on
    them in batch. (default: 1 (don't batch))
    When setting the batching parameters, be mindful of the
    system and gpu memory of the machine you are running the script on.
    Feel free to experiment, but some reasonable -T numbers would be 64/128,
      increasing -B might further improve performance.
    Args:
        input_vcf (str): Path to the input VCF file.
        ouput_vcf (str): Path to the ouput VCF file.
        fasta (str): Path to the reference genome file in FASTA format.
        annotation (str): Annotation type (default is "grch38").

    Returns:
        str: Path to the output VCF file created.

    Raises:
        SpliceAIError: If the FASTA file is not found or if SpliceAI execution fails.
    """
    if not os.path.isfile(fasta):
        raise SpliceAIError(f"FASTA file not found: {fasta}")

    spliceai_command = [
        "spliceai",
        "-I", input_vcf,
        "-O", ouput_vcf,
        "-R", fasta,
        "-A", annotation,
        "-D", "500",
    ]

    if env.get_use_cuda():
        spliceai_command.extend(["-B", env.get_cuda_batch_size()])

    try:
        result = subprocess.run(spliceai_command, capture_output=True, text=True, check=True)
        if result.returncode != 0:
            raise SpliceAIError(f"SpliceAI failed: {result.stderr}")
    except Exception as exc:
        raise SpliceAIError(f"Error running SpliceAI: {exc}") from exc


def parse_spliceai_vcf(vcf_file: str)->dict:
    """
    Parses a VCF file to extract SpliceAI scores and maps them to genomic variants.

    This function reads a VCF file, extracts SpliceAI scores from the INFO field,
    and stores them in a dictionary using a variant key format: "chromosome-position-ref-alt".
    The extracted scores include delta scores for acceptor/donor gain/loss and their positions.
    Args:
       vcf_file(str): Path to the VCF file containing SpliceAI annotations.
    Returns:
        dict: A dictionary where keys are variant identifiers (e.g., "chr-pos-ref-alt")
        and values are dictionaries of SpliceAI scores.
    Raises:
        ValueError:If the VCF file is not found or an error occurs during parsing.
    """
    spliceai_scores = {}
    try:
        with open(vcf_file, 'r', encoding='utf-8') as vcf:
            for line in vcf:
                if line.startswith('#'):
                    continue
                columns = line.strip().split('\t')
                chrom, pos, ref, alt = columns[0], columns[1], columns[3], columns[4]
                variant_key = f"{chrom}-{pos}-{ref}-{alt}"
                info_field = columns[7]
                info_parts = info_field.split(";")
                scores = {}
                for part in info_parts:
                    if part.startswith("SpliceAI="):
                        spliceai_values = part.split("=")[1].split("|")
                        if all(is_valid_number(val) for val in spliceai_values[2:9]):
                            scores = {
                                "Delta score (acceptor gain)": float(spliceai_values[2]),
                                "Delta score (acceptor loss)": float(spliceai_values[3]),
                                "Delta score (donor gain)": float(spliceai_values[4]),
                                "Delta score (donor loss)": float(spliceai_values[5]),
                                "Delta position (acceptor gain)": int(columns[1]) + int(spliceai_values[6]),
                                "Delta position (acceptor loss)": int(columns[1]) + int(spliceai_values[7]),
                                "Delta position (donor gain)": int(columns[1]) + int(spliceai_values[8]),
                                "Delta position (donor loss)": int(columns[1]) + int(spliceai_values[9]),
                                "Max_Delta_Score": max(float(spliceai_values[2]), float(spliceai_values[3]),
                                                        float(spliceai_values[4]), float(spliceai_values[5]))
                            }
                        else:
                            scores = {
                                "Delta score (acceptor gain)": None,
                                "Delta score (acceptor loss)": None,
                                "Delta score (donor gain)": None,
                                "Delta score (donor loss)": None,
                                "Delta position (acceptor gain)": None,
                                "Delta position (acceptor loss)": None,
                                "Delta position (donor gain)": None,
                                "Delta position (donor loss)": None,
                                "Max_Delta_Score": None
                            }
                        spliceai_scores[variant_key] = scores
                        break
        return spliceai_scores
    except FileNotFoundError as e:
        raise ValueError(f"VCF file not found: {vcf_file}") from e
    except Exception as e:
        raise SpliceAIError(f"Error reading VCF file {vcf_file}: {e}") from e


def is_valid_number(value):
        """Returns True if the value can be converted to an int or float, else False."""
        try:
            float(value)
            return True
        except ValueError:
            return False


def merge_spliceai_scores(data:pd.DataFrame,spliceai_scores:dict)-> pd.DataFrame:
    """
    Merges SpliceAI scores into a given DataFrame based on variant values.

    This function extracts variant values from the input DataFrame, maps them to corresponding
    SpliceAI scores from the provided dictionary, and adds the SpliceAI score columns to the DataFrame.
    Args:
        data(pd.DataFrame): Input DataFrame containing variant information.
        spliceai_scores(dict): A dictionary mapping variant values to their corresponding SpliceAI scores.
    Returns:
        pd.DataFrame: A new DataFrame with SpliceAI score columns merged, maintaining the original data.
    Raises:
        SpliceAIError: If an error occurs during the merging process.
    """
    try:
        updated_data = data.copy()
        spliceai_map = updated_data['gen_pos'].map(spliceai_scores)
        for key in ["Delta score (acceptor gain)", "Delta score (acceptor loss)",
                    "Delta score (donor gain)", "Delta score (donor loss)",
                    "Delta position (acceptor gain)", "Delta position (acceptor loss)",
                    "Delta position (donor gain)", "Delta position (donor loss)",
                    "Max_Delta_Score"]:
            updated_data.loc[:, f"{key}_spliceai"] = spliceai_map.apply(lambda x: x.get(key, None) if isinstance(x, dict) else None)
        updated_data = updated_data.convert_dtypes()
        return updated_data
    except Exception as e:
        raise SpliceAIError(f"Error merging SpliceAI scores: {e}") from e


def add_spliceai_eval_columns(data: pd.DataFrame, fasta_path: str,spliceai_dir:str) -> pd.DataFrame:
    """
    Adds SpliceAI evaluation columns to the DataFrame with a `_spliceai` postfix.

    This function processes the input variant data by:
    1. Writing a VCF file from the DataFrame.
    2. Running the SpliceAI algorithm using the provided reference genome.
    3. Parsing the SpliceAI output to extract scores.
    4. Merging the SpliceAI scores back into the original DataFrame.

    Args:
        data (pd.DataFrame): DataFrame containing original variant information.
        fasta_path (str): Path to the reference genome file in FASTA format.
        spliceai_dir (str): Directory where SpliceAI input and output files will be stored.

    Returns:
        pd.DataFrame: DataFrame enriched with SpliceAI evaluation columns.

    """
    spliceai_input_vcf=os.path.join(spliceai_dir, "spliceai_input.vcf")
    spliceai_output_vcf=os.path.join(spliceai_dir, "spliceai_output.vcf")
    data_copy = data.copy()
    input_vcf = write_vcf(data_copy,spliceai_input_vcf)
    run_spliceai(input_vcf,spliceai_output_vcf, fasta_path)
    spliceai_scores = parse_spliceai_vcf(spliceai_output_vcf)

    return merge_spliceai_scores(data_copy,spliceai_scores)
