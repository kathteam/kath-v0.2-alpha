""" Module provides interface to web APIs of CADD tool. """
import os
import re
import shutil
import time
import gzip
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class CaddError(Exception):
    """Custom exception for CADD-related errors."""
    def __init__(self, message: str):
        super().__init__(f"CADD Error: {message}")


def create_cadd_input_files(chunk: pd.DataFrame, cadd_folder_path: str, chunk_id: int):
    """
    Generates a VCF (Variant Call Format) file from a dataframe chunk for CADD processing.

    This function takes a portion of genomic data (`chunk`), writes it to a VCF file
    in the specified folder, and returns the file path along with the chunk ID.

    Args:
        chunk (pd.DataFrame): A dataframe containing genomic variant data.
        cadd_folder_path (str): Directory path where the VCF file should be saved.
        chunk_id (int): Identifier for the data chunk, used in naming the output file.

    Returns:
        tuple: A tuple containing:
            - chunk_id (int): The identifier of the processed chunk.
            - chunk_vcf_path (str): The full file path of the generated VCF file.
    """
    chunk_vcf_path = os.path.join(cadd_folder_path,f"chunk_{chunk_id}.vcf")
    write_vcf(dataframe=chunk, output_filepath=chunk_vcf_path)
    return chunk_id, chunk_vcf_path


def write_vcf(dataframe: pd.DataFrame, output_filepath: str) -> str:
    """
    Writes a VCF (Variant Call Format) file without header
    from the given DataFrame, ensuring no duplicate variants.

    This function extracts specific variant information
    from a pandas DataFrame and writes it to a VCF file.
    It ensures that duplicate variants (same chromosome, position, ref, and alt)
    are not written multiple times.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing the variant data.
        output_filepath (str): The path where the VCF file will be saved.

    Returns:
        str: The file path where the VCF file has been written.
    """
    seen_variants = set()
    with open(output_filepath, 'w', encoding='utf-8') as f:
        variant_columns = ["gen_pos"]
        for row in dataframe.itertuples(index=False):
            variant_value = next(
            (getattr(row,col) for col in variant_columns
            if hasattr(row,col) and pd.notna(getattr(row,col))
            and getattr(row,col) != "?"), None
            )
            if variant_value:
                parsed_variant = parse_variant(variant_value)
                if parsed_variant:
                    chrom, pos, ref, alt = parsed_variant
                    if (chrom, pos, ref, alt) not in seen_variants:
                        seen_variants.add((chrom, pos, ref, alt))
                        f.write(f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t.\t.\t.\n")
    return output_filepath


def gzip_file(file_path: str):
    """
    Compresses a file into a .gz format.

    This function takes a file at the given file path and compresses it
    into a .gz file by reading the original file and writing it to a
    gzipped version.

    Args:
        file_path (str): The path of the file to be compressed.

    Returns:
        str: The path to the newly gzipped file.
    """
    gzipped_file_path = f"{file_path}.gz"
    try:
        with open(file_path, 'rb') as f_in:
            with gzip.open(gzipped_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return gzipped_file_path
    except Exception as e:
        raise CaddError(f"Error during compression of file {file_path}: {str(e)}") from e


def send_cadd_input_files(gzipped_chunk_path:str,chunk_id:int):
    """
    Uploads a gzipped genomic data chunk to the CADD web service and retrieves the job URL.

    This function automates the process of submitting a gzipped genomic variant file
    to the CADD (Combined Annotation Dependent Depletion) web service using a Firefox
    web driver. After submission, it waits for the job to complete and returns the URL
    for checking the job status.

    Args:
        gzipped_chunk_path (str): The file path of the gzipped input data chunk to be uploaded.
        chunk_id (int): The identifier for the data chunk, used to track the submission.

    Returns:
        tuple: A tuple containing:
            - chunk_id (int): The identifier of the processed chunk.
            - job_url (str): The URL to check the status of the CADD job.

    Raises:
        TimeoutException: If the status or availability link is not found within the given time.
    """
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.set_preference("browser.download.manager.showWhenStarting", False)
    driver = webdriver.Firefox(options=options)
    driver.get("https://cadd.bihealth.org/score")

    file_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "file"))
    )
    file_input.send_keys(os.path.abspath(gzipped_chunk_path))

    submit_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
    submit_button.click()

    WebDriverWait(driver, 5).until(EC.url_contains("/upload"))
    try:
        finished_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/static/finished/")]'))
        )
        job_file = extract_job_file(finished_link.get_attribute("href"))
    except TimeoutException:
        try:
            check_avail_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/check_avail/")]'))
            )
            job_file = extract_job_file(check_avail_link.get_attribute("href"))
        except TimeoutException as exc:
            raise CaddError(
            f"Could not find the job status link (/check_avail/).Error:{str(exc)}") from exc
    driver.quit()

    return chunk_id, f"https://cadd.bihealth.org/check_avail/{job_file}"


