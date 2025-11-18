"""
This module defines additional error types for workspace operations.
"""

from typing import Dict, Optional


class WorkspaceError(Exception):
    """Base exception class for workspace operations."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(WorkspaceError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, details)


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace or workspace template is not found."""

    def __init__(self, workspace_id: str):
        super().__init__(f"Workspace not found: {workspace_id}", {"workspace_id": workspace_id})


class WorkspaceAccessError(WorkspaceError):
    """Raised when there are permission issues with workspace operations."""

    def __init__(self, message: str, path: Optional[str] = None):
        details = {"path": path} if path else {}
        super().__init__(message, details)


class InvalidOperationError(WorkspaceError):
    """Raised when attempting an invalid operation."""

    def __init__(self, message: str, operation: str):
        super().__init__(message, {"operation": operation})


class FileFormatError(WorkspaceError):
    """Raised when there are issues with file format or content."""

    def __init__(self, message: str, file_path: str):
        super().__init__(message, {"file_path": file_path})


class ConcurrencyError(WorkspaceError):
    """Raised when there are concurrency-related issues."""

    def __init__(self, message: str, resource: str):
        super().__init__(message, {"resource": resource})
