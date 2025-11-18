"""Helper classes and functions for data aggregation operations."""

from typing import Dict


class ColumnAggregator:
    """Class that handles aggregation operations for a column."""

    def __init__(self, action):
        """Initialize the aggregator with an action type."""
        self.action = action
        self.value = self._initialize_value()
        self.count = 0
        self.skipped_count = 0

    def _initialize_value(self):
        """Initialize the value based on the action type."""
        if self.action == "min":
            return float("inf")
        elif self.action == "max":
            return float("-inf")
        return float(0)

    def process_value(self, value):
        """Process a single value."""
        if self.action == "cnt":
            if value:
                self.value += float(1)
            else:
                self.skipped_count += 1
            return

        if not value or not self._is_numeric(value):
            self.skipped_count += 1
            return

        value = float(value)
        if self.action == "sum":
            self.value += value
        elif self.action == "avg":
            self.value += value
            self.count += 1
        elif self.action == "min":
            self.value = min(self.value, value)
        elif self.action == "max":
            self.value = max(self.value, value)

    def _is_numeric(self, value):
        """Check if a value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def get_final_value(self):
        """Get the final value with appropriate formatting."""
        # Handle averages
        if self.action == "avg" and self.count != 0:
            self.value /= self.count

        # Format the value
        if (
            self.value == float("inf")
            or self.value == float("-inf")
            or (self.value == float(0) and self.action not in ["min", "max", "cnt"])
        ):
            return "N/A"

        # Format integers without decimals
        if isinstance(self.value, float) and self.value.is_integer():
            return str(int(self.value))

        return f"{self.value:.3f}"


def process_csv_for_aggregation(file_path, columns_config):
    """Process a CSV file and calculate aggregations for specified columns.

    Args:
        file_path (str): Path to the CSV file
        columns_config (dict): Dictionary mapping column names to aggregation actions

    Returns:
        tuple: A tuple containing (aggregators, header_indices)
        where aggregators is a dict mapping column names to ColumnAggregator instances
        and header_indices is a dict mapping column names to their indices in the CSV
    """
    import csv

    aggregators: Dict[str, ColumnAggregator] = {
        field: ColumnAggregator(config["action"]) for field, config in columns_config.items()
    }

    header_indices: Dict[str, int] = {}
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)

        if not header:
            return aggregators, header_indices

        # Get indices for each column
        header_indices = {field: header.index(field) for field in columns_config.keys()}

        # Process each row
        for row in reader:
            for field, index in header_indices.items():
                if index >= len(row):
                    aggregators[field].skipped_count += 1
                    continue
                aggregators[field].process_value(row[index])

    return aggregators, header_indices


def format_aggregation_response(relative_path, aggregators, columns_config):
    """Format the aggregation results into a response structure.

    Args:
        relative_path (str): The relative path of the file being processed
        aggregators (dict): Dictionary mapping column names to ColumnAggregator instances
        columns_config (dict): Original columns configuration dictionary

    Returns:
        dict: Response data structure
    """
    return {
        "fileId": relative_path,
        "columnsAggregation": {
            field: {
                "action": columns_config[field]["action"],
                "value": aggregator.get_final_value(),
            }
            for field, aggregator in aggregators.items()
        },
    }


def format_skipped_info(aggregators):
    """Format skipped cell information for console feedback.

    Args:
        aggregators (dict): Dictionary mapping column names to ColumnAggregator instances

    Returns:
        list: List of strings describing skipped cells for each column
    """
    skipped_columns_info = []
    for field, aggregator in aggregators.items():
        if aggregator.skipped_count != 0:
            skipped_columns_info.append(f"'{field}': {aggregator.skipped_count} cells")
    return skipped_columns_info
