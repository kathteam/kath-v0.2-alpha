""" Module dedicated for refactoring collected data for further processing """

import os
import logging
import re


import pandas as pd
import xml.etree.ElementTree as ET
from pandas import DataFrame
from datetime import datetime

from pyliftover import LiftOver

from .constants import LOVD_PATH, GNOMAD_PATH, CLINVAR_PATH


def set_lovd_dtypes(df_dict: dict[str, pd.DataFrame]):
    """
    Convert data from LOVD format table to desired data format based on specified data types.

    :param dict[str, DataFrame] df_dict: Dictionary of tables saved as DataFrame
    """

    for table_name, frame in df_dict.items():
        try:
            frame = frame.convert_dtypes()
        except Exception as e:
            raise Exception(f"Failed to convert data types for LOVD table '{table_name}': {e}") from e
        df_dict[table_name] = frame

def set_gnomad_dtypes(df:pd.DataFrame):
    """
    Convert data from gnomAD format table to desired data format based on specified data types.

    :param DataFrame df: DataFrame containing gnomAD data
    :raises GnomadDtypeConversionError: if there is an error during data type conversion
    """
    try:
        df.convert_dtypes()
    except Exception as e:
        raise Exception(f"Failed to convert gnomAD data types: {e}") from e


def set_clinvar_dtypes(df:pd.DataFrame):
    """
    Convert data from ClinVar format table to desired data format based on specified data types.

    :param DataFrame df: DataFrame containing Clinvar data
    :raises ClinVarDtypeConversionError: if there is an error during data type conversion
    """
    try:
        df.convert_dtypes()
    except Exception as e:
        raise Exception(f"Failed to convert Clinvar data types: {e}") from e


def set_custom_file_dtypes(df:pd.DataFrame):
    """
    Convert data from custom_file format table to desired data format based on specified data types.

    :param DataFrame df: DataFrame containing custom_file data
    :raises DtypeConversionError: if there is an error during data type conversion
    """
    try:
        df.convert_dtypes()
    except Exception as e:
        raise Exception(f"Failed to convert custom_file data types: {e}") from e


def infer_type(value:str):
    """
    Infer the type of given value based on its content.
   This function attempts to convert the input value into an
   integer or a float based on its string representation. If the
   conversion is not possible, it returns the original value as a
   string.
    Args:
        value: The value to infer the type for, expected to be a string.

    Returns: The value converted to int, float, or string based on the inferred type.
    """
    try:
        if '.' in value or 'E-' in value or 'E+' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        return value  # Return as string if it cannot be converted


def parse_lovd(path: str = LOVD_PATH + '/lovd_data.txt', save_to: str = LOVD_PATH):
    """
    Converts data from text file with LOVD format to dictionary of tables.

    Key is name of table, value is data saved as pandas DataFrame.
    Notes for each table are displayed with log.

    **IMPORTANT:** It doesn't provide types for data inside. Use set_lovd_dtypes for this.

    :param str path: path to text file
    :returns: dictionary of tables
    :rtype: dict[str, tuple[DataFrame, list[str]]]
    """

    # Check if the file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"The file at {path} does not exist.")

    d = {}

    with open(path, encoding="UTF-8") as f:
        # skip header
        [f.readline() for _ in range(4)]  # pylint: disable=expression-not-assigned

        # Notify about parsing in log
        logging.info("Parsing file %s using parse_lovd.", path)

        while True:
            line = f.readline()

            if line == '':
                break

            table_name = line.split("##")[1].strip()

            # Save notes for each table
            notes = ""
            i = 1
            line = f.readline()
            while line.startswith("##"):
                notes += f"\n    - Note {i}: {line[3:-1]}"
                i += 1
                line = f.readline()

            # Log notes for each table
            if notes:
                logging.info("[%s]%s", table_name, notes)

            table_header = [column[3:-3] for column in line[:-1].split('\t')]
            frame = DataFrame([], columns=table_header)
            line = f.readline()
            while line != '\n':
                variables = [variable[1:-1] for variable in line[:-1].split('\t')]
                observation = DataFrame([variables], columns=table_header)
                frame = pd.concat([frame, observation], ignore_index=True)
                line = f.readline()

            for col in frame.columns:
                frame[col] = frame[col].apply(infer_type)

            d[table_name] = frame

            file_location = os.path.join(save_to, f"{table_name}.csv")
            if not os.path.exists(save_to):
                os.makedirs(save_to)
            frame.to_csv(file_location, index=False)

            # skip inter tables lines
            [f.readline() for _ in range(1)]  # pylint: disable=expression-not-assigned

    return d


