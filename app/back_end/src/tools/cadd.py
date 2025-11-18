"""Module provides interface to web APIs of CADD tool."""

import gzip
import logging
import os
import platform
import re
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


@dataclass
class BrowserInfo:
    """Information about detected browser."""

    name: str
    binary_path: Optional[str]
    driver_type: str  # "firefox", "chrome", "edge", "brave", "safari"
    driver_service: Optional[object]  # Service object for the driver


def _find_binary_in_paths(binary_names: list[str], common_paths: dict[str, list[str]]) -> Optional[str]:
    """
    Find a binary in common installation paths.

    Args:
        binary_names: List of possible binary names
        common_paths: Dict mapping binary name to list of common paths

    Returns:
        Path to the binary if found, None otherwise
    """
    for binary_name in binary_names:
        # Check common paths for this binary
        if binary_name in common_paths:
            for path in common_paths[binary_name]:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path

        # Try using 'which' command
        try:
            result = subprocess.run(["which", binary_name], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                binary_path = result.stdout.strip()
                if os.path.isfile(binary_path) and os.access(binary_path, os.X_OK):
                    return binary_path
        except Exception:
            pass

    return None


def find_firefox_binary() -> Optional[str]:
    """
    Locate Firefox binary on the system.

    Checks common Firefox installation paths in order:
    1. /usr/bin/firefox (Linux standard)
    2. /usr/local/bin/firefox (Custom installations)
    3. /snap/bin/firefox (Snap installations)
    4. Uses 'which firefox' to search PATH
    5. Falls back to None if not found

    Returns:
        Path to Firefox binary or None to use Selenium default
    """
    common_paths = {"firefox": ["/usr/bin/firefox", "/usr/local/bin/firefox", "/snap/bin/firefox"]}

    if platform.system() == "Darwin":  # macOS
        common_paths["firefox"].extend(
            [
                "/Applications/Firefox.app/Contents/MacOS/firefox",
            ]
        )

    binary_path = _find_binary_in_paths(["firefox"], common_paths)
    if binary_path:
        return binary_path

    logger.warning(
        "Firefox binary not found. Selenium will attempt to use system default. "
        "If this fails, please install Firefox"
    )
    return None


def find_chrome_binary() -> Optional[str]:
    """
    Locate Chrome/Chromium binary on the system.

    Checks for Google Chrome, Chromium, and related variants.

    Returns:
        Path to Chrome binary or None if not found
    """
    common_paths = {
        "google-chrome": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/snap/bin/chromium",
        ],
        "chromium": ["/usr/bin/chromium", "/usr/bin/chromium-browser"],
        "chromium-browser": ["/usr/bin/chromium-browser"],
    }

    if platform.system() == "Darwin":  # macOS
        common_paths["google-chrome"].extend(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
        )
        common_paths["chromium"].extend(
            [
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        )

    binary_names = ["google-chrome", "chromium", "chromium-browser"]
    binary_path = _find_binary_in_paths(binary_names, common_paths)

    if binary_path:
        return binary_path

    logger.debug("Chrome/Chromium binary not found")
    return None


def find_edge_binary() -> Optional[str]:
    """
    Locate Microsoft Edge binary on the system.

    Returns:
        Path to Edge binary or None if not found
    """
    common_paths = {
        "microsoft-edge": [
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable",
        ],
    }

    if platform.system() == "Darwin":  # macOS
        common_paths["microsoft-edge"].extend(
            [
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            ]
        )
    elif platform.system() == "Windows":
        common_paths["msedge"] = [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]

    binary_names = ["microsoft-edge", "msedge"]
    binary_path = _find_binary_in_paths(binary_names, common_paths)

    if binary_path:
        return binary_path

    logger.debug("Microsoft Edge binary not found")
    return None


def find_brave_binary() -> Optional[str]:
    """
    Locate Brave browser binary on the system.

    Returns:
        Path to Brave binary or None if not found
    """
    common_paths = {
        "brave": ["/usr/bin/brave", "/usr/bin/brave-browser"],
        "brave-browser": ["/usr/bin/brave-browser"],
    }

    if platform.system() == "Darwin":  # macOS
        common_paths["brave"].extend(
            [
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            ]
        )
    elif platform.system() == "Windows":
        common_paths["brave"] = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ]

    binary_names = ["brave", "brave-browser"]
    binary_path = _find_binary_in_paths(binary_names, common_paths)

    if binary_path:
        return binary_path

    logger.debug("Brave browser binary not found")
    return None


