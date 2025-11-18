"""
Delta-Sync Manager

Handles intelligent data synchronization by detecting existing records and only
downloading new/updated data from external sources. This optimization reduces
bandwidth usage and improves performance when databases already contain data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.database.config import get_db_session
from src.models import File, SourceVariant, Workspace
from src.utils.cache import cached_query

logger = logging.getLogger(__name__)


class DeltaSyncStatus:
    """Data structure representing delta-sync status."""

    def __init__(
        self,
        has_existing_data: bool,
        record_count: int,
        last_import_timestamp: Optional[datetime] = None,
        source_version: Optional[str] = None,
        requires_full_sync: bool = False,
        version_mismatch: bool = False,
    ):
        """
        Initialize delta-sync status.

        Args:
            has_existing_data: Whether database has any records for this source
            record_count: Number of existing records
            last_import_timestamp: Timestamp of latest import
            source_version: Version of source data
            requires_full_sync: Whether full resync is needed (version mismatch, etc.)
            version_mismatch: Whether source version has changed
        """
        self.has_existing_data = has_existing_data
        self.record_count = record_count
        self.last_import_timestamp = last_import_timestamp
        self.source_version = source_version
        self.requires_full_sync = requires_full_sync
        self.version_mismatch = version_mismatch

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "has_existing_data": self.has_existing_data,
            "record_count": self.record_count,
            "last_import_timestamp": self.last_import_timestamp.isoformat() if self.last_import_timestamp else None,
            "source_version": self.source_version,
            "requires_full_sync": self.requires_full_sync,
            "version_mismatch": self.version_mismatch,
        }


class DeltaSyncManager:
    """Manages delta-sync detection and download optimization."""

    # Default version for each source - update when schema changes
    SOURCE_VERSIONS = {
        "clinvar": "2024.01",  # Update when ClinVar format changes
        "lovd": "2024.01",  # Update when LOVD format changes
        "gnomad": "4.0",  # Update when gnomAD version changes
        "custom": "1.0",  # Custom data
    }

    # Time window for considering data "fresh" (in hours)
    FRESHNESS_WINDOW = {
        "clinvar": 24,  # ClinVar updated daily
        "lovd": 168,  # LOVD updated weekly
        "gnomad": 720,  # gnomAD updated monthly
        "custom": 8760,  # Custom data considered fresh for 1 year
    }

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize DeltaSyncManager.

        Args:
            session: SQLAlchemy session. If None, uses get_db_session()
        """
        self.session = session or get_db_session()

    def check_sync_status(
        self,
        workspace_id: str,
        file_id: int,
        source_database: str,
        current_version: Optional[str] = None,
    ) -> DeltaSyncStatus:
        """
        Check sync status for a specific source database.

        Determines if data needs to be re-downloaded or updated based on:
        - Whether existing data exists
        - Source version compatibility
        - Time since last import
        - Record count

        Args:
            workspace_id: Workspace UUID
            file_id: File ID
            source_database: Source database name (clinvar, lovd, gnomad, custom)
            current_version: Current version of source data

        Returns:
            DeltaSyncStatus with sync decision information
        """
        # Get default version if not provided
        if current_version is None:
            current_version = self.SOURCE_VERSIONS.get(source_database, "1.0")

        # Query existing source variants for this file and source
        existing_records = self.session.query(SourceVariant).filter(
            SourceVariant.file_id == file_id,
            SourceVariant.source_database == source_database,
        )

        record_count = existing_records.count()
        has_existing_data = record_count > 0

        if not has_existing_data:
            return DeltaSyncStatus(
                has_existing_data=False,
                record_count=0,
                requires_full_sync=True,
                version_mismatch=False,
            )

        # Get latest import timestamp
        latest_import = self.session.query(SourceVariant.import_timestamp).filter(
            SourceVariant.file_id == file_id,
            SourceVariant.source_database == source_database,
        ).order_by(SourceVariant.import_timestamp.desc()).first()

        latest_import_dt = latest_import[0] if latest_import else None

        # Get stored source version
        stored_version = self.session.query(SourceVariant.source_version).filter(
            SourceVariant.file_id == file_id,
            SourceVariant.source_database == source_database,
        ).first()

        stored_version_str = stored_version[0] if stored_version else None

        # Check if version mismatch requires full resync
        requires_full_sync = stored_version_str != current_version

        if requires_full_sync:
            logger.info(
                "Source version mismatch for %s in file %d: "
                "stored=%s, current=%s. Requiring full resync.",
                source_database,
                file_id,
                stored_version_str,
                current_version,
            )

        # Check freshness window
        is_fresh = False
        if latest_import_dt:
            freshness_hours = self.FRESHNESS_WINDOW.get(source_database, 24)
            time_since_import = datetime.utcnow() - latest_import_dt
            is_fresh = time_since_import < timedelta(hours=freshness_hours)

        return DeltaSyncStatus(
            has_existing_data=True,
            record_count=record_count,
            last_import_timestamp=latest_import_dt,
            source_version=stored_version_str,
            requires_full_sync=requires_full_sync or not is_fresh,
            version_mismatch=requires_full_sync,
        )

    def get_last_import_timestamp(
        self,
        workspace_id: str,
        file_id: int,
        source_database: str,
    ) -> Optional[datetime]:
        """
        Get the timestamp of the last import for a source.

        Args:
            workspace_id: Workspace UUID
            file_id: File ID
            source_database: Source database name

        Returns:
            Timestamp of last import or None if no previous imports
        """
        result = self.session.query(SourceVariant.import_timestamp).filter(
            SourceVariant.file_id == file_id,
            SourceVariant.source_database == source_database,
        ).order_by(SourceVariant.import_timestamp.desc()).first()

        return result[0] if result else None

    def get_sync_status_for_file(
        self,
        workspace_id: str,
        file_id: int,
    ) -> Dict[str, DeltaSyncStatus]:
        """
        Get sync status for all sources in a file.

        Args:
            workspace_id: Workspace UUID
            file_id: File ID

        Returns:
            Dictionary mapping source database name to DeltaSyncStatus
        """
        status_map = {}

        # Check each known source
        for source_db in self.SOURCE_VERSIONS.keys():
            status = self.check_sync_status(workspace_id, file_id, source_db)
            status_map[source_db] = status

        return status_map

    @cached_query(ttl=300)  # Cache for 5 minutes
    def get_importable_genes(
        self,
        source_database: str,
    ) -> List[str]:
        """
        Get list of genes available for import from a source.

        This is cached as it represents static data from the source.

        Args:
            source_database: Source database name

        Returns:
            List of available gene names
        """
        # This would be populated by each source's specific implementation
        # For now, returning common genes as example
        common_genes = {
            "clinvar": ["BRCA1", "BRCA2", "TP53", "KRAS", "MLH1"],
            "lovd": ["BRCA1", "BRCA2", "TP53", "MLH1", "MSH2"],
            "gnomad": [],  # gnomAD is genome-wide, not gene-specific
            "custom": [],  # Custom data varies
        }

        return common_genes.get(source_database, [])

    def should_download(
        self,
        workspace_id: str,
        file_id: int,
        source_database: str,
        current_version: Optional[str] = None,
        force_refresh: bool = False,
    ) -> bool:
        """
        Determine if data should be downloaded for a source.

        Args:
            workspace_id: Workspace UUID
            file_id: File ID
            source_database: Source database name
            current_version: Current version of source data
            force_refresh: Force download even if data exists

        Returns:
            True if download should proceed, False otherwise
        """
        if force_refresh:
            logger.info(
                "Force refresh requested for %s in file %d",
                source_database,
                file_id,
            )
            return True

        status = self.check_sync_status(
            workspace_id,
            file_id,
            source_database,
            current_version,
        )

        if status.requires_full_sync:
            logger.info(
                "Full sync required for %s in file %d (has_existing: %s)",
                source_database,
                file_id,
                status.has_existing_data,
            )
            return True

        logger.info(
            "No download needed for %s in file %d: "
            "has_existing=%s, records=%d",
            source_database,
            file_id,
            status.has_existing_data,
            status.record_count,
        )

        return False

    def update_import_metadata(
        self,
        file_id: int,
        source_database: str,
        record_count: int,
        source_version: str,
    ) -> None:
        """
        Update import metadata after successful download/import.

        This updates the import_timestamp and source_version fields
        for records in this file from this source.

        Args:
            file_id: File ID
            source_database: Source database name
            record_count: Number of records imported
            source_version: Version of source data imported
        """
        now = datetime.utcnow()

        self.session.query(SourceVariant).filter(
            SourceVariant.file_id == file_id,
            SourceVariant.source_database == source_database,
        ).update(
            {
                SourceVariant.import_timestamp: now,
                SourceVariant.source_version: source_version,
            }
        )

        self.session.commit()

        logger.info(
            "Updated import metadata for %s in file %d: "
            "%d records, version %s",
            source_database,
            file_id,
            record_count,
            source_version,
        )

    def get_sync_statistics(
        self,
        workspace_id: str,
    ) -> Dict:
        """
        Get comprehensive sync statistics for a workspace.

        Args:
            workspace_id: Workspace UUID

        Returns:
            Dictionary with sync statistics
        """
        workspace = self.session.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace:
            return {}

        stats = {
            "workspace_id": workspace_id,
            "total_files": len(workspace.files),
            "files_with_source_data": 0,
            "total_source_records": 0,
            "sources_represented": set(),
            "by_source": {},
        }

        for file in workspace.files:
            file_stats = self._get_file_source_statistics(file.id)
            if file_stats["total_records"] > 0:
                stats["files_with_source_data"] += 1
                stats["total_source_records"] += file_stats["total_records"]
                for source, count in file_stats["by_source"].items():
                    stats["sources_represented"].add(source)
                    if source not in stats["by_source"]:
                        stats["by_source"][source] = 0
                    stats["by_source"][source] += count

        # Convert set to list for serialization
        stats["sources_represented"] = sorted(list(stats["sources_represented"]))

        return stats

    def _get_file_source_statistics(self, file_id: int) -> Dict:
        """
        Get source statistics for a specific file.

        Args:
            file_id: File ID

        Returns:
            Dictionary with source statistics
        """
        by_source = {}
        total_records = 0

        for source_db in self.SOURCE_VERSIONS.keys():
            count = self.session.query(SourceVariant).filter(
                SourceVariant.file_id == file_id,
                SourceVariant.source_database == source_db,
            ).count()

            if count > 0:
                by_source[source_db] = count
                total_records += count

        return {
            "file_id": file_id,
            "total_records": total_records,
            "by_source": by_source,
        }

    def mark_download_complete(
        self,
        file_id: int,
        source_database: str,
        imported_record_count: int,
        source_version: str,
    ) -> None:
        """
        Mark a download/import as complete.

        Updates timestamps and version information for tracking.

        Args:
            file_id: File ID
            source_database: Source database name
            imported_record_count: Number of records imported
            source_version: Version of source data
        """
        self.update_import_metadata(
            file_id=file_id,
            source_database=source_database,
            record_count=imported_record_count,
            source_version=source_version,
        )

        logger.info(
            "Marked download complete for %s in file %d: "
            "%d records imported",
            source_database,
            file_id,
            imported_record_count,
        )