def extract_job_file(url:str):
    """
    Extracts the filename from a given URL.

    This function retrieves the last segment of a URL (typically a filename).
    It assumes the filename appears at the end of the URL, following the last '/'.

    Args:
        url (str): The URL string from which the filename will be extracted.

    Returns:
        str: The extracted filename.

    Raises:
       CaddError: If no valid filename is found in the URL.

    Example:
        >>> extract_job_id("
        https://cadd.bihealth.org/check_avail/
        GRCh38-v1.7_fdf994281314d8d098d2cd17ade6458a.tsv.gz")
        'GRCh38-v1.7_fdf994281314d8d098d2cd17ade6458a.tsv.gz'
    """
    match = re.search(r'/([^/]+)$', url)
    if match:
        return match.group(1)
    raise CaddError("CADD server: Invalid URL format - filename not found.")


def get_cadd_output_files(cadd_job_url: str, cadd_output_dir: str, chunk_id: int,max_retries=15):
    """Downloads CADD output file while preventing infinite loops.

    Args:
        cadd_job_url (str): The URL of the CADD job.
        cadd_output_dir (str): The directory to save the output file.
        chunk_id (int): The chunk identifier.
        max_retries (int): Maximum number of retries before giving up.
        retry_interval (int): Time (in seconds) between retries.

    Returns:
        tuple: (chunk_id, job_id) if successful, else raises TimeoutException.
    """
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", cadd_output_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/gzip")

    driver = webdriver.Firefox(options=options)
    retry_count = 0

    driver.get(cadd_job_url)
    try:
        finished_link = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
            (By.XPATH, '//a[contains(@href, "/static/finished/")]')))
        job_file = extract_job_file(finished_link.get_attribute("href"))
        finished_link.click()
    except TimeoutException:
        for retry_count in range(max_retries):
            driver.refresh()
            try:
                finished_link = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//a[contains(@href, "/static/finished/")]'))
                )
                job_file = extract_job_file(finished_link.get_attribute("href"))
                finished_link.click()
                break
            except TimeoutException as e:
                if retry_count == max_retries - 1:
                    error_message = (
                        f"Max retries reached: Unable to fetch CADD output from {cadd_job_url} "
                        f"after {max_retries} attempts."
                    )
                    raise CaddError(error_message) from e
                time.sleep(120)
    driver.quit()
    return chunk_id, job_file