def find_safari_binary() -> Optional[str]:
    """
    Locate Safari browser on macOS.

    Safari is typically available on macOS as the default browser.

    Returns:
        "safari" if available on macOS, None otherwise
    """
    if platform.system() != "Darwin":
        return None

    # Check if Safari exists on macOS
    safari_path = "/Applications/Safari.app/Contents/MacOS/Safari"
    if os.path.isfile(safari_path) and os.access(safari_path, os.X_OK):
        return safari_path

    logger.debug("Safari not found or not running on macOS")
    return None


def detect_available_browsers() -> list[Tuple[str, str]]:
    """
    Detect all available browsers on the system.

    Returns:
        List of tuples (browser_name, binary_path) for available browsers
    """
    available_browsers: list[Tuple[str, str]] = []

    # Check browsers in order of preference
    browsers_to_check = [
        ("Firefox", find_firefox_binary),
        ("Chrome", find_chrome_binary),
        ("Edge", find_edge_binary),
        ("Brave", find_brave_binary),
        ("Safari", find_safari_binary),
    ]

    for browser_name, detector_func in browsers_to_check:
        binary_path = detector_func()
        if binary_path:
            available_browsers.append((browser_name, binary_path))
            logger.debug(f"Found {browser_name} at {binary_path}")

    if not available_browsers:
        logger.warning("No compatible browsers found. Selenium will attempt to use system defaults")

    return available_browsers


def get_webdriver(browser: Optional[str] = None) -> webdriver.Remote:  # noqa: C901
    """
    Get a Selenium WebDriver for the specified browser.

    Automatically detects and uses the first available browser if not specified.

    Args:
        browser: Browser to use ("firefox", "chrome", "edge", "brave", "safari")
                If None, uses first detected browser

    Returns:
        Configured WebDriver instance

    Raises:
        CaddError: If no compatible browser is found
    """
    available = detect_available_browsers()

    if not available:
        raise CaddError("No compatible browser found. Please install Firefox, Chrome, Edge, or Brave")

    # Use specified browser if available, otherwise use first detected
    if browser:
        browser_lower = browser.lower()
        selected_browser = None
        selected_path = None

        for name, path in available:
            if name.lower() == browser_lower:
                selected_browser = name
                selected_path = path
                break

        if not selected_browser:
            available_names = ", ".join([name for name, _ in available])
            raise CaddError(f"Browser '{browser}' not found. Available: {available_names}")
    else:
        selected_browser, selected_path = available[0]

    logger.info(f"Using {selected_browser} browser for web automation")

    # Create appropriate WebDriver based on browser type
    if selected_browser.lower() == "firefox":
        from selenium.webdriver.firefox.options import Options as FirefoxOptions

        options = FirefoxOptions()
        if selected_path:
            options.binary_location = selected_path
        options.add_argument("--headless")
        options.set_preference("browser.download.manager.showWhenStarting", False)
        # Try to use geckodriver from standard Docker/system location
        geckodriver_path = None
        for path in ["/usr/local/bin/geckodriver", "/usr/bin/geckodriver"]:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                geckodriver_path = path
                break
        # Try to use Firefox from Docker installation location
        firefox_binary = None
        for path in ["/opt/firefox/firefox", "/usr/bin/firefox", "/usr/local/bin/firefox"]:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                firefox_binary = path
                break
        options.binary_location = firefox_binary if firefox_binary else None
        service = FirefoxService(executable_path=geckodriver_path) if geckodriver_path else FirefoxService()
        return webdriver.Firefox(service=service, options=options)

    elif selected_browser.lower() in ["chrome", "brave", "edge"]:
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        if selected_path:
            options.binary_location = selected_path
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = ChromeService()
        return webdriver.Chrome(service=service, options=options)

    elif selected_browser.lower() == "safari":
        from selenium.webdriver.safari.service import Service as SafariService

        service = SafariService()
        # Safari doesn't support as many options, but set headless if available
        try:
            from selenium.webdriver.safari.options import Options as SafariOptions

            options = SafariOptions()
            return webdriver.Safari(service=service, options=options)
        except ImportError:
            return webdriver.Safari(service=service)

    else:
        raise CaddError(f"Unsupported browser: {selected_browser}")


