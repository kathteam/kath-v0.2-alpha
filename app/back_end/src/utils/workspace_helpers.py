"""Helper functions for workspace file operations."""

import csv
import os
from typing import Any, Dict, List, Optional, Tuple

from ..constants import WORKSPACE_DIR


def paginate_rows(rows: List[List[str]], page: int, rows_per_page: int) -> List[List[str]]:
    """Return a paginated subset of rows.

    Args:
        rows: List of rows to paginate
        page: Page number (0-based)
        rows_per_page: Number of rows per page

    Returns:
        List of rows for the requested page
    """
    start_row = page * rows_per_page
    end_row = start_row + rows_per_page
    return rows[start_row:end_row]


def read_csv_file(
    file_path: str, page: int = 0, rows_per_page: Optional[int] = None
) -> Tuple[List[str], List[List[str]], int]:
    """Read a CSV file with optional pagination.

    Args:
        file_path: Path to CSV file
        page: Page number for pagination
        rows_per_page: Number of rows per page, or None for all rows

    Returns:
        Tuple of (header_row, data_rows, total_rows)
    """
    all_rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        all_rows = list(reader)

    total_rows = len(all_rows)
    if rows_per_page is not None:
        all_rows = paginate_rows(all_rows, page, rows_per_page)

    return header, all_rows, total_rows


def write_csv_file(
    file_path: str,
    header: List[str],
    rows: List[List[str]],
    start_row: Optional[int] = None,
    total_rows: Optional[int] = None,
) -> None:
    """Write or update a CSV file.

    If start_row is provided, updates the file at that position.
    Otherwise creates a new file.

    Args:
        file_path: Path to CSV file
        header: Header row
        rows: Data rows to write
        start_row: Starting row for update, or None for new file
        total_rows: Total expected rows for validation
    """
    if start_row is not None:
        # Update existing file
        temp_path = file_path + ".tmp"
        with open(file_path, "r", encoding="utf-8") as src, open(temp_path, "w", encoding="utf-8", newline="") as dst:
            writer = csv.writer(dst)
            reader = csv.reader(src)

            # Copy header
            orig_header = next(reader)
            writer.writerow(orig_header)

            # Copy unchanged rows
            for i, row in enumerate(reader):
                if i < start_row:
                    writer.writerow(row)
                elif i < start_row + len(rows):
                    writer.writerow(rows[i - start_row])
                else:
                    writer.writerow(row)

        os.replace(temp_path, file_path)

    else:
        # Create new file
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