def parse_gnomad(path:str=GNOMAD_PATH + '/gnomad_data.csv'):
    """
    Parses data from a gnomAD format text file into a pandas DataFrame.

    :param str path: path to the gnomAD data file
    :returns: pandas DataFrame containing gnomAD data
    :rtype: pd.DataFrame
    """

    # Check if the file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"The file at {path} does not exist.")
    logging.info("Parsing file %s using parse_gnomad.", path)
    try:
        gnomad_data = pd.read_csv(path, sep=',', encoding='UTF-8')
        return gnomad_data
    except Exception as e:
        logging.error("Error parsing gnomAD data: %s", str(e))
        raise e


def parse_custom_file(path: str):
    """
    Parses data from a file (CSV or XLSX) into a pandas DataFrame.

    :param str path: path to the data file
    :returns: pandas DataFrame containing data
    :rtype: pd.DataFrame
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"The file at {path} does not exist.")

    logging.info("Parsing file %s using parse_custom_file.", path)
    try:
        if path.endswith(".xlsx") or path.endswith(".xls"):
            data = pd.read_excel(path, engine="openpyxl")
        elif path.endswith(".csv"):
            data = pd.read_csv(path, sep=',', encoding='UTF-8')
        else:
            raise ValueError("Unsupported file format. Only .csv and .xlsx files are allowed.")
        return data
    except Exception as e:
        logging.error("Error parsing file data: %s", str(e))
        raise e


def clinvar_file_parse(path:str=CLINVAR_PATH + '/clinvar_data.csv'):
    """
    Parses data from a ClinVar format text file into a pandas DataFrame.

    :param str path: path to the ClinVar data file
    :returns: pandas DataFrame containing ClinVar data
    :rtype: pd.DataFrame
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"The file at {path} does not exist.")
    logging.info("Parsing file %s using parse_clinvar.", path)
    try:
        clinvar_data = pd.read_csv(path, sep=',', encoding='UTF-8')
        return clinvar_data
    except Exception as e:
        logging.error("Error parsing ClinVar data: %s", str(e))
        raise e


def from_clinvar_name_to_cdna_position(name:str):
    """
    Custom cleaner to extract cDNA position from Clinvar `name` variable.

    :param str name:
    :returns: extracted cDNA
    :rtype: str
    """

    start = name.find(":") + 1
    ends = {'del', 'delins', 'dup', 'ins', 'inv', 'subst'}

    if "p." in name:
        name = name[:name.index("p.") - 1].strip()

    end = len(name)

    for i in ends:
        if i in name:
            end = name.index(i) + len(i)
            break

    return name[start:end]


def lovd_fill_hg38(lovd: pd.DataFrame):
    """
    Fills missing hg38 values in the LOVD dataframe
    by converting hg19 values to hg38.
    New column 'hg38_gnomad_format' is added to store
    the converted positions in the format '6-position-ref-alt'.
    :param lovd: pandas DataFrame containing following columns:
               - 'VariantOnGenome/DNA': hg19 values.
               - 'VariantOnGenome/DNA/hg38': hg38 values.
    :return: None: Modifies the input DataFrame in-place by adding
                'hg38_gnomad_format' column.
    """

    if lovd.empty:
        return
    lovd.loc[:,'hg38_gnomad_format'] = lovd.loc[:,'VariantOnGenome/DNA/hg38'].replace('', pd.NA)
    missing_hg38_mask = lovd.loc[:,'hg38_gnomad_format'].isna()
    lovd.loc[missing_hg38_mask, 'hg38_gnomad_format'] = (lovd.loc[missing_hg38_mask,
                                                                'VariantOnGenome/DNA'].
                                                         apply(convert_hg19_if_missing))
    lovd.loc[:,'hg38_gnomad_format'] = lovd.loc[:,'hg38_gnomad_format'].apply(convert_to_gnomad_gen)


