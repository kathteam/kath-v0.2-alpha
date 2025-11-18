"""
Workspace apply route module.
This module defines routes for applying algorithms to files and saving the results to the user's
workspace.
"""

# pylint: disable=broad-exception-caught

import os
import time

import pandas as pd
from flask import Blueprint, jsonify, request

from ..constants import CONSOLE_FEEDBACK_EVENT, WORKSPACE_APPLY_ROUTE, WORKSPACE_DIR, WORKSPACE_UPDATE_FEEDBACK_EVENT
from ..setup.extensions import env, logger
from ..tools import add_spliceai_eval_columns, cadd_pipeline, main_revel_pipeline
from ..utils.exceptions import UnexpectedError
from ..utils.helpers import socketio_emit_to_user_session

workspace_apply_route_bp = Blueprint("workspace_apply_route", __name__)


from ..utils.algorithm_helpers import (
    handle_existing_data,
    process_algorithm_pipeline,
    save_algorithm_results,
    setup_file_paths,
    validate_request_args,
    validate_request_headers,
)


@workspace_apply_route_bp.route(f"{WORKSPACE_APPLY_ROUTE}/spliceai/<path:relative_path>", methods=["GET"])
def get_workspace_apply_spliceai(relative_path):
    """Apply the SpliceAI algorithm to a file and save the results."""
    # Validate request
    if error := validate_request_headers(request):
        return error
    if error := validate_request_args(request):
        return error

    # Get request parameters
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")
    override = request.args.get("override")
    applyTo = request.args.get("applyTo")

    try:
        # Setup paths and prepare data
        destination_path, apply_to = setup_file_paths(uuid, relative_path, applyTo)
        existing_data = handle_existing_data(destination_path, override)

        # Set up SpliceAI-specific paths
        fasta_path = os.path.join(WORKSPACE_DIR, "fasta", "hg38.fa")
        spliceai_dir = os.path.join(WORKSPACE_DIR, uuid, "spliceai")
        os.makedirs(spliceai_dir, exist_ok=True)

        # Process the algorithm
        result_data = process_algorithm_pipeline(
            "SpliceAI",
            add_spliceai_eval_columns,
            apply_to,
            relative_path,
            uuid,
            sid,
            {"fasta_path": fasta_path, "spliceai_dir": spliceai_dir},
        )

        # Save results
        save_algorithm_results(destination_path, result_data, existing_data)

        # Emit success feedback
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"SpliceAI algorithm was successfully applied to '{relative_path}'.",
            },
            uuid,
            sid,
        )

        socketio_emit_to_user_session(
            WORKSPACE_UPDATE_FEEDBACK_EVENT,
            {"status": "updated"},
            uuid,
            sid,
        )

        return jsonify({"message": "SpliceAI algorithm was successfully applied"}), 200

    except (FileNotFoundError, PermissionError, UnexpectedError, Exception) as e:
        error_type = type(e).__name__
        error_message = e.message if isinstance(e, UnexpectedError) else str(e)
        logger.error(
            f"{error_type}: %s while applying SpliceAI algorithm %s",
            error_message,
            destination_path,
        )

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"{error_type}: {error_message} while applying SpliceAI algorithm {destination_path}",
            },
            uuid,
            sid,
        )

        if isinstance(e, FileNotFoundError):
            return jsonify({"error": "Requested file not found"}), 404
        elif isinstance(e, PermissionError):
            return jsonify({"error": "Permission denied"}), 403
        return jsonify({"error": "An internal error occurred"}), 500


