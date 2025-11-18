"""
Unit Tests for Phase 2 Delta-Sync Module

Comprehensive unit tests for delta-sync detection, version checking,
freshness window evaluation, and sync status reporting.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.delta_sync import DeltaSyncManager, DeltaSyncStatus
from src.models.base import Base
from src.models.source_variant import SourceVariant


@pytest.fixture
def db_session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sync_manager(db_session):
    """Create DeltaSyncManager instance."""
    return DeltaSyncManager(session=db_session)


class TestDeltaSyncManagerInitialization:
    """Test DeltaSyncManager initialization."""

    def test_initialization_with_session(self, db_session):
        """Test manager initializes with provided session."""
        manager = DeltaSyncManager(session=db_session)
        assert manager.session is not None
        assert manager.session == db_session

    def test_initialization_without_session(self, db_session, mocker):
        """Test manager initializes without session (uses default)."""
        # Mock get_db_session to return our test db_session
        mocker.patch('src.data.delta_sync.get_db_session', return_value=db_session)
        # Should not raise exception
        manager = DeltaSyncManager(session=None)
        assert manager.session is not None

    def test_source_versions_configured(self, sync_manager):
        """Test that source versions are properly configured."""
        assert "clinvar" in sync_manager.SOURCE_VERSIONS
        assert "lovd" in sync_manager.SOURCE_VERSIONS
        assert "gnomad" in sync_manager.SOURCE_VERSIONS
        assert isinstance(sync_manager.SOURCE_VERSIONS["clinvar"], str)

    def test_freshness_windows_configured(self, sync_manager):
        """Test that freshness windows are properly configured."""
        assert "clinvar" in sync_manager.FRESHNESS_WINDOW
        assert "lovd" in sync_manager.FRESHNESS_WINDOW
        assert "gnomad" in sync_manager.FRESHNESS_WINDOW
        assert isinstance(sync_manager.FRESHNESS_WINDOW["clinvar"], int)
        assert sync_manager.FRESHNESS_WINDOW["clinvar"] > 0


class TestSyncStatusDetection:
    """Test sync status detection logic."""

    def test_check_sync_status_no_existing_data(self, sync_manager):
        """Test sync status when no data exists."""
        status = sync_manager.check_sync_status(
            workspace_id="test-workspace",
            file_id=1,
            source_database="clinvar"
        )

        assert status.has_existing_data is False
        assert status.record_count == 0
        assert status.requires_full_sync is True
        assert status.version_mismatch is False

    def test_check_sync_status_with_existing_data(self, sync_manager, db_session):
        """Test sync status with existing data."""
        # Add test data
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({"clinvar_id": 12345}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        status = sync_manager.check_sync_status(
            workspace_id="test-workspace",
            file_id=1,
            source_database="clinvar"
        )

        assert status.has_existing_data is True
        assert status.record_count > 0

    def test_check_sync_status_version_mismatch(self, sync_manager, db_session):
        """Test version mismatch detection."""
        # Add variant with old version
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2023.01"
        )
        db_session.add(variant)
        db_session.commit()

        status = sync_manager.check_sync_status(
            workspace_id="test-workspace",
            file_id=1,
            source_database="clinvar",
            current_version="2024.01"
        )

        assert status.version_mismatch is True
        assert status.requires_full_sync is True

    def test_check_sync_status_version_match(self, sync_manager, db_session):
        """Test version match (no re-sync needed)."""
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow() - timedelta(hours=12),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        status = sync_manager.check_sync_status(
            workspace_id="test-workspace",
            file_id=1,
            source_database="clinvar",
            current_version="2024.01"
        )

        assert status.version_mismatch is False


class TestDownloadDecision:
    """Test download decision logic."""

    def test_should_download_no_data(self, sync_manager):
        """Test download is needed when no data exists."""
        result = sync_manager.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        )
        assert result is True

    def test_should_download_force_refresh(self, sync_manager, db_session):
        """Test download with force_refresh=True."""
        # Add recent data
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        result = sync_manager.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar",
            force_refresh=True
        )
        assert result is True

    def test_should_download_stale_data(self, sync_manager, db_session):
        """Test download is needed when data is stale."""
        # Add very old data
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow() - timedelta(days=100),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        result = sync_manager.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        )
        assert result is True

    def test_should_not_download_fresh_data(self, sync_manager, db_session):
        """Test download is not needed when data is fresh."""
        # Add fresh data
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow() - timedelta(hours=12),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        result = sync_manager.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        )
        assert result is False


class TestDeltaSyncStatus:
    """Test DeltaSyncStatus data structure."""

    def test_sync_status_creation(self):
        """Test DeltaSyncStatus object creation."""
        status = DeltaSyncStatus(
            has_existing_data=True,
            record_count=100,
            requires_full_sync=False,
            version_mismatch=False,
            last_import_timestamp=datetime.utcnow()
        )

        assert status.has_existing_data is True
        assert status.record_count == 100
        assert status.requires_full_sync is False
        assert status.version_mismatch is False

    def test_sync_status_to_dict(self):
        """Test DeltaSyncStatus serialization."""
        timestamp = datetime.utcnow()
        status = DeltaSyncStatus(
            has_existing_data=True,
            record_count=100,
            requires_full_sync=False,
            version_mismatch=False,
            last_import_timestamp=timestamp
        )

        status_dict = status.to_dict()
        assert status_dict["has_existing_data"] is True
        assert status_dict["record_count"] == 100
        assert "last_import_timestamp" in status_dict


class TestFreshnessWindows:
    """Test freshness window evaluation."""

    def test_freshness_window_clinvar(self, sync_manager):
        """Test ClinVar freshness window (24 hours)."""
        window_hours = sync_manager.FRESHNESS_WINDOW["clinvar"]
        assert window_hours == 24

    def test_freshness_window_lovd(self, sync_manager):
        """Test LOVD freshness window (1 week)."""
        window_hours = sync_manager.FRESHNESS_WINDOW["lovd"]
        assert window_hours == 168  # 7 days * 24 hours

    def test_freshness_window_gnomad(self, sync_manager):
        """Test gnomAD freshness window (1 month)."""
        window_hours = sync_manager.FRESHNESS_WINDOW["gnomad"]
        assert window_hours == 720  # 30 days * 24 hours

    def test_data_freshness_calculation(self, sync_manager, db_session):
        """Test data freshness is calculated correctly."""
        # Add variant imported 12 hours ago
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow() - timedelta(hours=12),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        status = sync_manager.check_sync_status(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        )

        # ClinVar window is 24 hours, so 12-hour-old data should still be fresh
        assert status.requires_full_sync is False


class TestMultipleSourceHandling:
    """Test handling of multiple data sources."""

    def test_check_sync_status_different_sources(self, sync_manager, db_session):
        """Test sync status for different sources independently."""
        # Add ClinVar variant
        clinvar_variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(clinvar_variant)
        db_session.commit()

        # Check ClinVar status
        clinvar_status = sync_manager.check_sync_status(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        )
        assert clinvar_status.has_existing_data is True

        # Check LOVD status (no data)
        lovd_status = sync_manager.check_sync_status(
            workspace_id="test",
            file_id=1,
            source_database="lovd"
        )
        assert lovd_status.has_existing_data is False


class TestErrorHandling:
    """Test error handling in delta-sync."""

    def test_invalid_source_database(self, sync_manager):
        """Test handling of invalid source database."""
        # Should not raise exception, just return appropriate status
        status = sync_manager.check_sync_status(
            workspace_id="test",
            file_id=1,
            source_database="invalid_source"
        )
        # Status should still be returned even for unknown source
        assert status is not None

    def test_null_workspace_id(self, sync_manager):
        """Test handling of null workspace ID."""
        # Should handle gracefully
        status = sync_manager.check_sync_status(
            workspace_id=None,
            file_id=1,
            source_database="clinvar"
        )
        assert status is not None

    def test_zero_file_id(self, sync_manager):
        """Test handling of zero/invalid file ID."""
        status = sync_manager.check_sync_status(
            workspace_id="test",
            file_id=0,
            source_database="clinvar"
        )
        assert status.has_existing_data is False


class TestBandwidthOptimization:
    """Test bandwidth optimization aspects."""

    def test_sync_reduces_redundant_downloads(self, sync_manager, db_session):
        """Test that sync status correctly identifies when download can be skipped."""
        # First import
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        # Second check - should not need download
        should_download = sync_manager.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        )

        assert should_download is False  # No need for re-download within freshness window

    def test_version_change_triggers_download(self, sync_manager, db_session):
        """Test that version change triggers new download."""
        # Import with version 2024.01
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        # Check if new version should be downloaded
        status = sync_manager.check_sync_status(
            workspace_id="test",
            file_id=1,
            source_database="clinvar",
            current_version="2025.01"
        )

        assert status.version_mismatch is True
        assert status.requires_full_sync is True