def convert_hg19_if_missing(hg19: str, lo = LiftOver('hg19', 'hg38')):
    """
    Converts hg19 variant to hg38 if hg38 is missing.
    :param hg19: a row from the DataFrame.
    :param lo: converter for genomic data between reference assemblies
    :return: hg38 value or a conversion of the hg19 value in the format 'g.positionref>alt'.
    """

    if pd.isna(hg19) or '_' in hg19:
        return "?"

    match = re.search(r'g\.(\d+)', hg19)
    if not match:
        return '?'

    position_str = match.group(1)
    new_pos = lo.convert_coordinate('chr6', int(position_str))[0][1]
    return f"g.{new_pos}{hg19[-3:]}"



def convert_to_gnomad_gen(variant: str):
    """
    converts a variant string from hg38 format
    to the format used by gnomAD ('6-position-ref-alt').
    :param variant: str: the variant in the format 'g.startRef>Alt'.
    :return: str: variant formatted as '6-position-ref-alt'
    or '?' if the input contains interval ranges or is invalid.
    """

    patterns = {
        'dup': re.compile(r'^g\.(\d+)dup$'),
        'del': re.compile(r'^g\.(\d+)del$'),
        'ref_alt': re.compile(r'^g\.(\d+)([A-Z])>([A-Z])$')
    }

    match = patterns['dup'].match(variant)
    if match:
        position = match.group(1)
        return f"6-{position}-dup"

    match = patterns['del'].match(variant)
    if match:
        position = match.group(1)
        return f"6-{position}-del"

    match = patterns['ref_alt'].match(variant)
    if match:
        position = match.group(1)
        ref = match.group(2)
        alt = match.group(3)
        return f"6-{position}-{ref}-{alt}"

    return "?"


def merge_gnomad_lovd(lovd:pd.DataFrame, gnomad:pd.DataFrame):
    """
    Merge LOVD and gnomAD dataframes on genomic positions.

    Parameters:
    lovd : pd.DataFrame
        LOVD dataframe.
    gnomAD : pd.DataFrame
        gnomAD dataframe.

    Returns:
    pd.DataFrame
        Merged dataframe with combined information from LOVD and gnomAD.
    """

    lovd_fill_hg38(lovd)
    gnomad.columns = [
        col + '_gnomad' if not col.endswith('_gnomad') else col
        for col in gnomad.columns
    ]

    merged_frame = pd.merge(
        lovd,
        gnomad,
        how="left",
        left_on="hg38_gnomad_format",
        right_on="variant_id_gnomad"
    )

    return merged_frame


def merge_custom_file(custom_data:pd.DataFrame, other_data:pd.DataFrame):
    """
    Merge custom data file and dataframes on genomic positions.

    Parameters:
    custom_data : pd.DataFrame
        custom_data dataframe.
    other_data : pd.DataFrame
        other_data DataFrame.

    Returns:
    pd.DataFrame
        Merged dataframe with combined information from custom file and dataframes.
    """

    custom_data_fill_hg38(custom_data)
    custom_data.columns = [
        col + '_custom' if not col.endswith('_custom') else col
        for col in custom_data.columns
    ]
    merged_frame = pd.merge(
        custom_data,
        other_data,
        how="outer",
        left_on="hg38_data_custom",
        right_on="hg38_gnomad_format"
    )
    return merged_frame


def custom_data_fill_hg38(custom_data: pd.DataFrame):
    """
    Adds a new column 'hg38_gnomad_format' to store
    the converted positions in the format '6-position-ref-alt',
    without modifying existing columns.

    :param custom_data: pandas DataFrame containing the following columns:
        - 'Chromosome': Chromosome number (e.g., 'chr6').
        - 'Position': Genomic position.
        - 'REF': Reference allele.
        - 'ALT': Alternate allele.

    :return: None (modifies the input DataFrame in-place)
    """

    if custom_data.empty:
        return
    custom_data["hg38_data"] = (
        custom_data["Chromosome"].str.replace("chr", "", regex=True) + "-" +
        custom_data["Position"].astype(str) + "-" +
        custom_data["REF"] + "-" +
        custom_data["ALT"]
    )
    return custom_data



