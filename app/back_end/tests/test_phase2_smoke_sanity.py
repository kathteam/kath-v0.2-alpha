"""
Smoke Tests and Sanity Tests for Phase 2

Quick validation tests for critical functionality and basic system health.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.delta_sync import DeltaSyncManager, DeltaSyncStatus
from src.data.merge_operations import MergeOperationHandler, MergeStrategy
from src.data.quality_filtering import QualityFilteringEngine
from src.data.analysis_integration import AnalysisIntegrationHandler, AnalysisToolConfig
from src.models.base import Base
from src.models.source_variant import SourceVariant
from src.models.merged_variant import MergedVariant


@pytest.fixture(scope="session")
def db_engine():
    """Create in-memory database for entire test session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create database session for each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()


# ============================================================================
# SMOKE TESTS - Critical Path Validation
# ============================================================================

class TestPhase2SmokeTests:
    """Smoke tests for critical Phase 2 functionality."""

    @pytest.mark.smoke
    def test_delta_sync_manager_instantiation(self, db_session):
        """Test DeltaSyncManager can be instantiated."""
        manager = DeltaSyncManager(session=db_session)
        assert manager is not None
        assert manager.session is not None

    @pytest.mark.smoke
    def test_delta_sync_check_status_works(self, db_session):
        """Test basic delta-sync status check."""
        manager = DeltaSyncManager(session=db_session)
        status = manager.check_sync_status("test", 1, "clinvar")
        assert isinstance(status, DeltaSyncStatus)
        assert hasattr(status, "has_existing_data")

    @pytest.mark.smoke
    def test_merge_operation_handler_instantiation(self, db_session):
        """Test MergeOperationHandler can be instantiated."""
        handler = MergeOperationHandler(session=db_session)
        assert handler is not None
        assert handler.session is not None

    @pytest.mark.smoke
    def test_merge_strategies_available(self):
        """Test all merge strategies are defined."""
        strategies = MergeStrategy.get_all_strategies()
        assert len(strategies) == 3
        assert "outer_union" in strategies
        assert "inner_intersection" in strategies
        assert "consensus" in strategies

    @pytest.mark.smoke
    def test_quality_filtering_engine_instantiation(self, db_session):
        """Test QualityFilteringEngine can be instantiated."""
        engine = QualityFilteringEngine(session=db_session)
        assert engine is not None
        assert engine.session is not None

    @pytest.mark.smoke
    def test_filtering_engine_has_filters(self, db_session):
        """Test filtering engine has filters initialized."""
        engine = QualityFilteringEngine(session=db_session)
        assert len(engine.critical_filters) > 0
        assert len(engine.soft_filters) > 0
        assert len(engine.all_filters) > 0

    @pytest.mark.smoke
    def test_analysis_integration_handler_instantiation(self, db_session):
        """Test AnalysisIntegrationHandler can be instantiated."""
        handler = AnalysisIntegrationHandler(session=db_session)
        assert handler is not None
        assert handler.session is not None

    @pytest.mark.smoke
    def test_analysis_tools_configured(self):
        """Test analysis tools are configured."""
        tools = AnalysisToolConfig.get_all_tools()
        assert len(tools) == 3
        assert "cadd" in tools
        assert "revel" in tools
        assert "spliceai" in tools

    @pytest.mark.smoke
    def test_pathogenicity_thresholds_defined(self):
        """Test pathogenicity thresholds are defined."""
        assert "cadd" in AnalysisToolConfig.PATHOGENICITY_THRESHOLDS
        assert "revel" in AnalysisToolConfig.PATHOGENICITY_THRESHOLDS
        assert "spliceai" in AnalysisToolConfig.PATHOGENICITY_THRESHOLDS

    @pytest.mark.smoke
    def test_score_ranges_defined(self):
        """Test score ranges are defined for all tools."""
        assert "cadd" in AnalysisToolConfig.SCORE_RANGES
        assert "revel" in AnalysisToolConfig.SCORE_RANGES
        assert "spliceai" in AnalysisToolConfig.SCORE_RANGES


# ============================================================================
# SANITY TESTS - Basic Functionality Validation
# ============================================================================

