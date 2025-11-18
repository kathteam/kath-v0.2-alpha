"""
Workspace Service Layer.

Provides business logic for workspace file operations, abstracting database queries
from route handlers. Supports filtering, sorting, and pagination.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, or_

from src.database import FileRepository, VariantRepository, WorkspaceRepository
from src.database.config import get_db_session


class WorkspaceService:
    """Service for workspace and file operations."""

    def __init__(self):
        """Initialize service with repositories."""
        self._workspace_repo = None
        self._file_repo = None
        self._variant_repo = None

    @property
    def workspace_repo(self):
        """Lazy-load workspace repository."""
        if self._workspace_repo is None:
            self._workspace_repo = WorkspaceRepository()
        return self._workspace_repo

    @property
    def file_repo(self):
        """Lazy-load file repository."""
        if self._file_repo is None:
            self._file_repo = FileRepository()
        return self._file_repo

    @property
    def variant_repo(self):
        """Lazy-load variant repository."""
        if self._variant_repo is None:
            self._variant_repo = VariantRepository()
        return self._variant_repo

    def get_file_data(
        self,
        workspace_id: str,
        file_path: str,
        page: int = 0,
        rows_per_page: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sorts: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[str], List[List[Any]], int]:
        """
        Retrieve file data with filtering, sorting, and pagination.

        Args:
            workspace_id: Workspace UUID
            file_path: Relative file path within workspace
            page: Page number (0-indexed)
            rows_per_page: Number of rows per page
            filters: Filter dictionary with format: {column: {operator: str, value: str}}
            sorts: Sort dictionary with format: {column: "asc"|"desc"}

        Returns:
            Tuple of (header, rows, total_count):
                - header: List of column names
                - rows: List of row data (each row is a list of values)
                - total_count: Total number of rows matching filters

        Raises:
            FileNotFoundError: If workspace or file doesn't exist
        """
        # Get or create workspace (auto-index when accessing files)
        workspace = self.workspace_repo.get_or_create(workspace_id)

        # Get or create file (auto-index when accessing files from filesystem)
        file_name = os.path.basename(file_path) if file_path else "root"
        file_obj = self.file_repo.get_or_create(
            workspace_id=workspace_id,
            path=file_path,
            name=file_name,
            file_type="file"
        )

        # Parse header
        import json

        header = json.loads(file_obj.header_json) if file_obj.header_json else []

        # Build filter criteria for database query
        filter_dict = self._build_filter_dict(filters, header)

        # Build sort criteria
        sort_column, sort_order = self._parse_sort(sorts, header)

        # Query variants with filtering, sorting, and pagination
        variants, total_count = self.variant_repo.filter_variants(
            file_id=file_obj.id,
            filters=filter_dict,
            sort_column=sort_column,
            sort_order=sort_order,
            limit=rows_per_page,
            offset=page * rows_per_page,
        )

        # Convert variant objects to row format
        rows = self._variants_to_rows(variants, header)

        return header, rows, total_count

    def _build_filter_dict(self, filters: Optional[Dict[str, Any]], header: List[str]) -> Dict[str, Any]:
        """
        Build filter dictionary for repository query.

        Args:
            filters: Filter dictionary from request
            header: Column names

        Returns:
            Filter dictionary for repository
        """
        if not filters:
            return {}

        filter_dict = {}

        for column, filter_info in filters.items():
            if column not in header:
                continue

            operator = filter_info.get("operator")
            value = filter_info.get("value")

            # Map to repository filter format
            filter_dict[column] = {"operator": operator, "value": value}

        return filter_dict

    def _parse_sort(self, sorts: Optional[Dict[str, str]], header: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse sort dictionary to extract column and order.

        Args:
            sorts: Sort dictionary from request
            header: Column names

        Returns:
            Tuple of (sort_column, sort_order)
        """
        if not sorts:
            return None, None

        # Get first sort (only support single column sort for now)
        sort_column, sort_order = list(sorts.items())[0]

        if sort_column not in header:
            return None, None

        return sort_column, sort_order

    def _variants_to_rows(self, variants: List[Any], header: List[str]) -> List[List[Any]]:
        """
        Convert variant objects to row format matching header columns.

        Args:
            variants: List of Variant model instances
            header: Column names

        Returns:
            List of rows (each row is a list of values)
        """
        rows = []

        # Define core variant columns mapping
        core_columns = {
            "chromosome": "chromosome",
            "position": "position",
            "ref_allele": "ref_allele",
            "alt_allele": "alt_allele",
            "variant_id": "variant_id",
            "gen_pos": "gen_pos",
            "gene": "gene",
            "transcript": "transcript",
            "consequence": "consequence",
        }

        for variant in variants:
            row = []
            import json

            # Parse data_json once
            data_dict = {}
            if variant.data_json:
                try:
                    data_dict = json.loads(variant.data_json)
                except json.JSONDecodeError:
                    pass

            # Map each header column to variant data
            for col in header:
                # Check core columns first
                if col in core_columns:
                    attr_name = core_columns[col]
                    value = getattr(variant, attr_name, None)
                    row.append(value if value is not None else "")
                # Check data_json for additional columns
                elif col in data_dict:
                    row.append(data_dict[col])
                else:
                    row.append("")

            rows.append(row)

        return rows

    def file_exists(self, workspace_id: str, file_path: str) -> bool:
        """
        Check if file exists in workspace.

        Args:
            workspace_id: Workspace UUID
            file_path: Relative file path

        Returns:
            True if file exists, False otherwise
        """
        file_obj = self.file_repo.find_by_path(workspace_id, file_path)
        return file_obj is not None