def merge_lovd_clinvar(lovd:pd.DataFrame, clinvar:pd.DataFrame):
    """
    Merge LOVD and clinvar dataframes on genomic positions.

    Parameters:
    lovd : pd.DataFrame
        LOVD dataframe.
    clinvar : pd.DataFrame
        clinvar dataframe.

    Returns:
    pd.DataFrame
        Merged dataframe with combined information from LOVD and clinvar.
    """

    lovd_fill_hg38(lovd)
    clinvar.columns = [
        col + '_clinvar' if not col.endswith('_clinvar') else col
        for col in clinvar.columns
    ]

    merged_frame = pd.merge(
        lovd,
        clinvar,
        how="outer",
        left_on="hg38_gnomad_format",
        right_on="hg38_ID_clinvar"
    )

    merged_frame['VariantOnTranscript/DNA'] = merged_frame['VariantOnTranscript/DNA'].fillna(
        merged_frame['Name_clinvar'].astype(str).str.extract(r':(c\.[^ ]+)')[0]
    )

    merged_frame['VariantOnTranscript/Protein'] = merged_frame['VariantOnTranscript/Protein'].fillna(
        merged_frame['Name_clinvar'].astype(str).str.extract(r'\ \((p\.[^)]*)\)')[0]
    )

    merged_frame['malformed'] = merged_frame['Name_clinvar'].where(merged_frame['VariantOnTranscript/DNA'].isna())


    return merged_frame


def transform_spdi_to_format(df, spdi_column="Canonical SPDI", new_column="hg38_ID")->pd.DataFrame:
    """
    Transforms the SPDI format in a given column to the desired format.

    Args:
        df (pd.DataFrame): The DataFrame containing the SPDI column.
        spdi_column (str): The name of the column with SPDI format.
        new_column (str): The name of the new column to add with the formatted data.

    Returns:
        pd.DataFrame: The updated DataFrame with the new column.
    """
    df[spdi_column] = df[spdi_column].astype(str)
    df[new_column] = df[spdi_column].apply(format_spdi)
    return df


def format_spdi(row) -> str | None:
    """
    Formats a given SPDI (Sequence, Position, Deletion, Insertion) string into a standardized format.
    The function expects the input string in the form of "chromosome:position:ref:alt",
    where:
     - chromosome is the chromosome identifier, potentially prefixed with "NC_" and containing a version number (e.g., "NC_000001.11").
     - position is the position of the mutation on the chromosome.
     - ref is the reference nucleotide.
     - alt is the alternate nucleotide.

    The function processes the chromosome by removing the "NC_" prefix and any version number after the dot,
    and strips any leading zeroes. It then returns the string formatted as "chromosome-position-ref-alt".

    If the input string is not properly formatted or cannot be split into the four expected components, the function returns None.

    params: row (str): A string representing the SPDI, formatted as "chromosome:position:ref:alt".

    returns (str or None): A formatted string in the form "chromosome-position-ref-alt", or None if the input is invalid.
    """
    try:
        chromosome, position, ref, alt = row.split(":")
        chromosome = chromosome.replace("NC_", "").split(".")[0].lstrip("0")
        return f"{chromosome}-{position}-{ref}-{alt}"
    except ValueError:
        return None


def save_lovd_as_vcf(data:pd.DataFrame, save_to:str="./lovd.vcf"):
    """
    Gets hg38 variants from LOVD and saves as VCF file.
    :param DataFrame data: LOVD DataFrame with data
    :param str save_to: path where to save VCF file.
    """
    df = data["Variants_On_Genome"]
    if "VariantOnGenome/DNA/hg38" not in df.columns:
        raise ValueError("VariantOnGenome/DNA/hg38 is not in the LOVD DataFrame.")

    save_to_dir = os.path.dirname(save_to)
    if not os.path.exists(save_to_dir):
        os.makedirs(save_to_dir)

    with open(save_to, "w", encoding="UTF-8") as f:
        header = ("##fileformat=VCFv4.2\n"
                  "##contig=<ID=6,length=63719980>\n"
                  "#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO\n")
        f.write(header)
        for variant in df.loc[:, "VariantOnGenome/DNA/hg38"]:
            if len(variant) != 13 or variant[-2] != '>':
                logging.warning("Skipping variant %s", variant)
                continue
            record = ["6", variant[2:-3], ".", variant[-3], variant[-1], ".", ".", "."]

            f.write("\t".join(record))
            f.write("\n")


