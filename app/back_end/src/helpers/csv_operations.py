"""
CSV file operations module.

This module provides functionality for reading, writing, filtering and sorting CSV files.
It encapsulates common CSV operations used throughout the workspace routes.
"""

import csv
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utils.exceptions import UnexpectedError


@dataclass
class FilterInfo:
    """Information about how to filter a column."""

    key: str
    operator: str
    value: str


@dataclass
class SortInfo:
    """Information about how to sort a column."""

    key: str
    order: str  # "asc" or "desc"


class CsvOperations:
    """Handles CSV file operations including reading, filtering, and sorting."""

    FILTER_OPERATORS = {
        "contains": lambda val, filter_val: filter_val.lower() in val.lower(),
        "does-not-contain": lambda val, filter_val: filter_val.lower() not in val.lower(),
        "equals": lambda val, filter_val: val.lower() == filter_val.lower(),
        "does-not-equal": lambda val, filter_val: val.lower() != filter_val.lower(),
        "starts-with": lambda val, filter_val: val.lower().startswith(filter_val.lower()),
        "ends-with": lambda val, filter_val: val.lower().endswith(filter_val.lower()),
        "is-empty": lambda val, _: val.strip() == "",
        "is-not-empty": lambda val, _: val.strip() != "",
    }

    @staticmethod
    def is_number(value: str) -> bool:
        """Check if a string can be converted to a number."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def convert_to_number(value: str) -> Union[float, str]:
        """Convert a string to a number if possible."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def apply_filter(row: List[str], filter_info: FilterInfo, header: List[str]) -> bool:
        """
        Apply filter criteria to a row.

        Args:
            row (List[str]): The row to filter.
            filter_info (FilterInfo): Filter criteria.
            header (List[str]): CSV header row.

        Returns:
            bool: True if row passes filter, False otherwise.
        """
        try:
            filter_index = header.index(filter_info.key)
            filter_func = CsvOperations.FILTER_OPERATORS.get(filter_info.operator)

            if not filter_func:
                raise UnexpectedError(f"Unknown filter operator: {filter_info.operator}")

            result: bool = filter_func(row[filter_index], filter_info.value)
            return result

        except ValueError:
            raise UnexpectedError(f"Filter key not found in header: {filter_info.key}")
        except Exception as e:
            raise UnexpectedError(f"Error applying filter: {str(e)}")

    @staticmethod
    def sort_rows(rows: List[List[str]], sort_info: SortInfo, header: List[str]) -> List[List[str]]:
        """
        Sort rows based on specified criteria.

        Args:
            rows (List[List[str]]): Rows to sort.
            sort_info (SortInfo): Sort criteria.
            header (List[str]): CSV header row.

        Returns:
            List[List[str]]: Sorted rows.
        """
        try:
            if not rows:
                return rows

            sort_index = header.index(sort_info.key)
            reverse_sort = sort_info.order == "desc"

            # Check if column contains numbers
            first_valid_value = next((row[sort_index] for row in rows if row[sort_index]), None)

            if first_valid_value and CsvOperations.is_number(first_valid_value):
                # Numeric sort
                return sorted(
                    rows,
                    key=lambda row: (
                        CsvOperations.convert_to_number(row[sort_index])
                        if row[sort_index]
                        else (float("-inf") if reverse_sort else float("inf"))
                    ),
                    reverse=reverse_sort,
                )
            else:
                # String sort
                return sorted(
                    rows,
                    key=lambda row: (
                        row[sort_index].lower() if row[sort_index] else ("\u0000" if reverse_sort else "\uFFFF")
                    ),
                    reverse=reverse_sort,
                )

        except ValueError:
            raise UnexpectedError(f"Sort key not found in header: {sort_info.key}")
        except Exception as e:
            raise UnexpectedError(f"Error sorting rows: {str(e)}")

    @classmethod
    def read_csv_file(
        cls,
        file_path: str,
        filter_info: Optional[FilterInfo] = None,
        sort_info: Optional[SortInfo] = None,
        start_row: int = 0,
        end_row: Optional[int] = None,
    ) -> Tuple[List[str], List[List[str]], int]:
        """
        Read a CSV file with optional filtering and sorting.

        Args:
            file_path (str): Path to CSV file.
            filter_info (FilterInfo, optional): Filter criteria.
            sort_info (SortInfo, optional): Sort criteria.
            start_row (int): First row to include (0-based).
            end_row (int, optional): Last row to include (exclusive).

        Returns:
            Tuple[List[str], List[List[str]], int]: Header row, data rows, total row count
        """
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Read header row

                # Read and filter rows
                rows = []
                total_rows = 0

                for row in reader:
                    total_rows += 1

                    # Apply filter if specified
                    if filter_info and not cls.apply_filter(row, filter_info, header):
                        continue

                    rows.append(row)

                # Apply sorting if specified
                if sort_info:
                    rows = cls.sort_rows(rows, sort_info, header)

                # Apply pagination
                if end_row is not None:
                    rows = rows[start_row:end_row]
                else:
                    rows = rows[start_row:]

                return header, rows, total_rows

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied reading CSV file: {file_path}")
        except Exception as e:
            raise UnexpectedError(f"Error reading CSV file: {str(e)}")

    @staticmethod
    def write_csv_file(
        file_path: str,
        header: List[str],
        rows: List[List[str]],
        index_file: Optional[str] = None,
        index_map: Optional[List[Tuple[int, int]]] = None,
    ) -> None:
        """
        Write data to a CSV file.

        Args:
            file_path (str): Path to CSV file.
            header (List[str]): Header row.
            rows (List[List[str]]): Data rows.
            index_file (str, optional): Path to index file.
            index_map (List[Tuple[int, int]], optional): Mapping of new to original row indices.
        """
        try:
            # Create temporary file
            temp_file = f"{file_path}.tmp"

            with open(temp_file, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)
                writer.writerows(rows)

            # Replace original with temp file
            os.replace(temp_file, file_path)

            # Write index file if provided
            if index_file and index_map:
                with open(index_file, "w", encoding="utf-8") as idxfile:
                    for orig_idx, new_idx in index_map:
                        idxfile.write(f"{orig_idx} {new_idx + 1}\n")

        except PermissionError:
            raise PermissionError(f"Permission denied writing CSV file: {file_path}")
        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            raise UnexpectedError(f"Error writing CSV file: {str(e)}")
