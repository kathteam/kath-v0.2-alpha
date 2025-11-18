"""
Workspace response formatting module.

This module provides standardized response formatting for workspace operations.
It ensures consistent error handling and response structure across routes.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Response, jsonify

from ..utils.workspace_errors import (
    ConcurrencyError,
    FileFormatError,
    InvalidOperationError,
    ValidationError,
    WorkspaceAccessError,
    WorkspaceError,
    WorkspaceNotFoundError,
)

# Configure logger
logger = logging.getLogger(__name__)


class WorkspaceResponses:
    """Handles standardized response formatting for workspace operations."""

    # Error code mapping
    ERROR_CODES = {
        ValidationError: 400,
        WorkspaceNotFoundError: 404,
        WorkspaceAccessError: 403,
        InvalidOperationError: 400,
        FileFormatError: 400,
        ConcurrencyError: 409,
        Exception: 500,  # Default for unhandled exceptions
    }

    @staticmethod
    def success_response(data: Dict[str, Any]) -> Response:
        """
        Create a success response with standardized format.

        Args:
            data (Dict[str, Any]): Response data.

        Returns:
            Response: Flask response object.
        """
        return jsonify(data)

    @staticmethod
    def error_response(
        message: str, status_code: int = 500, error_type: Optional[str] = None, details: Optional[Dict] = None
    ) -> Tuple[Response, int]:
        """
        Create an error response with standardized format.

        Args:
            message (str): Error message.
            status_code (int): HTTP status code.
            error_type (str, optional): Type of error.
            details (Dict, optional): Additional error details.

        Returns:
            Tuple[Response, int]: Flask response and status code.
        """
        error_data: Dict[str, Any] = {"error": message, "type": error_type or "UnknownError"}
        if details:
            error_data["details"] = details

        return jsonify(error_data), status_code

    @staticmethod
    def format_csv_response(page: int, total_rows: int, header: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """
        Format response for CSV file operations.

        Args:
            page (int): Current page number.
            total_rows (int): Total number of rows.
            header (List[str]): CSV header row.
            rows (List[List[str]]): Data rows.

        Returns:
            Dict[str, Any]: Formatted response data.
        """
        return {"page": page, "totalRows": total_rows, "header": header, "rows": rows}

    @staticmethod
    def format_file_operation_response(
        operation: str, path: str, item_type: str, new_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format response for file operations (create/rename/delete).

        Args:
            operation (str): Operation performed ("create", "rename", "delete").
            path (str): Path to the affected item.
            item_type (str): Type of item ("file" or "folder").
            new_path (str, optional): New path for rename operations.

        Returns:
            Dict[str, Any]: Formatted response data.

        Raises:
            InvalidOperationError: If operation is not recognized.
        """
        base_path = path.split("/")[-1] if path else ""

        if operation == "create":
            return {"newId": path, "newLabel": base_path, "newType": item_type}
        elif operation == "rename" and new_path:
            new_base = new_path.split("/")[-1]
            return {"newId": new_path, "newLabel": new_base, "newType": item_type}
        elif operation == "delete":
            return {"oldId": path}
        else:
            raise InvalidOperationError(f"Invalid file operation: {operation}", operation)

    @staticmethod
    def handle_workspace_error(e: Exception, operation: str, path: str) -> Tuple[Response, int]:
        """
        Handle common workspace operation errors.

        Args:
            e (Exception): The caught exception.
            operation (str): Operation being performed.
            path (str): Path being operated on.

        Returns:
            Tuple[Response, int]: Error response and status code.
        """
        # Log the error
        logger.error("%s: %s while %s %s", e.__class__.__name__, str(e), operation, path)

        # Get the appropriate status code
        status_code = WorkspaceResponses.ERROR_CODES.get(type(e), WorkspaceResponses.ERROR_CODES[Exception])

        # Get additional details for workspace errors
        details = getattr(e, "details", None) if isinstance(e, WorkspaceError) else None

        return WorkspaceResponses.error_response(str(e), status_code, e.__class__.__name__, details)