def find_popmax_in_gnomad(data:pd.DataFrame):
    """
    Finds popmax in gnomad data
    :param DataFrame data: Gnomad data.
    """

    population_mapping = {
            'afr': 'African/African American',
            'eas': 'East Asian',
            'asj': 'Ashkenazi Jew',
            'sas': 'South Asian',
            'nfe': 'European (non-Finnish)',
            'fin': 'European (Finnish)',
            'mid': 'Middle Eastern',
            'amr': 'Admixed American',
            'ami': "Amish",
            'remaining': 'Remaining',
            '': ''
        }
    population_ids = ['afr', 'eas', 'asj', 'sas', 'nfe', 'fin', 'mid', 'amr', 'ami', 'remaining']

    for i in range(data.shape[0]):
        max_pop = 0
        max_id = ''
        for population_id in population_ids:
            if data.loc[i, f'Allele_Frequency_{population_id}'] > max_pop:
                max_pop = data.loc[i, f'Allele_Frequency_{population_id}']
                max_id = population_id
        data.loc[i, 'Popmax'] = max_pop
        data.loc[i, 'Popmax population'] = population_mapping[max_id]


def parse_clinvar(rows: list[list[str]], variation_archives: list[ET.Element]):
    # Parse variation archives
    for element in variation_archives:
        row = []

        # Name
        name = element.attrib.get("VariationName")
        row.append(name if name is not None else "")

        # Gene(s)
        genes = [
            inner.attrib.get("Symbol")
            for inner in element.findall("ClassifiedRecord/SimpleAllele/GeneList/Gene")
            if inner.attrib.get("Symbol") is not None
        ]
        row.append("|".join(genes) if genes else "")

        # Protein change
        proteins = [
            inner.text
            for inner in element.findall("ClassifiedRecord/SimpleAllele/ProteinChange")
            if inner.text is not None
        ]
        row.append(", ".join(proteins) if proteins else "")

        # Condition(s)
        germline_classification = element.find("ClassifiedRecord/Classifications/GermlineClassification")
        conditions = [
            inner.text
            for inner in germline_classification.findall("ConditionList/TraitSet/Trait/Name/ElementValue[@Type='Preferred']")
            if inner.text is not None
        ]
        row.append("|".join(conditions) if conditions else "")

        # Accession
        accession = element.attrib.get("Accession")
        row.append(accession if accession is not None else "")

        # GRCh37Chromosome
        grch37_sequence_location = element.find("ClassifiedRecord/SimpleAllele/Location/SequenceLocation[@Assembly='GRCh37']")
        grch37_chromosome = grch37_sequence_location.attrib.get("Chr") if grch37_sequence_location is not None else None
        row.append(grch37_chromosome if grch37_chromosome is not None else "")

        # GRCh37Location
        grch37_start = grch37_sequence_location.attrib.get("display_start") if grch37_sequence_location is not None else None
        grch37_end = grch37_sequence_location.attrib.get("display_stop") if grch37_sequence_location is not None else None
        row.append(f"{grch37_start} - {grch37_end}" if grch37_start is not None and grch37_end is not None and grch37_start != grch37_end else grch37_start if grch37_start is not None else "")

        # GRCh38Chromosome
        grch38_sequence_location = element.find("ClassifiedRecord/SimpleAllele/Location/SequenceLocation[@Assembly='GRCh38']")
        grch38_chromosome = grch38_sequence_location.attrib.get("Chr") if grch38_sequence_location is not None else None
        row.append(grch38_chromosome if grch38_chromosome is not None else "")

        # GRCh38Location
        grch38_start = grch38_sequence_location.attrib.get("display_start") if grch38_sequence_location is not None else None
        grch38_end = grch38_sequence_location.attrib.get("display_stop") if grch38_sequence_location is not None else None
        row.append(f"{grch38_start} - {grch38_end}" if grch38_start is not None and grch38_end is not None and grch38_start != grch38_end else grch38_start if grch38_start is not None else "")

        # VariationID
        variation_id = element.attrib.get("VariationID")
        row.append(variation_id if variation_id is not None else "")

        # AlleleID(s)
        simple_allele = element.find("ClassifiedRecord/SimpleAllele")
        allele_id = simple_allele.attrib.get("AlleleID") if simple_allele is not None else None
        row.append(allele_id if allele_id is not None else "")

        # dbSNP ID
        xrefs = element.findall("ClassifiedRecord/SimpleAllele/XRefList/XRef")
        xref = next((inner for inner in xrefs if inner.attrib.get("DB") == "dbSNP"), None)
        row.append(f"{xref.attrib.get('Type')}{xref.attrib.get('ID')}" if xref is not None else "")

        # Canonical SPDI
        canonical_spdi = element.find("ClassifiedRecord/SimpleAllele/CanonicalSPDI")
        row.append(canonical_spdi.text if canonical_spdi is not None else "")

        # Variant type
        variant_type = element.find("ClassifiedRecord/SimpleAllele/VariantType")
        row.append(variant_type.text if variant_type is not None else "")

        # Molecular consequence
        molecular_consequences = [
            inner.attrib.get("Type")
            for inner in element.findall("ClassifiedRecord/SimpleAllele/HGVSlist/HGVS[@Type='coding']/MolecularConsequence")
            if inner.attrib.get("Type") is not None
        ]
        molecular_consequences = list(set(molecular_consequences))
        row.append("|".join(molecular_consequences) if molecular_consequences else "")

        # Germline classification
        description = germline_classification.find("Description") if germline_classification is not None else None
        row.append(description.text if description is not None else "")

        # Germline review status
        review_status = germline_classification.find("ReviewStatus") if germline_classification is not None else None
        row.append(review_status.text if review_status is not None else "")

        # Germline date last evaluated
        date_last_evaluated = germline_classification.attrib.get("DateLastEvaluated") if germline_classification is not None else None
        row.append(datetime.strptime(date_last_evaluated, "%Y-%m-%d").strftime("%b %d, %Y") if date_last_evaluated is not None else "")

        # Append row to rows
        rows.append(row)