class CaddError(Exception):
    """Custom exception for CADD-related errors."""

    def __init__(self, message: str) -> None:
        """Initialize CADD error with message."""
        super().__init__(f"CADD Error: {message}")


def create_cadd_input_files(chunk: pd.DataFrame, cadd_folder_path: str, chunk_id: int):
    """
    Generate a VCF (Variant Call Format) file from a dataframe chunk for CADD processing.

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
    chunk_vcf_path = os.path.join(cadd_folder_path, f"chunk_{chunk_id}.vcf")
    write_vcf(dataframe=chunk, output_filepath=chunk_vcf_path)
    return chunk_id, chunk_vcf_path


def write_vcf(dataframe: pd.DataFrame, output_filepath: str) -> str:
    """
    Write a VCF (Variant Call Format) file without header from DataFrame.

    Extracts specific variant information from a pandas DataFrame and writes
    it to a VCF file. Ensures that duplicate variants (same chromosome,
    position, ref, and alt) are not written multiple times.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing the variant data.
        output_filepath (str): The path where the VCF file will be saved.

    Returns:
        str: The file path where the VCF file has been written.
    """
    seen_variants = set()
    with open(output_filepath, "w", encoding="utf-8") as f:
        variant_columns = ["gen_pos"]
        for row in dataframe.itertuples(index=False):
            variant_value = next(
                (
                    getattr(row, col)
                    for col in variant_columns
                    if hasattr(row, col) and pd.notna(getattr(row, col)) and getattr(row, col) != "?"
                ),
                None,
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
    Compress a file into a .gz format.

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
        with open(file_path, "rb") as f_in:
            with gzip.open(gzipped_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return gzipped_file_path
    except Exception as e:
        raise CaddError(f"Error during compression of file {file_path}: {str(e)}") from e


def send_cadd_input_files(gzipped_chunk_path: str, chunk_id: int, browser: Optional[str] = None):
    """
    Upload a gzipped genomic data chunk to the CADD web service and retrieve the job URL.

    This function automates the process of submitting a gzipped genomic variant file
    to the CADD (Combined Annotation Dependent Depletion) web service using a web driver.
    After submission, it waits for the job to complete and returns the URL for checking
    the job status.

    Args:
        gzipped_chunk_path (str): The file path of the gzipped input data chunk to be uploaded.
        chunk_id (int): The identifier for the data chunk, used to track the submission.
        browser (str, optional): Browser to use ("firefox", "chrome", "edge", "brave", "safari")
                                If None, uses first detected browser.

    Returns:
        tuple: A tuple containing:
            - chunk_id (int): The identifier of the processed chunk.
            - job_url (str): The URL to check the status of the CADD job.

    Raises:
        TimeoutException: If the status or availability link is not found within the given time.
    """
    driver = get_webdriver(browser)
    driver.get("https://cadd.bihealth.org/score")

    file_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "file")))
    file_input.send_keys(os.path.abspath(gzipped_chunk_path))

    submit_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
    submit_button.click()

    WebDriverWait(driver, 5).until(EC.url_contains("/upload"))
    job_file = None
    try:
        finished_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/static/finished/")]'))
        )
        href = finished_link.get_attribute("href")
        if href:
            job_file = extract_job_file(href)
    except TimeoutException:
        try:
            check_avail_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/check_avail/")]'))
            )
            href = check_avail_link.get_attribute("href")
            if href:
                job_file = extract_job_file(href)
        except TimeoutException as exc:
            raise CaddError(f"Could not find the job status link (/check_avail/).Error:{str(exc)}") from exc

    if not job_file:
        raise CaddError("Could not extract job file from CADD response")

    driver.quit()

    return chunk_id, f"https://cadd.bihealth.org/check_avail/{job_file}"


def extract_job_file(url: str):
    """
    Extract the filename from a given URL.

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
    match = re.search(r"/([^/]+)$", url)
    if match:
        return match.group(1)
    raise CaddError("CADD server: Invalid URL format - filename not found.")