def gunzip_file(file_path: str, chunk_id: int):
    """
    Uncompresses a .gz file to its uncompressed version.

    This function takes a gzipped file at the given file path and uncompresses it
    by reading the .gz file and extracting it to an uncompressed version.

    Args:
        file_path (str): The path of the gzipped file to be uncompressed.
        chunk_id (int): The chunk identifier associated with the file.

    Returns:
        tuple: A tuple containing the chunk_id and the path to the uncompressed file.

    Raises:
        CaddError: If an error occurs during the decompression process.
    """
    uncompressed_file_path = file_path[:-3]
    try:
        with gzip.open(file_path, 'rb') as f_in:
            with open(uncompressed_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return chunk_id, uncompressed_file_path
    except Exception as e:
        raise CaddError(f"Error during decompression of file {file_path}: {str(e)}") from e


def parse_variant(variant_str:str):
    """
    Parses a variant string and extracts chromosome, position, reference, and alternative alleles.

    The function takes a variant string in the format of `chrom-pos-ref-alt` (e.g., `1-123-A-G`),
    and splits it into the individual components.
    If the string contains only chromosome and position
    (e.g., `1-123`), it will assume reference and
    alternative alleles as missing (represented by `"."`).

    Args:
        variant_str (str): The variant string to be parsed,
        typically in the format `chrom-pos-ref-alt`.

    Returns:
        tuple: A tuple containing:
            - chrom (str): The chromosome part of the variant string.
            - pos (str): The position part of the variant string.
            - ref (str): The reference allele (or `"."` if not provided).
            - alt (str): The alternative allele (or `"."` if not provided).

    Example:
        parse_variant("1-123-A-G")  -> ('1', '123', 'A', 'G')
    """
    try:
        if not isinstance(variant_str, str):
            return None
        chrom, pos, ref, alt = variant_str.split("-")
        if not chrom or not pos or not ref or not alt:
            return None
        return chrom, pos, ref, alt
    except (ValueError, AttributeError):
        return None


def parse_tsv(file_path:str)->pd.DataFrame:
    """
    Parses a TSV file and returns a DataFrame with two columns: 'cadd_gen_position' and 'PHRED'.

    The function reads the TSV file, skipping comment lines, and generates a new column,
    'cadd_gen_position', by concatenating 'Chrom', 'Pos', 'Ref', and 'Alt'. It also extracts
    the 'PHRED' scores.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        pd.DataFrame: DataFrame with 'cadd_gen_position' and 'PHRED' columns.

    Example:
        result = parse_tsv('file_path.tsv')
    """
    df = pd.read_csv(file_path, sep='\t', comment='#',
                    names=['Chrom', 'Pos', 'Ref', 'Alt', 'RawScore', 'PHRED'])
    df['cadd_gen_position'] = (
    df['Chrom'].astype(str) + '-' +
    df['Pos'].astype(str) + '-' +
    df['Ref'] + '-' +
    df['Alt'])
    return df[['cadd_gen_position', 'PHRED']]


def merge_with_tsv(data_chunk:pd.DataFrame, tsv_chunk):
    """
    Merges the given data_chunk with the tsv_chunk DataFrame based on matching values
    between the 'cadd_gen_position' column in tsv_chunk and the corresponding columns
    ('hg38_gnomad_format', 'variant_id_gnomad', 'hg38_ID_clinvar') in data_chunk.

    The function uses the first non-empty value from these
    columns to construct the 'cadd_gen_position' key.
    If a matching CADD score is not found in tsv_chunk,
    the PHRED value will be set to "Cadd score unavailable".

    Args:
        data_chunk (pd.DataFrame): The DataFrame containing genomic data to be merged.
        tsv_chunk (pd.DataFrame): The DataFrame containing CADD genomic positions.

    Returns:
        pd.DataFrame: The merged DataFrame based on the matching positions.
    """

    merged_df = pd.merge(
        data_chunk,
        tsv_chunk[['cadd_gen_position', 'PHRED']],
        left_on='gen_pos',
        right_on='cadd_gen_position',
        how='left'
    )

    return merged_df.drop(columns=['cadd_gen_position'])


def cadd_pipeline(dataframe: pd.DataFrame, cadd_folder_path: str) -> pd.DataFrame:
    """
    Process genomic data through multiple stages of file creation, uploading,
    fetching results, parsing, and merging with CADD data.

    Args:
        dataframe (pd.DataFrame): The input genomic data.
        cadd_folder_path (str): Path to store temporary input/output files for CADD processing.

    Returns:
        pd.DataFrame: The final merged dataframe with CADD scores.
    """
    num_chunks = max(2, len(dataframe) // 1000)
    data_chunks = np.array_split(dataframe, num_chunks)
    vcf_gziped_chunks={}
    cadd_job_chunks={}
    tsv_chunks={}
    merged_chunks={}

    cadd_folder_path = os.path.join(cadd_folder_path,
                                    datetime.now().strftime("%Y%m%d_%H%M%S"))
    cadd_folder_input = os.path.join(cadd_folder_path,"input")
    cadd_folder_output = os.path.join(cadd_folder_path,"output")
    if not os.path.exists(cadd_folder_input):
        os.makedirs(cadd_folder_input)
    if not os.path.exists(cadd_folder_output):
        os.makedirs(cadd_folder_output)

    with ProcessPoolExecutor() as executor:
        jobs = {executor.submit(
            create_cadd_input_files,
            data_chunks[i],
            cadd_folder_input,
            i): i for i in range(num_chunks)}
        for job in jobs:
            chunk_id, vcf_chunk_path = job.result()
            vcf_gziped_chunks[chunk_id] = gzip_file(vcf_chunk_path)
            os.remove(os.path.join(cadd_folder_input,vcf_chunk_path))

    for i in range(num_chunks):
        chunk_id, cadd_job_url = send_cadd_input_files(
            vcf_gziped_chunks[i],
            i)
        os.remove(os.path.join(cadd_folder_input,vcf_gziped_chunks[chunk_id]))
        cadd_job_chunks[chunk_id] = cadd_job_url

    for i in range(num_chunks):
        chunk_id, cadd_gzip_file_path = get_cadd_output_files(
            cadd_job_chunks[i],
            cadd_folder_output,
            i)
        renamed_path = os.path.join(cadd_folder_output,f"cadd_chunk_{chunk_id}.tsv.gz")
        os.rename(os.path.join(cadd_folder_output,cadd_gzip_file_path),
                  renamed_path)
        tsv_chunks[chunk_id] = renamed_path

    with ProcessPoolExecutor() as executor:
        jobs = {executor.submit(
            gunzip_file,
            os.path.join(cadd_folder_output,
            tsv_chunks[i]),
            i): i for i in range(num_chunks)}
        for job in jobs:
            chunk_id, cadd_tsv_file_path = job.result()
            merged_chunks[chunk_id] = merge_with_tsv(
                data_chunks[chunk_id],
                parse_tsv(cadd_tsv_file_path))
            os.remove(os.path.join(cadd_folder_output,cadd_tsv_file_path))
    return pd.concat(merged_chunks.values(), ignore_index=True)