def process_genomic_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates genomic variant data by unique genomic position (gen_pos), counting occurrences
    across different data sources, and retaining key annotation fields.

    Args:
        df: Input DataFrame containing raw variant records with columns for different position
            identifiers and annotation fields.
    Returns:
        final_df: DataFrame indexed by unique genomic position (gen_pos), with count columns for
            each source (LOVD_count, gnomAD_count, ClinVar_count) and the specified annotation columns.
    """
    position_cols = {
        "hg38_gnomad_format": "LOVD_count",
        "variant_id_gnomad": "gnomAD_count",
        "hg38_ID_clinvar": "ClinVar_count"
    }
    annotation_cols = [
        "VariantOnTranscript/DNA",
        "VariantOnTranscript/Protein",
        "malformed",
        "VariantOnGenome/ClinicalClassification",
        "Germline classification_clinvar",
        "Allele Frequency_gnomad",
        "Popmax_gnomad",
        "Popmax population_gnomad"
    ]
    melted = df.melt(
        id_vars=annotation_cols,
        value_vars=list(position_cols.keys()),
        var_name='source_col',
        value_name='gen_pos'
    )
    melted = melted.dropna(subset=['gen_pos'])
    counts = (
        melted
        .groupby(['gen_pos', 'source_col'])
        .size()
        .unstack(fill_value=0)
        .rename(columns=position_cols)
    )
    for count_col in position_cols.values():
        if count_col not in counts:
            counts[count_col] = 0
    annotations = (
        melted
        .sort_values('gen_pos')
        .groupby('gen_pos')[annotation_cols]
        .first()
    )
    final_df = (
        counts
        .join(annotations)
        .reset_index()
        .rename(columns={'gen_pos': 'gen_pos'})
    )
    cols = ['gen_pos'] + annotation_cols + list(position_cols.values())
    final_df = final_df[cols]
    return final_df
