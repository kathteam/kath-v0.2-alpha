"""
This module defines routes for workspace file management operations (create/rename/delete).

For detailed API documentation, see workspace_route.py.
"""

import os

from flask import Blueprint, jsonify, request
from flask_compress import Compress

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
workspace_mgmt_bp = Blueprint("workspace_mgmt", __name__)


@workspace_mgmt_bp.route(f"{WORKSPACE_CREATE_ROUTE}/<path:relative_path>", methods=["PUT"])
@workspace_mgmt_bp.route(f"{WORKSPACE_CREATE_ROUTE}/", methods=["PUT"])
@compress.compressed()
def put_workspace_create(relative_path=None):
    """
    Creates a new file or directory in the workspace.

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
    label = data.get("label")
    item_type = data.get("type")

    # Handle root path case
    if relative_path is None:
        relative_path = ""

    try:
        # Ensure workspace exists and get paths
        base_path = WorkspaceFileOperations.get_workspace_path(uuid, relative_path)
        destination_path = os.path.join(base_path, label)
        WorkspaceFileOperations.ensure_user_workspace_exists(uuid)

        # Start operation notification
        WorkspaceEvents.file_operation_started("create", relative_path, uuid, sid)

        # Create file or directory
        if item_type == "file":
            WorkspaceFileOperations.create_file(destination_path)
        elif item_type == "folder":
            WorkspaceFileOperations.create_directory(destination_path)
        else:
            raise UnexpectedError(f"Invalid item type: {item_type}")

        # Format response
        response = WorkspaceResponses.format_file_operation_response(
            operation="create", path=os.path.join(relative_path, label) if relative_path else label, item_type=item_type
        )

        # Notify success
        WorkspaceEvents.file_operation_completed("create", relative_path, uuid, sid)
        WorkspaceEvents.emit_workspace_update(uuid, sid)

        return WorkspaceResponses.success_response(response)

    except Exception as e:
        # Error handling and notification
        WorkspaceEvents.file_operation_error(e, "create", relative_path, uuid, sid)
        return WorkspaceResponses.handle_workspace_error(e, "creating", destination_path)


@workspace_mgmt_bp.route(f"{WORKSPACE_RENAME_ROUTE}/<path:relative_path>", methods=["PUT"])
@compress.compressed()
def put_workspace_rename(relative_path):
    """
    Renames a file or directory in the workspace.

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
    label = data.get("label")
    item_type = data.get("type")

    try:
        # Get paths and ensure workspace exists
        old_path = WorkspaceFileOperations.get_workspace_path(uuid, relative_path)
        new_path = os.path.join(os.path.dirname(old_path), label)
        WorkspaceFileOperations.ensure_user_workspace_exists(uuid)

        # Start operation notification
        WorkspaceEvents.file_operation_started("rename", relative_path, uuid, sid)

        # Clean up auxiliary files
        if item_type == "file":
            WorkspaceFileOperations.clean_auxiliary_files(old_path)

        # Rename the item
        WorkspaceFileOperations.rename_item(old_path, new_path)

        # Format response
        new_relative_path = f"{os.path.dirname(relative_path)}/{label}" if os.path.dirname(relative_path) else label
        response = WorkspaceResponses.format_file_operation_response(
            operation="rename", path=relative_path, item_type=item_type, new_path=new_relative_path
        )

        # Notify success
        WorkspaceEvents.file_operation_completed("rename", relative_path, uuid, sid)
        WorkspaceEvents.emit_workspace_update(uuid, sid)

        return WorkspaceResponses.success_response(response)

    except Exception as e:
        # Error handling and notification
        WorkspaceEvents.file_operation_error(e, "rename", relative_path, uuid, sid)
        return WorkspaceResponses.handle_workspace_error(e, "renaming", old_path)


@workspace_mgmt_bp.route(f"{WORKSPACE_DELETE_ROUTE}/<path:relative_path>", methods=["PUT"])
@compress.compressed()
def put_workspace_delete(relative_path):
    """
    Deletes a file or directory from the workspace.

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
    item_type = data.get("type")

    try:
        # Get path and ensure workspace exists
        destination_path = WorkspaceFileOperations.get_workspace_path(uuid, relative_path)
        WorkspaceFileOperations.ensure_user_workspace_exists(uuid)

        # Start operation notification
        WorkspaceEvents.file_operation_started("delete", relative_path, uuid, sid)

        # Clean up auxiliary files for files
        if item_type == "file":
            WorkspaceFileOperations.clean_auxiliary_files(destination_path)

        # Delete the item
        WorkspaceFileOperations.delete_item(destination_path, is_directory=(item_type == "folder"))

        # Format response
        response = WorkspaceResponses.format_file_operation_response(
            operation="delete", path=relative_path, item_type=item_type
        )

        # Notify success
        WorkspaceEvents.file_operation_completed("delete", relative_path, uuid, sid)
        WorkspaceEvents.emit_workspace_update(uuid, sid)

        return WorkspaceResponses.success_response(response)

    except Exception as e:
        # Error handling and notification
        WorkspaceEvents.file_operation_error(e, "delete", relative_path, uuid, sid)
        return WorkspaceResponses.handle_workspace_error(e, "deleting", destination_path)