@workspace_apply_route_bp.route(f"{WORKSPACE_APPLY_ROUTE}/cadd/<path:relative_path>", methods=["GET"])
def get_workspace_apply_cadd(relative_path):
    """
    Route to apply the CADD algorithm to a file and save the result to the workspace.
    """

    # Check if 'uuid' and 'sid' are provided in the headers
    if "uuid" not in request.headers or "sid" not in request.headers:
        return jsonify({"error": "UUID and SID headers are required"}), 400

    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")

    # Check if 'override' and 'applyTo' are provided
    if "override" not in request.args or "applyTo" not in request.args:
        return (
            jsonify({"error": "'override', and 'applyTo' parameters are required"}),
            400,
        )

    # Explanation about the parameters:
    # - destination_path: string
    #     - The path to the destination file (where to save it) in the user's workspace
    #       Destination file can either be a new file or an existing file, check its existence
    # - override: boolean
    #     - If true, the existing destination file should be overridden
    #     - If false, the existing destination file should not be overridden and merged
    #       content should be appended
    # - apply_to: string
    #     - The path to the file to which the CADD algorithm should be applied
    #       Destination file can be the same file so ensure correct handling

    destination_path = os.path.join(WORKSPACE_DIR, uuid, relative_path)
    override = request.args.get("override")
    apply_to = os.path.join(WORKSPACE_DIR, uuid, request.args.get("applyTo"))

    try:
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "info",
                "message": f"Applying CADD algorithm to '{relative_path}' with " + f"override: '{override}'...",
            },
            uuid,
            sid,
        )

        #
        # TODO: Implement CADD algorithm apply and save logic using defined parameters
        # [destination_path, override, apply_to]

        existing_data = pd.DataFrame()
        if os.path.exists(destination_path):
            if override:
                os.remove(destination_path)
            else:
                existing_data = pd.read_csv(destination_path)

        cadd_dir = os.path.join(WORKSPACE_DIR, uuid, "cadd")
        os.makedirs(cadd_dir, exist_ok=True)

        try:
            data_copy = pd.read_csv(apply_to).convert_dtypes()[: env.get_max_entries()]
            result_data_cadd = cadd_pipeline(data_copy, cadd_dir)
        except Exception as e:
            raise RuntimeError(f"Error applying CADD algorithm: {e}")

        if not existing_data.empty:
            result_data_cadd = pd.concat([existing_data, result_data_cadd], ignore_index=True)
        result_data_cadd = result_data_cadd.convert_dtypes()
        try:
            result_data_cadd = result_data_cadd.convert_dtypes()
            result_data_cadd.to_csv(destination_path, index=False)
        except OSError as e:
            raise RuntimeError(f"Error saving file: {e}")

        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"CADD algorithm was successfully applied to '{relative_path}'.",
            },
            uuid,
            sid,
        )

        socketio_emit_to_user_session(
            WORKSPACE_UPDATE_FEEDBACK_EVENT,
            {"status": "updated"},
            uuid,
            sid,
        )

    except FileNotFoundError as e:
        logger.error(
            "FileNotFoundError: %s while applying CADD algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"FileNotFoundError: {e} while applying CADD algorithm " + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Requested file not found"}), 404
    except PermissionError as e:
        logger.error("PermissionError: %s while applying CADD algorithm %s", e, destination_path)
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"PermissionError: {e} while applying CADD algorithm {destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Permission denied"}), 403
    except UnexpectedError as e:
        logger.error(
            "UnexpectedError: %s while applying CADD algorithm %s",
            e.message,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"UnexpectedError: {e.message} while applying CADD algorithm " + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500
    except Exception as e:
        logger.error(
            "UnexpectedError: %s while applying CADD algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"UnexpectedError: {e} while applying CADD algorithm " + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500

    return jsonify({"message": "CADD algorithm was successfully applied"}), 200


# TODO - Implement the route to apply the REVEL algorithm to a file and save the result to the workspace. Currently, Idk why it does not work.
@workspace_apply_route_bp.route(f"{WORKSPACE_APPLY_ROUTE}/revel/<path:relative_path>", methods=["GET"])
def get_workspace_apply_revel(relative_path):
    """
    Route to apply the revel algorithm to a file and save the result to the workspace.
    """

    # Check if 'uuid' and 'sid' are provided in the headers
    if "uuid" not in request.headers or "sid" not in request.headers:
        return jsonify({"error": "UUID and SID headers are required"}), 400

    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")

    # Check if 'override' and 'applyTo' are provided
    if "override" not in request.args or "applyTo" not in request.args:
        return (
            jsonify({"error": "'override', and 'applyTo' parameters are required"}),
            400,
        )

    destination_path = os.path.join(WORKSPACE_DIR, uuid, relative_path)
    override = request.args.get("override")
    apply_to = os.path.join(WORKSPACE_DIR, uuid, request.args.get("applyTo"))
    revel_db_path = os.path.join(WORKSPACE_DIR, "revel", "revel_with_transcript_ids.db")

    try:
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "info",
                "message": f"Applying REVEL algorithm to '{relative_path}' with " + f"override: '{override}'...",
            },
            uuid,
            sid,
        )
        try:
            result_data_revel = main_revel_pipeline(dataset_path=apply_to, revel_db_path=revel_db_path)
        except Exception as e:
            raise RuntimeError(f"Error applying REVEL algorithm: {e}")

        try:
            result_data_revel.to_csv(destination_path, index=False)
        except OSError as e:
            raise RuntimeError(f"Error saving file: {e}")

        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"REVEL algorithm was successfully applied to '{relative_path}'.",
            },
            uuid,
            sid,
        )

        socketio_emit_to_user_session(
            WORKSPACE_UPDATE_FEEDBACK_EVENT,
            {"status": "updated"},
            uuid,
            sid,
        )

    except FileNotFoundError as e:
        logger.error(
            "FileNotFoundError: %s while applying REVEL algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"FileNotFoundError: {e} while applying REVEL algorithm" + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Requested file not found"}), 404
    except PermissionError as e:
        logger.error(
            "PermissionError: %s while applying REVEL algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"PermissionError: {e} while applying REVEL algorithm" + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Permission denied"}), 403
    except UnexpectedError as e:
        logger.error(
            "UnexpectedError: %s while applying REVEL algorithm %s",
            e.message,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"UnexpectedError: {e.message} while applying REVEL algorithm" + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500
    except Exception as e:
        logger.error(
            "UnexpectedError: %s while applying REVEL algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"UnexpectedError: {e} while applying REVEL algorithm" + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500

    return jsonify({"message": "REVEL algorithm was successfully applied"}), 200
