""" Module provides interface to web APIs of CADD tool. """
import os
import time
import gzip
import shutil
import re
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def gunzip_file(file_path:str):
    """
    Uncompresses a file from .gz format.

    This function takes a file at the given file path and uncompresses it 
    from a .gz file by reading the gzipped file and extracting it to a 
    uncompressed version.

    Args:
        file_path (str): The path of the file to be uncompressed.

    Returns:
        str: The path to the newly gunzipped file.
    """
    with gzip.open(file_path, 'rb') as f_in:
        with open(file_path[:-3], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


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

    with open(file_path, 'rb') as f_in:
        with gzip.open(gzipped_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return gzipped_file_path


def parse_variant(variant_str):
    """
    Parses a variant string and extracts chromosome, position, reference, and alternative alleles.

    The function takes a variant string in the format of `chrom-pos-ref-alt` (e.g., `1-123-A-G`), 
    and splits it into the individual components. If the string contains only chromosome and position 
    (e.g., `1-123`), it will assume reference and alternative alleles as missing (represented by `"."`).

    Args:
        variant_str (str): The variant string to be parsed, typically in the format `chrom-pos-ref-alt`.

    Returns:
        tuple: A tuple containing:
            - chrom (str): The chromosome part of the variant string.
            - pos (str): The position part of the variant string.
            - ref (str): The reference allele (or `"."` if not provided).
            - alt (str): The alternative allele (or `"."` if not provided).

    Example:
        parse_variant("1-123-A-G")  -> ('1', '123', 'A', 'G')
        parse_variant("1-123")      -> ('1', '123', '.', '.')
    """
    try:
        chrom, pos, ref, alt = variant_str.split("-")
        return chrom, pos, ref, alt
    except ValueError:
        chrom, pos, _ = variant_str.split("-")
        return chrom, pos, ".", "."
    except AttributeError:
        return ".", ".", ".", "."
    

def extract_job_id(url:str):
    """
    Extracts the job ID from a given URL.

    This function searches for a 32-character hexadecimal string (typically used as a job ID)
    in the provided URL. 
    The job ID is expected to be in the format `_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
    where `x` is a hexadecimal character (a-f, 0-9).

    Args:
        url (str): The URL string from which the job ID will be extracted.

    Returns:
        str or None: The extracted job ID as a string (without the leading underscore), 
        or None if no valid job ID is found.

    """
    match = re.search(r'_([a-f0-9]{32})', url)
    if match:
        return match.group(0)
    return None


def get_cadd_scores_file(file_path:str):
    """
    Processes a given VCF file to retrieve CADD scores.

    This function renames the input file with a timestamp, sets up a 
    headless Firefox WebDriver with appropriate download preferences, 
    and downloads CADD scores from an online source. The downloaded 
    file is then extracted and cleaned up.

    Args:
        file_path (str): The path to the input VCF file.

    Returns:
        str: The path to the processed CADD scores TSV file.

    Steps:
        1. Rename the input file to include a timestamp.
        2. Configure a headless Firefox WebDriver for automated download.
        3. Download CADD scores using the provided VCF file.
        4. Extract the downloaded GZ file and remove the compressed version.
        5. Return the path to the extracted CADD scores TSV file.
    """
   
    download_dir = os.path.dirname(file_path)

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/gzip")

    driver = webdriver.Firefox(options=options)

    job_id = download_cadd_scores(driver=driver,vcf_file_path=file_path)

    downloaded_file = os.path.join(download_dir, f"GRCh38-v1.7{job_id}.tsv.gz")
    gunzip_file(downloaded_file)
    os.remove(downloaded_file)

    return os.path.join(download_dir, f"GRCh38-v1.7{job_id}.tsv")


def download_cadd_scores(driver:webdriver.Firefox,vcf_file_path:str):
    """
    Downloads CADD (Combined Annotation-Dependent Depletion) scores for a given VCF file.

    This function automates the process of uploading a VCF file to the CADD web service, 
    checking the job status, and downloading the resulting CADD scores file. It uses Selenium 
    WebDriver to interact with the CADD website, waits for the job to finish, and retrieves 
    the resulting file.

    Args:
        driver (webdriver.Firefox): The WebDriver instance to interact with the browser.
        vcf_file_path (str): The local path to the VCF file to be uploaded to the CADD service.

    Returns:
        str: job_id of processed file from CADD web-server.
    
    Raises:
        TimeoutException: If the job status link or finished file link cannot be found within the 
                          expected time frame.
    """
    try:
        driver.get("https://cadd.bihealth.org/score")

        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "file"))
        )
        file_input.send_keys(os.path.abspath(vcf_file_path))

        submit_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
        submit_button.click()

        WebDriverWait(driver, 20).until(EC.url_contains("/upload"))

        try:
            finished_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/static/finished/")]'))
            )
            job_id = extract_job_id(finished_link.get_attribute("href"))
            finished_link.click()
            time.sleep(5)
        except:
            try:
                check_avail_link = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/check_avail/")]'))
                )
                job_url = check_avail_link.get_attribute("href")
                job_id = extract_job_id(job_url)
            except TimeoutException:
                raise TimeoutException("CADD:Could not find the job status link (/check_avail/).")

            driver.get(job_url)

            while True:
                driver.refresh()
                try:
                    finished_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/static/finished/")]'))
                    )
                    job_id = extract_job_id(finished_link.get_attribute("href"))
                    finished_link.click()
                    time.sleep(5)
                    break
                except:
                    time.sleep(60)
    finally:
        driver.quit()
        return job_id