def get_cadd_output_files(  # noqa: C901
    cadd_job_url: str,
    cadd_output_dir: str,
    chunk_id: int,
    browser: Optional[str] = None,
    max_retries=15,
):
    """Download CADD output file while preventing infinite loops.

    Supports automatic download for multiple browsers with appropriate
    configuration for each browser type.

    Args:
        cadd_job_url (str): The URL of the CADD job.
        cadd_output_dir (str): The directory to save the output file.
        chunk_id (int): The chunk identifier.
        browser (str, optional): Browser to use ("firefox", "chrome", "edge", "brave", "safari")
                                If None, uses first detected browser.
        max_retries (int): Maximum number of retries before giving up.

    Returns:
        tuple: (chunk_id, job_id) if successful, else raises TimeoutException.
    """
    # Get the appropriate browser with auto-detection support
    available = detect_available_browsers()

    if not available:
        raise CaddError("No compatible browser found. Please install Firefox, Chrome, Edge, or Brave")

    # Use specified browser if available, otherwise use first detected
    if browser:
        browser_lower = browser.lower()
        selected_browser = None
        selected_path = None

        for name, path in available:
            if name.lower() == browser_lower:
                selected_browser = name
                selected_path = path
                break

        if not selected_browser:
            available_names = ", ".join([name for name, _ in available])
            raise CaddError(f"Browser '{browser}' not found. Available: {available_names}")
    else:
        selected_browser, selected_path = available[0]

    logger.info(f"Using {selected_browser} browser for CADD output download")

    # Create driver with browser-specific download configuration
    driver: webdriver.Remote
    if selected_browser.lower() == "firefox":
        from selenium.webdriver.firefox.options import Options as FirefoxOptions

        options = FirefoxOptions()
        if selected_path:
            options.binary_location = selected_path
        options.add_argument("--headless")
        # Configure Firefox for automatic downloads
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", cadd_output_dir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/gzip")
        # Try to use geckodriver from standard Docker/system location
        geckodriver_path = None
        for path in ["/usr/local/bin/geckodriver", "/usr/bin/geckodriver"]:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                geckodriver_path = path
                break
        # Try to use Firefox from Docker installation location
        firefox_binary = None
        for path in ["/opt/firefox/firefox", "/usr/bin/firefox", "/usr/local/bin/firefox"]:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                firefox_binary = path
                break
        options.binary_location = firefox_binary if firefox_binary else None
        service = FirefoxService(executable_path=geckodriver_path) if geckodriver_path else FirefoxService()
        driver = webdriver.Firefox(service=service, options=options)

    elif selected_browser.lower() in ["chrome", "brave", "edge"]:
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        if selected_path:
            options.binary_location = selected_path
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Configure Chrome-based browsers for automatic downloads
        prefs = {
            "download.default_directory": cadd_output_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
        }
        options.add_experimental_option("prefs", prefs)
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)

    elif selected_browser.lower() == "safari":
        from selenium.webdriver.safari.service import Service as SafariService

        service = SafariService()
        driver = webdriver.Safari(service=service)

    else:
        raise CaddError(f"Unsupported browser for download: {selected_browser}")
    retry_count = 0

    driver.get(cadd_job_url)
    job_file = None
    try:
        finished_link = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/static/finished/")]'))
        )
        href = finished_link.get_attribute("href")
        if href:
            job_file = extract_job_file(href)
        finished_link.click()
    except TimeoutException:
        for retry_count in range(max_retries):
            driver.refresh()
            try:
                finished_link = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/static/finished/")]'))
                )
                href = finished_link.get_attribute("href")
                if href:
                    job_file = extract_job_file(href)
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

    if not job_file:
        raise CaddError("Could not extract job file from CADD response")

    driver.quit()
    return chunk_id, job_file


def gunzip_file(file_path: str, chunk_id: int):
    """
    Decompress a .gz file to its uncompressed version.

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
        with gzip.open(file_path, "rb") as f_in:
            with open(uncompressed_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return chunk_id, uncompressed_file_path
    except Exception as e:
        raise CaddError(f"Error during decompression of file {file_path}: {str(e)}") from e


def parse_variant(variant_str: str):
    """
    Parse a variant string and extracts chromosome, position, reference, and alternative alleles.

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


def parse_tsv(file_path: str) -> pd.DataFrame:
    """
    Parse a TSV file and return a DataFrame with CADD columns.

    Reads the TSV file, skipping comment lines, and generates a new column
    'cadd_gen_position' by concatenating 'Chrom', 'Pos', 'Ref', and 'Alt'.
    Also extracts the 'PHRED' scores.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        pd.DataFrame: DataFrame with 'cadd_gen_position' and 'PHRED' columns.

    Example:
        result = parse_tsv('file_path.tsv')
    """
    df = pd.read_csv(file_path, sep="\t", comment="#", names=["Chrom", "Pos", "Ref", "Alt", "RawScore", "PHRED"])
    df["cadd_gen_position"] = df["Chrom"].astype(str) + "-" + df["Pos"].astype(str) + "-" + df["Ref"] + "-" + df["Alt"]
    return df[["cadd_gen_position", "PHRED"]]


