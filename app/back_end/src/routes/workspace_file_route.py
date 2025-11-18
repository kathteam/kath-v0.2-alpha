"""
This module defines routes for workspace file operations.

For detailed API documentation, see workspace_route.py.
"""

import os

from flask import Blueprint, jsonify, request
from flask_compress import Compress

from ..helpers.csv_operations import CsvOperations, FilterInfo, SortInfo
from ..helpers.workspace_events import WorkspaceEvents
from ..helpers.workspace_file_operations import WorkspaceFileOperations
from ..helpers.workspace_responses import WorkspaceResponses
from ..setup.constants import (
    WORKSPACE_CREATE_ROUTE,
    WORKSPACE_DELETE_ROUTE,
    WORKSPACE_FILE_ROUTE,
    WORKSPACE_RENAME_ROUTE,
)
from ..setup.extensions import compress
from ..utils.exceptions import UnexpectedError

# Create blueprint
workspace_route_bp = Blueprint("workspace", __name__)


@workspace_route_bp.route(f"{WORKSPACE_FILE_ROUTE}/<path:relative_path>", methods=["GET"])
@compress.compressed()
def get_workspace_file(relative_path):
    """
    Retrieves file content with pagination and optional filtering/sorting.

    See docstring in workspace_route.py for full details.
    """
    # Validate headers
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")

    if not uuid:
        return WorkspaceResponses.error_response("UUID header is missing", 400)
    if not sid:
        return WorkspaceResponses.error_response("SID header is missing", 400)

    # Get query parameters with defaults
    page = int(request.args.get("page", 0))
    rows_per_page = int(request.args.get("rowsPerPage", 100))
    filter_data = request.args.get("filter")
    sort_data = request.args.get("sort")

    # Calculate pagination
    start_row = page * rows_per_page
    end_row = start_row + rows_per_page

    # Process filter and sort if provided
    filter_info = None
    sort_info = None

    if filter_data:
        key, info = list(filter_data.items())[0]
        filter_info = FilterInfo(key=key, operator=info.get("operator"), value=info.get("value"))

    if sort_data:
        key, order = list(sort_data.items())[0]
        sort_info = SortInfo(key=key, order=order)

    try:
        # Ensure workspace exists
        file_path = WorkspaceFileOperations.get_workspace_path(uuid, relative_path)
        WorkspaceFileOperations.ensure_user_workspace_exists(uuid)

        # Start operation notification
        WorkspaceEvents.file_operation_started("retrieve", relative_path, uuid, sid)

        # Handle empty file case
        if os.path.getsize(file_path) == 0:
            response = WorkspaceResponses.format_csv_response(page=page, total_rows=0, header=[], rows=[])
            return WorkspaceResponses.success_response(response)

        # Read and process CSV file
        header, rows, total_rows = CsvOperations.read_csv_file(
            file_path=file_path, filter_info=filter_info, sort_info=sort_info, start_row=start_row, end_row=end_row
        )

        # Generate index file for sorted results
        if sort_info:
            index_path = f"{file_path}.index"
            index_map = [(i, i + start_row) for i in range(len(rows))]
            CsvOperations.write_csv_file(
                file_path=file_path, header=header, rows=rows, index_file=index_path, index_map=index_map
            )

        # Format response
        response = WorkspaceResponses.format_csv_response(page=page, total_rows=total_rows, header=header, rows=rows)

        # Operation completed notification
        WorkspaceEvents.file_operation_completed("retrieve", relative_path, uuid, sid)

        return WorkspaceResponses.success_response(response)

    except Exception as e:
        # Error handling and notification
        WorkspaceEvents.file_operation_error(e, "retrieve", relative_path, uuid, sid)
        return WorkspaceResponses.handle_workspace_error(e, "retrieving", file_path)


@workspace_route_bp.route(f"{WORKSPACE_FILE_ROUTE}/<path:relative_path>", methods=["PUT"])
@compress.compressed()
def put_workspace_file(relative_path):
    """
    Saves updates to a workspace file.

    See docstring in workspace_route.py for full details.
    """
    # Validate headers
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")

    if not uuid:
        return WorkspaceResponses.error_response("UUID header is missing", 400)
    if not sid:
        return WorkspaceResponses.error_response("SID header is missing", 400)

    # Get request data
    data = request.json
    page = data.get("page")
    rows_per_page = data.get("rowsPerPage")
    header = data.get("header")
    rows = data.get("rows")

    try:
        # Get file paths and ensure workspace exists
        file_path = WorkspaceFileOperations.get_workspace_path(uuid, relative_path)
        index_path = f"{file_path}.index"
        WorkspaceFileOperations.ensure_user_workspace_exists(uuid)

        # Start operation notification
        WorkspaceEvents.file_operation_started("save", relative_path, uuid, sid)

        # Ensure file exists
        WorkspaceFileOperations.validate_file_access(file_path)

        # Read the current file and index to determine row mapping
        with open(index_path, "r", encoding="utf-8") as index:
            index_map = []
            for line in index:
                if not line.strip():
                    continue
                org_line, new_line = map(int, line.split())
                index_map.append((org_line, new_line - 1))

        # Save the file with updated rows
        CsvOperations.write_csv_file(
            file_path=file_path, header=header, rows=rows, index_file=index_path, index_map=index_map
        )

        # Format response
        response = WorkspaceResponses.format_csv_response(page=page, total_rows=len(rows), header=header, rows=rows)

        # Send success notifications
        WorkspaceEvents.file_operation_completed("save", relative_path, uuid, sid)
        WorkspaceEvents.emit_file_save_feedback("success", uuid, sid)

        return WorkspaceResponses.success_response(response)

    except Exception as e:
        # Error handling and notifications
        WorkspaceEvents.file_operation_error(e, "save", relative_path, uuid, sid)
        WorkspaceEvents.emit_file_save_feedback("error", uuid, sid)
        return WorkspaceResponses.handle_workspace_error(e, "saving", file_path)

        # Operation completed notification
        WorkspaceEvents.file_operation_completed("retrieve", relative_path, uuid, sid)

        return WorkspaceResponses.success_response(response)

    except Exception as e:
        # Error handling and notification
        WorkspaceEvents.file_operation_error(e, "retrieve", relative_path, uuid, sid)
        return WorkspaceResponses.handle_workspace_error(e, "retrieving", file_path)