class TestPhase2SanityTests:
    """Sanity tests for basic Phase 2 functionality."""

    @pytest.mark.sanity
    def test_source_variant_model_creation(self):
        """Test SourceVariant model can be created."""
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        assert variant is not None
        assert variant.source_database == "clinvar"
        assert variant.chromosome == "1"

    @pytest.mark.sanity
    def test_merged_variant_model_creation(self):
        """Test MergedVariant model can be created."""
        variant = MergedVariant(
            file_id=1,
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense_variant",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        )
        assert variant is not None
        assert variant.merge_strategy == "outer_union"

    @pytest.mark.sanity
    def test_delta_sync_status_creation(self):
        """Test DeltaSyncStatus object can be created."""
        status = DeltaSyncStatus(
            has_existing_data=True,
            record_count=100,
            requires_full_sync=False,
            version_mismatch=False,
            last_import_timestamp=datetime.utcnow()
        )
        assert status is not None
        assert status.record_count == 100

    @pytest.mark.sanity
    def test_delta_sync_status_serialization(self):
        """Test DeltaSyncStatus can be serialized to dict."""
        status = DeltaSyncStatus(
            has_existing_data=True,
            record_count=100,
            requires_full_sync=False,
            version_mismatch=False,
            last_import_timestamp=datetime.utcnow()
        )
        status_dict = status.to_dict()
        assert isinstance(status_dict, dict)
        assert "record_count" in status_dict

    @pytest.mark.sanity
    def test_merge_strategy_enum_values(self):
        """Test MergeStrategy enum has correct values."""
        assert MergeStrategy.OUTER_UNION == "outer_union"
        assert MergeStrategy.INNER_INTERSECTION == "inner_intersection"
        assert MergeStrategy.CONSENSUS == "consensus"

    @pytest.mark.sanity
    def test_analysis_tool_config_cadd(self):
        """Test CADD tool configuration."""
        assert AnalysisToolConfig.CADD == "cadd"
        assert AnalysisToolConfig.PATHOGENICITY_THRESHOLDS["cadd"] == 20
        assert AnalysisToolConfig.SCORE_RANGES["cadd"]["max"] == 100

    @pytest.mark.sanity
    def test_analysis_tool_config_revel(self):
        """Test REVEL tool configuration."""
        assert AnalysisToolConfig.REVEL == "revel"
        assert AnalysisToolConfig.PATHOGENICITY_THRESHOLDS["revel"] == 0.5
        assert AnalysisToolConfig.SCORE_RANGES["revel"]["max"] == 1

    @pytest.mark.sanity
    def test_analysis_tool_config_spliceai(self):
        """Test SpliceAI tool configuration."""
        assert AnalysisToolConfig.SPLICEAI == "spliceai"
        assert AnalysisToolConfig.PATHOGENICITY_THRESHOLDS["spliceai"] == 0.2
        assert AnalysisToolConfig.SCORE_RANGES["spliceai"]["max"] == 1

    @pytest.mark.sanity
    def test_pathogenicity_classification_cadd_threshold(self):
        """Test CADD pathogenicity classification at threshold."""
        # Score below threshold
        assert AnalysisToolConfig.is_pathogenic("cadd", 19) is False
        # Score at threshold
        assert AnalysisToolConfig.is_pathogenic("cadd", 20) is True
        # Score above threshold
        assert AnalysisToolConfig.is_pathogenic("cadd", 21) is True

    @pytest.mark.sanity
    def test_pathogenicity_classification_revel_threshold(self):
        """Test REVEL pathogenicity classification at threshold."""
        # Score below threshold
        assert AnalysisToolConfig.is_pathogenic("revel", 0.49) is False
        # Score at threshold
        assert AnalysisToolConfig.is_pathogenic("revel", 0.5) is True
        # Score above threshold
        assert AnalysisToolConfig.is_pathogenic("revel", 0.51) is True

    @pytest.mark.sanity
    def test_pathogenicity_classification_spliceai_threshold(self):
        """Test SpliceAI pathogenicity classification at threshold."""
        # Score below threshold
        assert AnalysisToolConfig.is_pathogenic("spliceai", 0.19) is False
        # Score at threshold
        assert AnalysisToolConfig.is_pathogenic("spliceai", 0.2) is True
        # Score above threshold
        assert AnalysisToolConfig.is_pathogenic("spliceai", 0.21) is True

    @pytest.mark.sanity
    def test_invalid_tool_pathogenicity(self):
        """Test pathogenicity check with invalid tool."""
        result = AnalysisToolConfig.is_pathogenic("invalid_tool", 100)
        assert result is False

    @pytest.mark.sanity
    def test_freshness_windows_realistic(self, db_session):
        """Test freshness windows have realistic values."""
        manager = DeltaSyncManager(session=db_session)

        # All windows should be positive integers (hours)
        for window in manager.FRESHNESS_WINDOW.values():
            assert isinstance(window, int)
            assert window > 0

    @pytest.mark.sanity
    def test_source_versions_configured(self, db_session):
        """Test source versions are properly configured."""
        manager = DeltaSyncManager(session=db_session)

        # All known sources should have versions
        for source in ["clinvar", "lovd", "gnomad"]:
            assert source in manager.SOURCE_VERSIONS
            assert isinstance(manager.SOURCE_VERSIONS[source], str)
            assert len(manager.SOURCE_VERSIONS[source]) > 0


# ============================================================================
# CRITICAL PATH VALIDATION
# ============================================================================

class TestCriticalPaths:
    """Tests for critical data flow paths."""

    @pytest.mark.smoke
    def test_delta_sync_to_merge_path(self, db_session):
        """Test complete path from delta-sync to merge."""
        # 1. Create source variant
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        # 2. Check delta-sync status
        sync_mgr = DeltaSyncManager(session=db_session)
        status = sync_mgr.check_sync_status("test", 1, "clinvar")
        assert status.has_existing_data is True

        # 3. Prepare for merge
        merge_handler = MergeOperationHandler(session=db_session)
        is_valid, error = merge_handler.validate_merge_inputs(1, ["clinvar"])
        assert is_valid is True

    @pytest.mark.sanity
    def test_merge_to_filter_path(self, db_session):
        """Test complete path from merge to filtering."""
        # 1. Create merged variant
        variant = MergedVariant(
            file_id=1,
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense_variant",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        )
        db_session.add(variant)
        db_session.commit()

        # 2. Prepare for filtering
        filter_engine = QualityFilteringEngine(session=db_session)
        summary = filter_engine.get_quality_summary(file_id=1)
        assert isinstance(summary, dict)
        assert "total" in summary

    @pytest.mark.smoke
    def test_data_model_hierarchy(self):
        """Test that data models follow hierarchy."""
        # Source → Merged → Filtered hierarchy is valid
        source = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense_variant",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )

        merged = MergedVariant(
            file_id=1,
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense_variant",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        )

        assert source.gen_pos == merged.gen_pos
        assert source.chromosome == merged.chromosome


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestSystemHealth:
    """System health check tests."""

    @pytest.mark.smoke
    def test_all_phase2_modules_importable(self):
        """Test all Phase 2 modules can be imported."""
        from src.data.delta_sync import DeltaSyncManager
        from src.data.merge_operations import MergeOperationHandler
        from src.data.quality_filtering import QualityFilteringEngine
        from src.data.analysis_integration import AnalysisIntegrationHandler

        assert DeltaSyncManager is not None
        assert MergeOperationHandler is not None
        assert QualityFilteringEngine is not None
        assert AnalysisIntegrationHandler is not None

    @pytest.mark.sanity
    def test_all_models_importable(self):
        """Test all Phase 2 models can be imported."""
        from src.models.source_variant import SourceVariant
        from src.models.merged_variant import MergedVariant
        from src.models.filtered_variant import FilteredVariant
        from src.models.workflow_audit import WorkflowAudit

        assert SourceVariant is not None
        assert MergedVariant is not None
        assert FilteredVariant is not None
        assert WorkflowAudit is not None

    @pytest.mark.smoke
    def test_database_session_creation(self, db_session):
        """Test database session can be created."""
        assert db_session is not None
        # Verify session is active
        assert db_session.is_active

    @pytest.mark.sanity
    def test_no_import_errors(self):
        """Test that all modules import without errors."""
        try:
            from src.data import delta_sync
            from src.data import merge_operations
            from src.data import quality_filtering
            from src.data import analysis_integration
            from src.routes import workspace_phase2_route
        except ImportError as e:
            pytest.fail(f"Import error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "smoke or sanity"])
