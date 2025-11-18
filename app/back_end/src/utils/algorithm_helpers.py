"""Helper functions for processing algorithm application requests."""

import os
from typing import Any, Callable, Dict, Optional, Tuple

import pandas as pd
from flask import jsonify

from ..constants import CONSOLE_FEEDBACK_EVENT, WORKSPACE_DIR, WORKSPACE_UPDATE_FEEDBACK_EVENT
from ..setup.extensions import env
from ..utils.helpers import socketio_emit_to_user_session


def validate_request_headers(request) -> Optional[Tuple[Dict, int]]:
    """Validate request headers for workspace apply routes.

    Returns:
        Tuple of (response, status_code) if validation fails, otherwise None
    """
    if "uuid" not in request.headers or "sid" not in request.headers:
        return jsonify({"error": "UUID and SID headers are required"}), 400
    return None


def validate_request_args(request) -> Optional[Tuple[Dict, int]]:
    """Validate request args for workspace apply routes.

    Returns:
        Tuple of (response, status_code) if validation fails, otherwise None
    """
    if "override" not in request.args or "applyTo" not in request.args:
        return jsonify({"error": "'override' and 'applyTo' parameters are required"}), 400
    return None


def setup_file_paths(uuid: str, relative_path: str, applyTo: str) -> Tuple[str, str]:
    """Set up file paths for workspace operations.

    Returns:
        Tuple of (destination_path, apply_to_path)
    """
    destination_path = os.path.join(WORKSPACE_DIR, uuid, relative_path)
    apply_to = os.path.join(WORKSPACE_DIR, uuid, applyTo)
    return destination_path, apply_to


def handle_existing_data(destination_path: str, override: bool) -> pd.DataFrame:
    """Handle existing data based on override flag.

    Returns:
        Existing DataFrame if not overriding, empty DataFrame if overriding
    """
    existing_data = pd.DataFrame()
    if os.path.exists(destination_path):
        if override:
            os.remove(destination_path)
        else:
            existing_data = pd.read_csv(destination_path)
    return existing_data


def process_algorithm_pipeline(
    algorithm_name: str,
    algorithm_func: Callable,
    apply_to: str,
    relative_path: str,
    uuid: str,
    sid: str,
    additional_args: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Process an algorithm pipeline and handle results.

    Args:
        algorithm_name (str): Name of the algorithm for messaging
        algorithm_func (callable): Function that implements the algorithm
        apply_to (str): Path to input file
        relative_path (str): Relative path for response
        uuid (str): User ID for feedback
        sid (str): Session ID for feedback
        additional_args (dict): Additional arguments for the algorithm function

    Returns:
        Dict containing algorithm results
    """
    # Emit start feedback
    socketio_emit_to_user_session(
        CONSOLE_FEEDBACK_EVENT,
        {
            "type": "info",
            "message": f"Applying {algorithm_name} algorithm to '{relative_path}'...",
        },
        uuid,
        sid,
    )

    try:
        data_copy = pd.read_csv(apply_to).convert_dtypes()[: env.get_max_entries()]
        if additional_args:
            result_data = algorithm_func(data_copy, **additional_args)
        else:
            result_data = algorithm_func(data_copy)
    except Exception as e:
        raise RuntimeError(f"Error applying {algorithm_name} algorithm: {e}")

    return result_data


def save_algorithm_results(
    destination_path: str,
    result_data: pd.DataFrame,
    existing_data: Optional[pd.DataFrame] = None,
) -> None:
    """Save algorithm results to file, optionally merging with existing data.

    Args:
        destination_path (str): Path to save results to
        result_data (pd.DataFrame): Results to save
        existing_data (pd.DataFrame): Existing data to merge with if any
    """
    try:
        if existing_data is not None and not existing_data.empty:
            result_data = pd.concat([existing_data, result_data], ignore_index=True)
        result_data = result_data.convert_dtypes()
        result_data.to_csv(destination_path, index=False)
    except OSError as e:
        raise RuntimeError(f"Error saving file: {e}")
