"""
Workspace apply route module.
This module defines routes for applying algorithms to files and saving the results to the user's
workspace.
"""

# pylint: disable=broad-exception-caught

import os
import pandas as pd
from flask import Blueprint, request, jsonify

from ..setup.extensions import logger
from ..utils.helpers import socketio_emit_to_user_session
from ..utils.exceptions import UnexpectedError
from ..constants import (
    WORKSPACE_APPLY_ROUTE,
    WORKSPACE_DIR,
    CONSOLE_FEEDBACK_EVENT,
    WORKSPACE_UPDATE_FEEDBACK_EVENT,
)

from ..tools import (
    add_spliceai_eval_columns,
    cadd_pipeline,
    main_revel_pipeline,
)

workspace_apply_route_bp = Blueprint("workspace_apply_route", __name__)


@workspace_apply_route_bp.route(
    f"{WORKSPACE_APPLY_ROUTE}/spliceai/<path:relative_path>", methods=["GET"]
)
def get_workspace_apply_spliceai(relative_path):
    """
    Route to apply the SpliceAI algorithm to a file and save the result to the workspace.
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
    #     - The path to the file to which the SpliceAI algorithm should be applied
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
                "message": f"Applying SpliceAI algorithm to '{relative_path}' with "
                + f"override: '{override}'...",
            },
            uuid,
            sid,
        )

        #
        # TODO: Implement SpliceAI algorithm apply and save logic using defined parameters
        # [destination_path, override, apply_to]
        #
        existing_data = pd.DataFrame()
        if os.path.exists(destination_path):
            if override:
                os.remove(destination_path)
            else:
                existing_data = pd.read_csv(destination_path)

        fasta_path = os.path.join(WORKSPACE_DIR,"fasta", "hg38.fa")
        spliceai_dir = os.path.join(WORKSPACE_DIR, uuid, "spliceai")
        os.makedirs(spliceai_dir, exist_ok=True)
        try:
            result_data_spliceai = add_spliceai_eval_columns(pd.read_csv(apply_to,low_memory=False),
                                                              fasta_path,
                                                              spliceai_dir)
        except Exception as e:
            raise RuntimeError(f"Error applying SpliceAI algorithm: {e}")

        if not existing_data.empty:
            result_data_spliceai = pd.concat([existing_data, result_data_spliceai], ignore_index=True)

        try:
            result_data_spliceai.to_csv(destination_path, index=False)
        except OSError as e:
            raise RuntimeError(f"Error saving file: {e}")

        # Emit a feedback to the user's console
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

    except FileNotFoundError as e:
        logger.error(
            "FileNotFoundError: %s while applying SpliceAI algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"FileNotFoundError: {e} while applying SpliceAI algorithm"
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Requested file not found"}), 404
    except PermissionError as e:
        logger.error(
            "PermissionError: %s while applying SpliceAI algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"PermissionError: {e} while applying SpliceAI algorithm"
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Permission denied"}), 403
    except UnexpectedError as e:
        logger.error(
            "UnexpectedError: %s while applying SpliceAI algorithm %s",
            e.message,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"UnexpectedError: {e.message} while applying SpliceAI algorithm"
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500
    except Exception as e:
        logger.error(
            "UnexpectedError: %s while applying SpliceAI algorithm %s",
            e,
            destination_path,
        )
        # Emit a feedback to the user's console
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "errr",
                "message": f"UnexpectedError: {e} while applying SpliceAI algorithm"
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500

    return jsonify({"message": "SpliceAI algorithm was successfully applied"}), 200


@workspace_apply_route_bp.route(
    f"{WORKSPACE_APPLY_ROUTE}/cadd/<path:relative_path>", methods=["GET"]
)
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
                "message": f"Applying CADD algorithm to '{relative_path}' with "
                + f"override: '{override}'...",
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
            result_data_cadd = cadd_pipeline((pd.read_csv(apply_to,low_memory=False)).convert_dtypes(),
                                             cadd_dir)
        except Exception as e:
            raise RuntimeError(f"Error applying CADD algorithm: {e}")

        if not existing_data.empty:
            result_data_cadd = pd.concat([existing_data, result_data_cadd], ignore_index=True)

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
                "message": f"FileNotFoundError: {e} while applying CADD algorithm "
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "Requested file not found"}), 404
    except PermissionError as e:
        logger.error(
            "PermissionError: %s while applying CADD algorithm %s", e, destination_path
        )
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
                "message": f"UnexpectedError: {e.message} while applying CADD algorithm "
                + f"{destination_path}",
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
                "message": f"UnexpectedError: {e} while applying CADD algorithm "
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500

    return jsonify({"message": "CADD algorithm was successfully applied"}), 200


# TODO - Implement the route to apply the REVEL algorithm to a file and save the result to the workspace. Currently, Idk why it does not work.
@workspace_apply_route_bp.route(
    f"{WORKSPACE_APPLY_ROUTE}/revel/<path:relative_path>", methods=["GET"]
)
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
                "message": f"Applying REVEL algorithm to '{relative_path}' with "
                + f"override: '{override}'...",
            },
            uuid,
            sid,
        )
        try:
            result_data_revel = main_revel_pipeline(dataset_path = apply_to, revel_db_path = revel_db_path)
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
                "message": f"FileNotFoundError: {e} while applying REVEL algorithm"
                + f"{destination_path}",
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
                "message": f"PermissionError: {e} while applying REVEL algorithm"
                + f"{destination_path}",
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
                "message": f"UnexpectedError: {e.message} while applying REVEL algorithm"
                + f"{destination_path}",
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
                "message": f"UnexpectedError: {e} while applying REVEL algorithm"
                + f"{destination_path}",
            },
            uuid,
            sid,
        )
        return jsonify({"error": "An internal error occurred"}), 500

    return jsonify({"message": "REVEL algorithm was successfully applied"}), 200
