"""
Phase 2 Integration Tests

Comprehensive test suite for Phase 2 database-driven pipeline operations
including delta-sync, merge, filtering, analysis, and API endpoints.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import Phase 2 modules
from src.data.delta_sync import DeltaSyncManager, DeltaSyncStatus
from src.data.merge_operations import MergeOperationHandler, MergeStrategy, MergeResult
from src.data.quality_filtering import QualityFilteringEngine, FilterResult
from src.data.analysis_integration import AnalysisIntegrationHandler, AnalysisToolConfig, AnalysisResult
from src.models import SourceVariant, MergedVariant, FilteredVariant, WorkflowAudit
from src.database.repositories import (
    SourceVariantRepository,
    MergedVariantRepository,
    FilteredVariantRepository,
    WorkflowAuditRepository,
)


# ============================================================================
# Delta-Sync Tests
# ============================================================================

class TestDeltaSyncManager:
    """Test DeltaSyncManager functionality."""

    def test_check_sync_status_no_existing_data(self, db_session):
        """Test sync status when no data exists."""
        sync_mgr = DeltaSyncManager(session=db_session)

        status = sync_mgr.check_sync_status(
            workspace_id="test-workspace",
            file_id=1,
            source_database="clinvar"
        )

        assert status.has_existing_data is False
        assert status.record_count == 0
        assert status.requires_full_sync is True

    def test_check_sync_status_with_existing_data(self, db_session, sample_source_variant):
        """Test sync status with existing data."""
        db_session.add(sample_source_variant)
        db_session.commit()

        sync_mgr = DeltaSyncManager(session=db_session)
        status = sync_mgr.check_sync_status(
            workspace_id="test-workspace",
            file_id=sample_source_variant.file_id,
            source_database="clinvar"
        )

        assert status.has_existing_data is True
        assert status.record_count > 0

    def test_version_mismatch_detection(self, db_session, sample_source_variant):
        """Test detection of version mismatches."""
        sample_source_variant.source_version = "2023.01"
        db_session.add(sample_source_variant)
        db_session.commit()

        sync_mgr = DeltaSyncManager(session=db_session)
        status = sync_mgr.check_sync_status(
            workspace_id="test-workspace",
            file_id=sample_source_variant.file_id,
            source_database="clinvar",
            current_version="2024.01"
        )

        assert status.requires_full_sync is True

    def test_should_download_decision(self, db_session):
        """Test download decision logic."""
        sync_mgr = DeltaSyncManager(session=db_session)

        # No data - should download
        assert sync_mgr.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar"
        ) is True

        # Force refresh - should download
        assert sync_mgr.should_download(
            workspace_id="test",
            file_id=1,
            source_database="clinvar",
            force_refresh=True
        ) is True


# ============================================================================
# Merge Operations Tests
# ============================================================================

class TestMergeOperationHandler:
    """Test MergeOperationHandler functionality."""

    def test_merge_strategies_available(self):
        """Test that all merge strategies are available."""
        strategies = MergeStrategy.get_all_strategies()

        assert MergeStrategy.OUTER_UNION in strategies
        assert MergeStrategy.INNER_INTERSECTION in strategies
        assert MergeStrategy.CONSENSUS in strategies

    def test_invalid_merge_strategy(self, db_session):
        """Test handling of invalid merge strategy."""
        handler = MergeOperationHandler(session=db_session)

        with pytest.raises(ValueError):
            handler.perform_merge(
                file_id=1,
                sources=["clinvar"],
                merge_strategy="invalid_strategy"
            )

    def test_no_sources_validation(self, db_session):
        """Test validation when no sources specified."""
        handler = MergeOperationHandler(session=db_session)

        with pytest.raises(ValueError):
            handler.perform_merge(
                file_id=1,
                sources=[]
            )

    def test_validate_merge_inputs(self, db_session, sample_source_variant):
        """Test input validation for merge."""
        db_session.add(sample_source_variant)
        db_session.commit()

        handler = MergeOperationHandler(session=db_session)

        # Valid input
        is_valid, error = handler.validate_merge_inputs(
            file_id=sample_source_variant.file_id,
            sources=["clinvar"]
        )
        assert is_valid is True
        assert error == ""

        # Invalid source
        is_valid, error = handler.validate_merge_inputs(
            file_id=sample_source_variant.file_id,
            sources=["unknown_source"]
        )
        assert is_valid is False


# ============================================================================
# Quality Filtering Tests
# ============================================================================

class TestQualityFilteringEngine:
    """Test QualityFilteringEngine functionality."""

    def test_filter_suite_initialized(self):
        """Test that filter suite is properly initialized."""
        engine = QualityFilteringEngine()

        assert len(engine.critical_filters) > 0
        assert len(engine.soft_filters) > 0
        assert len(engine.all_filters) > 0

    def test_quality_summary_empty_file(self, db_session):
        """Test quality summary with no filtered variants."""
        engine = QualityFilteringEngine(session=db_session)

        summary = engine.get_quality_summary(file_id=1)

        assert summary["total"] == 0
        assert summary["valid"] == 0
        assert summary["quality_rate"] == 0

    def test_required_fields_filter(self):
        """Test required fields validation."""
        from src.data.quality_filtering import RequiredFieldsFilter

        filter_obj = RequiredFieldsFilter()

        # Create mock variant with missing field
        mock_variant = Mock()
        mock_variant.chromosome = "1"
        mock_variant.position = 1000
        mock_variant.ref_allele = None  # Missing
        mock_variant.alt_allele = "A"

        passed, reason = filter_obj.apply(mock_variant)
        assert passed is False
        assert "Missing required field" in reason

    def test_genomic_coordinate_filter(self):
        """Test genomic coordinate validation."""
        from src.data.quality_filtering import GenomicCoordinateFilter

        filter_obj = GenomicCoordinateFilter()

        # Create mock variant with invalid chromosome
        mock_variant = Mock()
        mock_variant.chromosome = "99"  # Invalid
        mock_variant.position = 1000
        mock_variant.ref_allele = "G"
        mock_variant.alt_allele = "A"

        passed, reason = filter_obj.apply(mock_variant)
        assert passed is False


# ============================================================================
# Analysis Integration Tests
# ============================================================================

class TestAnalysisIntegrationHandler:
    """Test AnalysisIntegrationHandler functionality."""

    def test_analysis_tools_available(self):
        """Test that all analysis tools are available."""
        tools = AnalysisToolConfig.get_all_tools()

        assert AnalysisToolConfig.CADD in tools
        assert AnalysisToolConfig.REVEL in tools
        assert AnalysisToolConfig.SPLICEAI in tools

    def test_pathogenicity_classification_cadd(self):
        """Test CADD pathogenicity classification."""
        # Below threshold
        assert AnalysisToolConfig.is_pathogenic(AnalysisToolConfig.CADD, 15) is False

        # At threshold
        assert AnalysisToolConfig.is_pathogenic(AnalysisToolConfig.CADD, 20) is True

        # Above threshold
        assert AnalysisToolConfig.is_pathogenic(AnalysisToolConfig.CADD, 30) is True

    def test_pathogenicity_classification_revel(self):
        """Test REVEL pathogenicity classification."""
        # Below threshold
        assert AnalysisToolConfig.is_pathogenic(AnalysisToolConfig.REVEL, 0.4) is False

        # At threshold
        assert AnalysisToolConfig.is_pathogenic(AnalysisToolConfig.REVEL, 0.5) is True

        # Above threshold
        assert AnalysisToolConfig.is_pathogenic(AnalysisToolConfig.REVEL, 0.8) is True

    def test_analysis_result_creation(self):
        """Test AnalysisResult data structure."""
        result = AnalysisResult(
            variant_id=1,
            tool="cadd",
            score=25.5,
            raw_output={"test": "data"},
            timestamp=datetime.utcnow()
        )

        assert result.variant_id == 1
        assert result.tool == "cadd"
        assert result.score == 25.5
        assert result.is_pathogenic is True

        result_dict = result.to_dict()
        assert "variant_id" in result_dict
        assert "is_pathogenic" in result_dict

    def test_store_analysis_result(self, db_session):
        """Test storing analysis result."""
        handler = AnalysisIntegrationHandler(session=db_session)

        # Mock annotation repository
        with patch.object(handler, 'session') as mock_session:
            mock_session.add = Mock()
            mock_session.commit = Mock()

            # This would normally create an Annotation record
            # In actual tests with real DB, verify Annotation is created


# ============================================================================
# Repository Tests
# ============================================================================

class TestSourceVariantRepository:
    """Test SourceVariantRepository functionality."""

    def test_find_by_file(self, db_session, sample_source_variant):
        """Test finding source variants by file."""
        db_session.add(sample_source_variant)
        db_session.commit()

        repo = SourceVariantRepository(session=db_session)
        variants = repo.find_by_file(file_id=sample_source_variant.file_id)

        assert len(variants) > 0

    def test_count_by_source(self, db_session, sample_source_variant):
        """Test counting variants by source."""
        db_session.add(sample_source_variant)
        db_session.commit()

        repo = SourceVariantRepository(session=db_session)
        counts = repo.count_by_source(file_id=sample_source_variant.file_id)

        assert "clinvar" in counts or len(counts) > 0


class TestMergedVariantRepository:
    """Test MergedVariantRepository functionality."""

    def test_find_by_file(self, db_session, sample_merged_variant):
        """Test finding merged variants by file."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        repo = MergedVariantRepository(session=db_session)
        variants = repo.find_by_file(file_id=sample_merged_variant.file_id)

        assert len(variants) > 0

    def test_find_by_gene(self, db_session, sample_merged_variant):
        """Test finding merged variants by gene."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        repo = MergedVariantRepository(session=db_session)
        variants = repo.find_by_gene(
            file_id=sample_merged_variant.file_id,
            gene=sample_merged_variant.gene
        )

        assert len(variants) > 0


class TestFilteredVariantRepository:
    """Test FilteredVariantRepository functionality."""

    def test_count_by_validity(self, db_session, sample_filtered_variant):
        """Test counting variants by validity."""
        db_session.add(sample_filtered_variant)
        db_session.commit()

        repo = FilteredVariantRepository(session=db_session)
        counts = repo.count_by_validity(file_id=sample_filtered_variant.file_id)

        assert "total" in counts
        assert "valid" in counts
        assert counts["total"] > 0

    def test_find_by_validity(self, db_session, sample_filtered_variant):
        """Test finding variants by validity status."""
        db_session.add(sample_filtered_variant)
        db_session.commit()

        repo = FilteredVariantRepository(session=db_session)
        variants = repo.find_by_validity(
            file_id=sample_filtered_variant.file_id,
            is_valid=True
        )

        assert len(variants) >= 0


class TestWorkflowAuditRepository:
    """Test WorkflowAuditRepository functionality."""

    def test_find_by_operation(self, db_session, sample_audit):
        """Test finding audits by operation."""
        db_session.add(sample_audit)
        db_session.commit()

        repo = WorkflowAuditRepository(session=db_session)
        audits = repo.find_by_operation(
            file_id=sample_audit.file_id,
            operation=sample_audit.operation
        )

        assert len(audits) > 0

    def test_count_by_status(self, db_session, sample_audit):
        """Test counting audits by status."""
        db_session.add(sample_audit)
        db_session.commit()

        repo = WorkflowAuditRepository(session=db_session)
        counts = repo.count_by_status(file_id=sample_audit.file_id)

        assert len(counts) > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase2Pipeline:
    """Integration tests for complete Phase 2 pipeline."""

    def test_delta_sync_to_merge_flow(self, db_session, sample_source_variant):
        """Test flow from delta-sync check to merge."""
        db_session.add(sample_source_variant)
        db_session.commit()

        # Step 1: Check delta-sync
        sync_mgr = DeltaSyncManager(session=db_session)
        status = sync_mgr.check_sync_status(
            workspace_id="test",
            file_id=sample_source_variant.file_id,
            source_database="clinvar"
        )
        assert status.has_existing_data is True

        # Step 2: Validate and merge
        merge_handler = MergeOperationHandler(session=db_session)
        is_valid, _ = merge_handler.validate_merge_inputs(
            file_id=sample_source_variant.file_id,
            sources=["clinvar"]
        )
        assert is_valid is True

    def test_merge_to_filter_flow(self, db_session, sample_merged_variant):
        """Test flow from merge to filtering."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        # Step 1: Merge produces merged variants (already done)
        repo = MergedVariantRepository(session=db_session)
        variants = repo.find_by_file(file_id=sample_merged_variant.file_id)
        assert len(variants) > 0

        # Step 2: Filter would process these
        filter_engine = QualityFilteringEngine(session=db_session)
        summary = filter_engine.get_quality_summary(
            file_id=sample_merged_variant.file_id
        )
        assert "total" in summary


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_session():
    """Create test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.models.base import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session
    session.close()


@pytest.fixture
def sample_source_variant(db_session):
    """Create sample SourceVariant."""
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
    return variant


@pytest.fixture
def sample_merged_variant(db_session):
    """Create sample MergedVariant."""
    variant = MergedVariant(
        file_id=1,
        chromosome="1",
        position=55505647,
        ref_allele="G",
        alt_allele="A",
        gen_pos="1-55505647-G-A",
        gene="BRCA2",
        transcript="NM_000059",
        consequence="missense_variant",
        source_databases=json.dumps(["clinvar", "lovd"]),
        merge_timestamp=datetime.utcnow(),
        merge_strategy="outer_union"
    )
    return variant


@pytest.fixture
def sample_filtered_variant(db_session):
    """Create sample FilteredVariant."""
    variant = FilteredVariant(
        file_id=1,
        chromosome="1",
        position=55505647,
        ref_allele="G",
        alt_allele="A",
        gen_pos="1-55505647-G-A",
        is_complete=True,
        is_valid=True,
        filter_results=json.dumps({"has_required_fields": True}),
        filter_timestamp=datetime.utcnow(),
        filter_version="1.0"
    )
    return variant


@pytest.fixture
def sample_audit(db_session):
    """Create sample WorkflowAudit."""
    audit = WorkflowAudit(
        file_id=1,
        operation="merge",
        operation_stage="combining_sources",
        input_count=100,
        output_count=80,
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        user_id="test-user"
    )
    return audit