def write_vcf(dataframe:pd.DataFrame, output_filepath:str) -> str:
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
    with open(output_filepath, 'w') as f:
        variant_columns = ["hg38_gnomad_format", "variant_id_gnomad","variant_id", "hg38_ID_clinvar"]
        for _, row in dataframe.iterrows():
            variant_value = None
            for col in variant_columns:
                if col in row and pd.notna(row[col]) and row[col]!="?":
                    variant_value = row[col]
                    break
            chrom, pos, ref, alt = parse_variant(variant_value)
            vcf_line = f"{chrom}\t{pos}\t.\t{ref}\t{alt}\n"
            f.write(vcf_line) 
    return output_filepath  


def parse_tsv(tsv_file_path: str, vcf_file_path: str):
    """
    Parses a TSV (Tab-Separated Values) file to extract PHRED scores.

    This function reads a TSV file, skips comment lines (lines starting with `#`),
    and extracts PHRED scores from the sixth column (index 5) based on variant
    positions and alleles found in the VCF file. If a corresponding value is not
    found, "CADD score unavailable" is stored.

    Args:
        tsv_file_path (str): The path to the TSV file.
        vcf_file_path (str): The path to the VCF file.

    Returns:
        dict: A dictionary mapping VCF variants (chrom, pos, ref, alt) to PHRED scores,
              or "CADD score unavailable" if no match is found.

    Raises:
        ValueError: If an error occurs while reading or parsing the file.
    """
    try:
        tsv_data = {}
        with open(tsv_file_path, 'r', encoding='utf-8') as tsv:
            for line in tsv:
                if line.startswith('#'):
                    continue
                columns = line.strip().split('\t')
                key = f"{columns[0]}:{columns[1]}:{columns[2]}:{columns[3]}"
                tsv_data[key] = columns[5]

        phred_scores = []
        with open(vcf_file_path, 'r', encoding='utf-8') as vcf:
            for line in vcf:
                columns = line.strip().split('\t')
                if len(columns) < 5:
                    phred_scores.append("CADD score unavailable")
                    continue
                key = f"{columns[0]}:{columns[1]}:{columns[3]}:{columns[4]}"
                phred_scores.append(tsv_data.get(key, "CADD score unavailable"))
        
        return phred_scores
    
    except Exception as e:
        raise ValueError(f"CADD: Error parsing files {tsv_file_path} or {vcf_file_path}: {e}") from e


def cadd_pipeline(dataframe:pd.DataFrame,vcf_file_path:str)->pd.DataFrame:
    """
    Executes the CADD (Combined Annotation Dependent Depletion) scoring pipeline.

    This function processes a given dataframe by:
    1. Writing it to a VCF file.
    2. Compressing the VCF file.
    3. Submitting it to the CADD server to retrieve PHRED-like scores.
    4. Parsing the downloaded scores and appending them to the original dataframe.

    Args:
        dataframe (pd.DataFrame): The input dataframe containing variant data.
        vcf_file_path (str): The file path where the VCF file will be stored.

    Returns:
        pd.DataFrame: The original dataframe with an additional column "PHRED_cadd"
                      containing the CADD scores.

    Steps:
        1. Create a copy of the input dataframe.
        2. Write the dataframe to a VCF file.
        3. Compress the VCF file using gzip.
        4. Retrieve CADD scores for the compressed VCF file.
        5. Parse the downloaded scores and append them to the dataframe.
        6. Remove the temporary CADD TSV file.
        7. Return the dataframe with the appended CADD scores.
    """
    data_copy=dataframe.copy()
    input_vcf_file=write_vcf(dataframe=data_copy,output_filepath=vcf_file_path)
    gzipped_file_path = gzip_file(input_vcf_file)
    cadd_tsv_file=get_cadd_scores_file(gzipped_file_path)
    os.remove(gzipped_file_path)
    scores = parse_tsv(tsv_file_path=cadd_tsv_file,vcf_file_path=input_vcf_file)
    scores_df = pd.DataFrame(scores)
    scores_df.columns = ["PHRED_cadd"]
    data_copy = pd.concat([data_copy,scores_df], axis=1)
    return data_copy
