"""
This module handles Socket.IO event emissions for workspace feedback.
It provides standardized methods for sending console and workspace feedback events.
"""

from typing import Any, Dict

from flask_socketio import emit

# Event constants
CONSOLE_FEEDBACK_EVENT = "console_feedback"
WORKSPACE_FILE_SAVE_FEEDBACK_EVENT = "workspace_file_save_feedback"
WORKSPACE_UPDATE_FEEDBACK_EVENT = "workspace_update_feedback"


class WorkspaceEvents:
    """Handles Socket.IO event emissions for workspace operations."""

    @staticmethod
    def emit_console_feedback(message: str, feedback_type: str, uuid: str, sid: str) -> None:
        """
        Emit console feedback event to user's session.

        Args:
            message (str): Feedback message.
            feedback_type (str): Type of feedback ("info", "succ", "warn", "errr").
            uuid (str): User's unique identifier.
            sid (str): Session identifier.
        """
        emit(CONSOLE_FEEDBACK_EVENT, {"type": feedback_type, "message": message}, room=sid, namespace="/")

    @staticmethod
    def emit_file_save_feedback(status: str, uuid: str, sid: str) -> None:
        """
        Emit file save feedback event to user's session.

        Args:
            status (str): Save operation status ("success" or "error").
            uuid (str): User's unique identifier.
            sid (str): Session identifier.
        """
        emit(WORKSPACE_FILE_SAVE_FEEDBACK_EVENT, {"status": status}, room=sid, namespace="/")

    @staticmethod
    def emit_workspace_update(uuid: str, sid: str) -> None:
        """
        Emit workspace update event to user's session.

        Args:
            uuid (str): User's unique identifier.
            sid (str): Session identifier.
        """
        emit(WORKSPACE_UPDATE_FEEDBACK_EVENT, {"status": "updated"}, room=sid, namespace="/")

    @staticmethod
    def file_operation_started(operation: str, path: str, uuid: str, sid: str) -> None:
        """
        Emit console feedback for start of file operation.

        Args:
            operation (str): Operation being performed.
            path (str): Path being operated on.
            uuid (str): User's unique identifier.
            sid (str): Session identifier.
        """
        WorkspaceEvents.emit_console_feedback(f"{operation.capitalize()}ing file at '{path}'...", "info", uuid, sid)

    @staticmethod
    def file_operation_completed(operation: str, path: str, uuid: str, sid: str) -> None:
        """
        Emit console feedback for completion of file operation.

        Args:
            operation (str): Operation that was performed.
            path (str): Path that was operated on.
            uuid (str): User's unique identifier.
            sid (str): Session identifier.
        """
        past_tense = {
            "create": "created",
            "save": "saved",
            "rename": "renamed",
            "delete": "deleted",
            "retrieve": "retrieved",
        }.get(operation.lower(), f"{operation}ed")

        WorkspaceEvents.emit_console_feedback(f"Successfully {past_tense} '{path}'", "succ", uuid, sid)

    @staticmethod
    def file_operation_error(error: Exception, operation: str, path: str, uuid: str, sid: str) -> None:
        """
        Emit console feedback for file operation error.

        Args:
            error (Exception): The error that occurred.
            operation (str): Operation that failed.
            path (str): Path that was being operated on.
            uuid (str): User's unique identifier.
            sid (str): Session identifier.
        """
        error_type = error.__class__.__name__
        WorkspaceEvents.emit_console_feedback(
            f"{error_type}: {str(error)} while {operation}ing {path}", "errr", uuid, sid
        )
