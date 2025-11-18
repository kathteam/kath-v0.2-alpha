#!/usr/bin/env python3
"""
CSV to Database Migration Script

Migrates existing CSV files from src/workspace/ to SQLite database.

Usage:
    python scripts/migrate_csv_to_database.py [--workspace-dir PATH] [--dry-run]

Options:
    --workspace-dir PATH    Path to workspace directory (default: src/workspace)
    --dry-run              Show what would be migrated without making changes
    --verbose              Show detailed progress information
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask

from src.database import AggregationRepository, FileRepository, VariantRepository, WorkspaceRepository, init_db
from src.settings import get_settings


class CSVMigrator:
    """Handles migration of CSV files to database."""

    def __init__(self, workspace_dir: str, dry_run: bool = False, verbose: bool = False):
        """
        Initialize migrator.

        Args:
            workspace_dir: Path to workspace directory
            dry_run: If True, show what would be done without making changes
            verbose: If True, show detailed progress
        """
        self.workspace_dir = Path(workspace_dir)
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            "workspaces": 0,
            "files": 0,
            "folders": 0,
            "variants": 0,
            "skipped": 0,
            "errors": 0,
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose."""
        if self.verbose or level == "ERROR":
            print(f"[{level}] {message}")

    def scan_workspace_structure(self) -> Dict[str, List[Dict]]:
        """
        Scan workspace directory structure.

        Returns:
            Dict mapping workspace_id to list of file/folder dicts
        """
        structure = {}

        if not self.workspace_dir.exists():
            self.log(f"Workspace directory not found: {self.workspace_dir}", "ERROR")
            return structure

        # Each subdirectory is a workspace (UUID)
        for workspace_path in self.workspace_dir.iterdir():
            if not workspace_path.is_dir() or workspace_path.name.startswith("."):
                continue

            workspace_id = workspace_path.name
            structure[workspace_id] = []

            # Walk the workspace directory
            for root, dirs, files in os.walk(workspace_path):
                rel_root = Path(root).relative_to(workspace_path)

                # Add directories
                for dir_name in dirs:
                    if dir_name.startswith("."):
                        continue

                    rel_path = str(rel_root / dir_name) if str(rel_root) != "." else dir_name

                    structure[workspace_id].append(
                        {
                            "type": "folder",
                            "name": dir_name,
                            "path": rel_path,
                            "full_path": Path(root) / dir_name,
                        }
                    )

                # Add CSV files
                for file_name in files:
                    if not file_name.endswith(".csv") or file_name.startswith("."):
                        continue

                    rel_path = str(rel_root / file_name) if str(rel_root) != "." else file_name
                    full_path = Path(root) / file_name

                    structure[workspace_id].append(
                        {
                            "type": "file",
                            "name": file_name,
                            "path": rel_path,
                            "full_path": full_path,
                        }
                    )

        return structure

    def extract_csv_metadata(self, csv_path: Path) -> Optional[Dict]:
        """
        Extract metadata from CSV file without loading full data.

        Args:
            csv_path: Path to CSV file

        Returns:
            Metadata dict or None if error
        """
        try:
            # Read only first few rows to get headers and estimate structure
            df = pd.read_csv(csv_path, nrows=5)

            metadata = {
                "header": list(df.columns),
                "column_count": len(df.columns),
                "data_source": self.detect_data_source(df.columns),
            }

            # Get actual row count
            with open(csv_path, "r") as f:
                row_count = sum(1 for _ in f) - 1  # Subtract header

            metadata["row_count"] = row_count

            return metadata

        except Exception as e:
            self.log(f"Error reading CSV {csv_path}: {e}", "ERROR")
            return None

    def detect_data_source(self, columns: pd.Index) -> str:
        """
        Detect data source based on column names.

        Args:
            columns: DataFrame columns

        Returns:
            Data source identifier
        """
        col_str = "|".join([str(c).lower() for c in columns])

        if "gnomad" in col_str:
            return "gnomAD"
        elif "clinvar" in col_str:
            return "ClinVar"
        elif "lovd" in col_str:
            return "LOVD"
        else:
            return "Custom"

    def migrate_workspace(self, workspace_id: str, items: List[Dict]) -> bool:
        """
        Migrate a single workspace.

        Args:
            workspace_id: Workspace UUID
            items: List of files/folders in workspace

        Returns:
            True if successful
        """
        self.log(f"\nMigrating workspace: {workspace_id}")

        if self.dry_run:
            self.log(f"  [DRY RUN] Would create workspace: {workspace_id}")
            self.stats["workspaces"] += 1
        else:
            # Create workspace
            workspace_repo = WorkspaceRepository()
            workspace = workspace_repo.get_or_create(uuid=workspace_id, name=workspace_id)
            self.stats["workspaces"] += 1
            self.log(f"  Created workspace: {workspace.id}")

        # Migrate folders first, then files
        folders = [item for item in items if item["type"] == "folder"]
        files = [item for item in items if item["type"] == "file"]

        # Migrate folders
        for folder in folders:
            self.migrate_folder(workspace_id, folder)

        # Migrate files
        for file_item in tqdm(files, desc=f"  Files in {workspace_id}", disable=not self.verbose):
            self.migrate_file(workspace_id, file_item)

        return True

    def migrate_folder(self, workspace_id: str, folder: Dict) -> bool:
        """
        Migrate a folder record.

        Args:
            workspace_id: Workspace UUID
            folder: Folder metadata dict

        Returns:
            True if successful
        """
        if self.dry_run:
            self.log(f"  [DRY RUN] Would create folder: {folder['path']}")
            self.stats["folders"] += 1
            return True

        try:
            file_repo = FileRepository()
            file_repo.get_or_create(
                workspace_id=workspace_id, name=folder["name"], path=folder["path"], file_type="folder"
            )
            self.stats["folders"] += 1
            return True
        except Exception as e:
            self.log(f"Error creating folder {folder['path']}: {e}", "ERROR")
            self.stats["errors"] += 1
            return False

    def migrate_file(self, workspace_id: str, file_item: Dict) -> bool:
        """
        Migrate a CSV file and its variant data.

        Args:
            workspace_id: Workspace UUID
            file_item: File metadata dict

        Returns:
            True if successful
        """
        csv_path = file_item["full_path"]

        # Extract metadata
        metadata = self.extract_csv_metadata(csv_path)
        if not metadata:
            self.stats["skipped"] += 1
            return False

        if self.dry_run:
            self.log(
                f"  [DRY RUN] Would migrate: {file_item['path']} "
                f"({metadata['row_count']} rows, {metadata['column_count']} cols)"
            )
            self.stats["files"] += 1
            self.stats["variants"] += metadata["row_count"]
            return True

        try:
            # Create file record
            file_repo = FileRepository()
            file_obj = file_repo.get_or_create(
                workspace_id=workspace_id,
                name=file_item["name"],
                path=file_item["path"],
                file_type="file",
                row_count=metadata["row_count"],
                column_count=metadata["column_count"],
                data_source=metadata["data_source"],
                header_json=json.dumps(metadata["header"]),
            )

            self.stats["files"] += 1

            # Migrate variant data in chunks
            chunk_size = 1000
            variant_repo = VariantRepository()

            for chunk_idx, chunk_df in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
                variants = self.dataframe_to_variants(chunk_df, file_obj.id, chunk_idx * chunk_size)
                variant_repo.create_bulk(variants)
                self.stats["variants"] += len(variants)

            self.log(f"  Migrated: {file_item['path']} ({metadata['row_count']} variants)")
            return True

        except Exception as e:
            self.log(f"Error migrating file {file_item['path']}: {e}", "ERROR")
            self.stats["errors"] += 1
            return False

    def dataframe_to_variants(self, df: pd.DataFrame, file_id: int, row_offset: int) -> List[Dict]:
        """
        Convert DataFrame to variant dicts for bulk insert.

        Args:
            df: DataFrame chunk
            file_id: File ID
            row_offset: Starting row index for this chunk

        Returns:
            List of variant dicts
        """
        variants = []

        # Define core variant columns
        core_columns = [
            "chromosome",
            "position",
            "ref_allele",
            "alt_allele",
            "variant_id",
            "gen_pos",
            "gene",
            "transcript",
            "consequence",
        ]

        for idx, row in df.iterrows():
            variant = {"file_id": file_id, "row_index": row_offset + idx}

            # Extract core columns
            for col in core_columns:
                if col in df.columns:
                    value = row[col]
                    # Handle NaN values
                    variant[col] = None if pd.isna(value) else value

            # Store remaining columns in data_json
            other_data = {}
            for col in df.columns:
                if col not in core_columns:
                    value = row[col]
                    if not pd.isna(value):
                        other_data[col] = value

            if other_data:
                variant["data_json"] = json.dumps(other_data)

            variants.append(variant)

        return variants

    def verify_migration(self) -> Dict:
        """
        Verify migration integrity.

        Returns:
            Dict with verification results
        """
        self.log("\nVerifying migration...")

        results = {"passed": True, "checks": []}

        if self.dry_run:
            results["checks"].append({"name": "Dry run mode", "status": "skipped"})
            return results

        try:
            workspace_repo = WorkspaceRepository()
            file_repo = FileRepository()
            variant_repo = VariantRepository()

            # Check workspace count
            workspace_count = workspace_repo.count()
            results["checks"].append(
                {
                    "name": "Workspace count",
                    "expected": self.stats["workspaces"],
                    "actual": workspace_count,
                    "status": "passed" if workspace_count == self.stats["workspaces"] else "failed",
                }
            )

            # Check file count (files + folders)
            total_files = self.stats["files"] + self.stats["folders"]
            file_count = file_repo.count()
            results["checks"].append(
                {
                    "name": "File/folder count",
                    "expected": total_files,
                    "actual": file_count,
                    "status": "passed" if file_count == total_files else "failed",
                }
            )

            # Check variant count
            variant_count = variant_repo.count()
            results["checks"].append(
                {
                    "name": "Variant count",
                    "expected": self.stats["variants"],
                    "actual": variant_count,
                    "status": "passed" if variant_count == self.stats["variants"] else "failed",
                }
            )

            # Spot check: verify first file has correct row count
            files = file_repo.find_all(limit=1)
            if files:
                file = files[0]
                db_variant_count = variant_repo.count_by_file(file.id)
                results["checks"].append(
                    {
                        "name": f"Spot check file '{file.name}' row count",
                        "expected": file.row_count,
                        "actual": db_variant_count,
                        "status": "passed" if db_variant_count == file.row_count else "failed",
                    }
                )

            # Update overall status
            results["passed"] = all(
                check["status"] == "passed" for check in results["checks"] if check["status"] != "skipped"
            )

        except Exception as e:
            results["passed"] = False
            results["error"] = str(e)

        return results

    def run(self) -> bool:
        """
        Run the migration.

        Returns:
            True if successful
        """
        print(f"\n{'='*60}")
        print(f"CSV to Database Migration")
        print(f"{'='*60}")
        print(f"Workspace directory: {self.workspace_dir}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        print(f"{'='*60}\n")

        # Scan workspace structure
        self.log("Scanning workspace directory...")
        structure = self.scan_workspace_structure()

        if not structure:
            print("No workspaces found to migrate.")
            return True

        print(f"Found {len(structure)} workspace(s)\n")

        # Migrate each workspace
        for workspace_id, items in structure.items():
            self.migrate_workspace(workspace_id, items)

        # Print statistics
        print(f"\n{'='*60}")
        print(f"Migration Statistics")
        print(f"{'='*60}")
        print(f"Workspaces: {self.stats['workspaces']}")
        print(f"Files:      {self.stats['files']}")
        print(f"Folders:    {self.stats['folders']}")
        print(f"Variants:   {self.stats['variants']:,}")
        print(f"Skipped:    {self.stats['skipped']}")
        print(f"Errors:     {self.stats['errors']}")
        print(f"{'='*60}\n")

        # Verify migration
        if not self.dry_run:
            verification = self.verify_migration()

            print(f"\n{'='*60}")
            print(f"Verification Results")
            print(f"{'='*60}")

            for check in verification["checks"]:
                status_symbol = "" if check["status"] == "passed" else ("" if check["status"] == "skipped" else "")
                print(f"{status_symbol} {check['name']}: ", end="")
                if "expected" in check:
                    print(f"Expected {check['expected']}, Got {check['actual']}")
                else:
                    print(check["status"])

            print(f"{'='*60}")
            print(f"Overall: {'PASSED ' if verification['passed'] else 'FAILED '}")
            print(f"{'='*60}\n")

            return verification["passed"]

        return self.stats["errors"] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate CSV files to database")
    parser.add_argument(
        "--workspace-dir", default="src/workspace", help="Path to workspace directory (default: src/workspace)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress information")

    args = parser.parse_args()

    # Create Flask app for database context
    app = Flask(__name__)
    init_db(app, create_tables=True)

    # Run migration within app context
    with app.app_context():
        migrator = CSVMigrator(workspace_dir=args.workspace_dir, dry_run=args.dry_run, verbose=args.verbose)

        success = migrator.run()

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