def merge_with_tsv(data_chunk: pd.DataFrame, tsv_chunk: pd.DataFrame) -> pd.DataFrame:
    """Merge data chunk with TSV chunk DataFrame on genomic positions.

    Matches values between the 'cadd_gen_position' column in tsv_chunk and
    the corresponding columns in data_chunk. If a matching CADD score is not
    found in tsv_chunk, the PHRED value will be set to "Cadd score unavailable".

    Args:
        data_chunk (pd.DataFrame): The DataFrame containing genomic data to be merged.
        tsv_chunk (pd.DataFrame): The DataFrame containing CADD genomic positions.

    Returns:
        pd.DataFrame: The merged DataFrame based on the matching positions.
    """
    merged_df = pd.merge(
        data_chunk,
        tsv_chunk[["cadd_gen_position", "PHRED"]],
        left_on="gen_pos",
        right_on="cadd_gen_position",
        how="left",
    )

    return merged_df.drop(columns=["cadd_gen_position"])


def cadd_pipeline(dataframe: pd.DataFrame, cadd_folder_path: str) -> pd.DataFrame:
    """
    Process genomic data through CADD pipeline stages.

    Process data through multiple stages: file creation, uploading, fetching
    results, parsing, and merging with CADD annotation data.

    Args:
        dataframe (pd.DataFrame): The input genomic data.
        cadd_folder_path (str): Path to store temporary input/output files for CADD processing.

    Returns:
        pd.DataFrame: The final merged dataframe with CADD scores.
    """
    num_chunks = max(2, len(dataframe) // 1000)
    data_chunks = np.array_split(dataframe, num_chunks)
    vcf_gziped_chunks = {}
    cadd_job_chunks = {}
    tsv_chunks = {}
    merged_chunks = {}

    cadd_folder_path = os.path.join(cadd_folder_path, datetime.now().strftime("%Y%m%d_%H%M%S"))
    cadd_folder_input = os.path.join(cadd_folder_path, "input")
    cadd_folder_output = os.path.join(cadd_folder_path, "output")
    if not os.path.exists(cadd_folder_input):
        os.makedirs(cadd_folder_input)
    if not os.path.exists(cadd_folder_output):
        os.makedirs(cadd_folder_output)

    with ProcessPoolExecutor() as executor:
        jobs = {
            executor.submit(create_cadd_input_files, data_chunks[i], cadd_folder_input, i): i for i in range(num_chunks)
        }
        for job in jobs:
            chunk_id, vcf_chunk_path = job.result()
            vcf_gziped_chunks[chunk_id] = gzip_file(vcf_chunk_path)
            os.remove(os.path.join(cadd_folder_input, vcf_chunk_path))

    for i in range(num_chunks):
        chunk_id, cadd_job_url = send_cadd_input_files(vcf_gziped_chunks[i], i)
        os.remove(os.path.join(cadd_folder_input, vcf_gziped_chunks[chunk_id]))
        cadd_job_chunks[chunk_id] = cadd_job_url

    for i in range(num_chunks):
        chunk_id, cadd_gzip_file_path = get_cadd_output_files(cadd_job_chunks[i], cadd_folder_output, i)
        renamed_path = os.path.join(cadd_folder_output, f"cadd_chunk_{chunk_id}.tsv.gz")
        os.rename(os.path.join(cadd_folder_output, cadd_gzip_file_path), renamed_path)
        tsv_chunks[chunk_id] = renamed_path

    with ProcessPoolExecutor() as executor:
        jobs = {
            executor.submit(gunzip_file, os.path.join(cadd_folder_output, tsv_chunks[i]), i): i
            for i in range(num_chunks)
        }
        for job in jobs:
            chunk_id, cadd_tsv_file_path = job.result()
            merged_chunks[chunk_id] = merge_with_tsv(data_chunks[chunk_id], parse_tsv(cadd_tsv_file_path))
            os.remove(os.path.join(cadd_folder_output, cadd_tsv_file_path))
    return pd.concat(merged_chunks.values(), ignore_index=True)
