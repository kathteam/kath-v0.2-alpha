"""
This module defines the routes for aggregating data from user workspaces in a Flask application.
It provides two main routes for performing column-level calculations on CSV files stored in the
user's workspace. The supported operations include summing, averaging, counting, finding the
minimum, and finding the maximum values in specified columns.

The module emits real-time feedback to the users session via Socket.IO, providing status updates
on the calculations, handling skipped cells due to invalid data, and notifying the user of errors
such as file not found, permission denied, or unexpected issues.

Routes:
    - get_workspace_aggregate_all(relative_path):
        Calculates aggregate values (sum, avg, min, max, cnt) for multiple columns in a CSV file.

    - get_workspace_aggregate(relative_path):
        Calculates an aggregate value (sum, avg, min, max, cnt) for a single column in a CSV file.

Exceptions are handled to provide feedback through the users console using Socket.IO.
"""

import csv
import os
from ast import literal_eval

from flask import Blueprint, jsonify, request

from ..constants import CONSOLE_FEEDBACK_EVENT, WORKSPACE_AGGREGATE_ROUTE, WORKSPACE_DIR
from ..setup.extensions import logger
from ..utils.exceptions import UnexpectedError
from ..utils.helpers import is_number, socketio_emit_to_user_session

workspace_aggregate_route_bp = Blueprint("workspace_aggregate_route", __name__)


from ..utils.aggregation_helpers import format_aggregation_response, format_skipped_info, process_csv_for_aggregation


@workspace_aggregate_route_bp.route(f"{WORKSPACE_AGGREGATE_ROUTE}/all/<path:relative_path>", methods=["GET"])
def get_workspace_aggregate_all(relative_path):
    """Calculate aggregate values for multiple columns in a CSV file.

    Args:
        relative_path (str): The relative path to the CSV file inside the user's workspace.

    Request Headers:
        - uuid: A unique identifier for the user's session.
        - sid: A session identifier for emitting real-time console feedback via Socket.IO.

    Query Parameters:
        - columnsAggregation (str): A stringified dictionary mapping column names to
          aggregation operations ('sum', 'avg', 'min', 'max', or 'cnt').

    Returns:
        Response (JSON): Aggregated results for each column or an error message.

    Emits:
        Console feedback via Socket.IO with progress, warnings, and errors.
    """
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")

    # Validate required headers
    if not uuid or not sid:
        return jsonify({"error": "UUID and SID headers are required"}), 400

    # Emit initial feedback
    socketio_emit_to_user_session(
        CONSOLE_FEEDBACK_EVENT,
        {"type": "info", "message": f"Calculating all file at '{relative_path}'..."},
        uuid,
        sid,
    )

    # Set up file paths and parse column config
    file_path = os.path.join(WORKSPACE_DIR, uuid, relative_path)
    columns_aggregation = literal_eval(request.args.get("columnsAggregation"))

    try:
        # Process the CSV file
        aggregators, _ = process_csv_for_aggregation(file_path, columns_aggregation)

        # Format the response
        response_data = format_aggregation_response(relative_path, aggregators, columns_aggregation)

        # Check for and emit warnings about skipped cells
        skipped_columns_info = format_skipped_info(aggregators)
        if skipped_columns_info:
            socketio_emit_to_user_session(
                CONSOLE_FEEDBACK_EVENT,
                {
                    "type": "warn",
                    "message": f"Cells skipped due to non-numeric values: {', '.join(skipped_columns_info)}",
                },
                uuid,
                sid,
            )

        # Emit success message
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"File at '{relative_path}' all calculated successfully.",
            },
            uuid,
            sid,
        )

        return jsonify(response_data)

    except (FileNotFoundError, PermissionError, UnexpectedError) as e:
        error_type = type(e).__name__
        error_message = e.message if isinstance(e, UnexpectedError) else str(e)
        logger.error(f"{error_type}: %s while calculating all %s", error_message, file_path)

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"{error_type}: {error_message} while calculating all {file_path}",
            },
            uuid,
            sid,
        )

        if isinstance(e, FileNotFoundError):
            return jsonify({"error": "Requested file not found"}), 404
        elif isinstance(e, PermissionError):
            return jsonify({"error": "Permission denied"}), 403
        else:
            return jsonify({"error": "An internal error occurred"}), 500


from ..utils.aggregation_helpers import ColumnAggregator


@workspace_aggregate_route_bp.route(f"{WORKSPACE_AGGREGATE_ROUTE}/<path:relative_path>", methods=["GET"])
def get_workspace_aggregate(relative_path):
    """Calculate an aggregate value for a single column in a CSV file.

    Args:
        relative_path (str): The relative path to the CSV file inside the user's workspace.

    Request Headers:
        - uuid: A unique identifier for the user's session.
        - sid: A session identifier for emitting real-time console feedback via Socket.IO.

    Query Parameters:
        - field (str): The name of the column to aggregate.
        - action (str): The type of aggregation ('sum', 'avg', 'min', 'max', or 'cnt').

    Returns:
        Response (JSON): The aggregated result or an error message.

    Emits:
        Console feedback via Socket.IO with progress, warnings, and errors.
    """
    # Validate headers
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")
    if not uuid or not sid:
        return jsonify({"error": "UUID and SID headers are required"}), 400

    # Validate parameters
    field = request.args.get("field")
    action = request.args.get("action")
    if not field or not action:
        return jsonify({"error": "field and action parameters are required"}), 400

    # Emit start feedback
    socketio_emit_to_user_session(
        CONSOLE_FEEDBACK_EVENT,
        {"type": "info", "message": f"Calculating file at '{relative_path}'..."},
        uuid,
        sid,
    )

    # Setup paths
    file_path = os.path.join(WORKSPACE_DIR, uuid, relative_path)
    aggregator = ColumnAggregator(action)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader)

            if not header:
                return jsonify({"error": "Empty file"}), 400

            if field not in header:
                socketio_emit_to_user_session(
                    CONSOLE_FEEDBACK_EVENT,
                    {
                        "type": "errr",
                        "message": f"Column '{field}' not found in the file '{relative_path}'",
                    },
                    uuid,
                    sid,
                )
                return jsonify({"error": f"Column '{field}' not found"}), 404

            header_index = header.index(field)
            for row in reader:
                if header_index >= len(row):
                    aggregator.skipped_count += 1
                    continue
                aggregator.process_value(row[header_index])

        # Handle warnings if cells were skipped
        if aggregator.skipped_count:
            socketio_emit_to_user_session(
                CONSOLE_FEEDBACK_EVENT,
                {
                    "type": "warn",
                    "message": f"At column '{field}' {aggregator.skipped_count} cells "
                    + "were skipped because they contain non-numeric values.",
                },
                uuid,
                sid,
            )

        # Emit success message
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"File at '{relative_path}' calculated successfully.",
            },
            uuid,
            sid,
        )

        # Build and return response
        response_data = {
            "fileId": relative_path,
            "field": field,
            "action": action,
            "value": aggregator.get_final_value(),
        }

        return jsonify(response_data)

    except (FileNotFoundError, PermissionError, UnexpectedError) as e:
        error_type = type(e).__name__
        error_message = e.message if isinstance(e, UnexpectedError) else str(e)
        logger.error(f"{error_type}: %s while calculating %s", error_message, file_path)

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"{error_type}: {error_message} while calculating {file_path}",
            },
            uuid,
            sid,
        )

        if isinstance(e, FileNotFoundError):
            return jsonify({"error": "Requested file not found"}), 404
        elif isinstance(e, PermissionError):
            return jsonify({"error": "Permission denied"}), 403
        return jsonify({"error": "An internal error occurred"}), 500
