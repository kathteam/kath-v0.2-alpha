"""
Workspace file operations module.

This module provides core file operation functionality for the workspace.
It handles common file system operations like ensuring workspace exists,
checking file permissions, and managing file paths.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Union

# Import constants from constants module
from ..constants import WORKSPACE_DIR, WORKSPACE_TEMPLATE_DIR
from ..utils.exceptions import UnexpectedError


class WorkspaceFileOperations:
    """Handle core file operations in the workspace."""

    @staticmethod
    def ensure_user_workspace_exists(uuid: str) -> str:
        """
        Ensure the user's workspace directory exists, creating it if necessary.

        Args:
            uuid (str): User's unique identifier.

        Returns:
            str: Path to the user's workspace directory.

        Raises:
            PermissionError: If unable to create workspace directory.
            UnexpectedError: If an unexpected error occurs.
        """
        user_workspace_dir = os.path.join(WORKSPACE_DIR, uuid)

        try:
            if not os.path.exists(user_workspace_dir):
                # Copy template directory to user workspace
                shutil.copytree(WORKSPACE_TEMPLATE_DIR, user_workspace_dir)
            return user_workspace_dir

        except PermissionError as e:
            raise PermissionError(f"Unable to create workspace directory: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error ensuring workspace exists: {str(e)}")

    @staticmethod
    def get_workspace_path(uuid: str, relative_path: Optional[str] = None) -> str:
        """
        Get the absolute path for a file/directory in the user's workspace.

        Args:
            uuid (str): User's unique identifier.
            relative_path (str, optional): Relative path within workspace.

        Returns:
            str: Absolute path in the workspace.
        """
        workspace_dir = os.path.join(WORKSPACE_DIR, uuid)
        if relative_path:
            return os.path.join(workspace_dir, relative_path)
        return workspace_dir

    @staticmethod
    def ensure_parent_dir_exists(file_path: str) -> None:
        """
        Ensure the parent directory of a file path exists.

        Args:
            file_path (str): Path to the file.

        Raises:
            PermissionError: If unable to create directory.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Unable to create directory: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error creating directory: {str(e)}")

    @staticmethod
    def create_file(path: str) -> None:
        """
        Create an empty file at the specified path.

        Args:
            path (str): Path where the file should be created.

        Raises:
            PermissionError: If unable to create file.
            FileExistsError: If file already exists.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            WorkspaceFileOperations.ensure_parent_dir_exists(path)
            with open(path, "w", encoding="utf-8") as _:
                pass
        except PermissionError as e:
            raise PermissionError(f"Unable to create file: {str(e)}")
        except FileExistsError as e:
            raise FileExistsError(f"File already exists: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error creating file: {str(e)}")

    @staticmethod
    def create_directory(path: str) -> None:
        """
        Create a directory at the specified path.

        Args:
            path (str): Path where the directory should be created.

        Raises:
            PermissionError: If unable to create directory.
            FileExistsError: If directory already exists.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            os.mkdir(path)
        except PermissionError as e:
            raise PermissionError(f"Unable to create directory: {str(e)}")
        except FileExistsError as e:
            raise FileExistsError(f"Directory already exists: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error creating directory: {str(e)}")

    @staticmethod
    def rename_item(old_path: str, new_path: str) -> None:
        """
        Rename a file or directory.

        Args:
            old_path (str): Current path of the item.
            new_path (str): New path for the item.

        Raises:
            FileNotFoundError: If source doesn't exist.
            PermissionError: If unable to rename.
            FileExistsError: If destination already exists.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            os.rename(old_path, new_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Source not found: {str(e)}")
        except PermissionError as e:
            raise PermissionError(f"Unable to rename: {str(e)}")
        except FileExistsError as e:
            raise FileExistsError(f"Destination already exists: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error renaming: {str(e)}")

    @staticmethod
    def delete_item(path: str, is_directory: bool = False) -> None:
        """
        Delete a file or directory.

        Args:
            path (str): Path to the item to delete.
            is_directory (bool): Whether the item is a directory.

        Raises:
            FileNotFoundError: If item doesn't exist.
            PermissionError: If unable to delete.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            if is_directory:
                shutil.rmtree(path)
            else:
                os.remove(path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Item not found: {str(e)}")
        except PermissionError as e:
            raise PermissionError(f"Unable to delete: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error deleting: {str(e)}")

    @staticmethod
    def clean_auxiliary_files(base_path: str) -> None:
        """
        Remove auxiliary files associated with a base file.

        Args:
            base_path (str): Path to the base file.

        Raises:
            PermissionError: If unable to delete files.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            base_name = os.path.basename(base_path)
            dir_path = os.path.dirname(base_path)

            # Find auxiliary files (non-CSV/txt files starting with base name)
            aux_files = [
                f
                for f in os.listdir(dir_path)
                if (
                    f.startswith(base_name)
                    and not f.endswith((".csv", ".txt"))
                    and not os.path.isdir(os.path.join(dir_path, f))
                )
            ]

            # Remove each auxiliary file
            for file_name in aux_files:
                os.remove(os.path.join(dir_path, file_name))

        except PermissionError as e:
            raise PermissionError(f"Unable to clean auxiliary files: {str(e)}")
        except Exception as e:
            raise UnexpectedError(f"Unexpected error cleaning auxiliary files: {str(e)}")

    @staticmethod
    def validate_file_access(path: str, check_exists: bool = True) -> None:
        """
        Validate that a file path is accessible.

        Args:
            path (str): Path to validate.
            check_exists (bool): Whether to check if file exists.

        Raises:
            FileNotFoundError: If file doesn't exist and check_exists is True.
            PermissionError: If file isn't accessible.
            UnexpectedError: If an unexpected error occurs.
        """
        try:
            if check_exists and not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

            # Check read/write permissions
            test_path = path if os.path.exists(path) else os.path.dirname(path)
            if not os.access(test_path, os.R_OK | os.W_OK):
                raise PermissionError(f"Insufficient permissions for: {path}")

        except (FileNotFoundError, PermissionError):
            raise
        except Exception as e:
            raise UnexpectedError(f"Unexpected error validating file access: {str(e)}")
