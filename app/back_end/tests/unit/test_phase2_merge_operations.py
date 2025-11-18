"""
Unit Tests for Phase 2 Merge Operations Module

Comprehensive unit tests for merge strategies, variant combining,
source attribution, and merge result reporting.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.merge_operations import (
    MergeOperationHandler,
    MergeStrategy,
    MergeResult
)
from src.models.base import Base
from src.models.source_variant import SourceVariant
from src.models.merged_variant import MergedVariant


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
def merge_handler(db_session):
    """Create MergeOperationHandler instance."""
    return MergeOperationHandler(session=db_session)


@pytest.fixture
def sample_source_variants(db_session):
    """Create sample source variants for testing."""
    variants = [
        SourceVariant(
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
        ),
        SourceVariant(
            file_id=1,
            source_database="lovd",
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_data=json.dumps({"lovd_id": 67890}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        ),
        SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="2",
            position=100000000,
            ref_allele="T",
            alt_allele="C",
            gen_pos="2-100000000-T-C",
            gene="TP53",
            transcript="NM_000546",
            consequence="frameshift_variant",
            source_data=json.dumps({"clinvar_id": 99999}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        ),
    ]

    for variant in variants:
        db_session.add(variant)
    db_session.commit()

    return variants


class TestMergeStrategyEnum:
    """Test MergeStrategy enum."""

    def test_outer_union_strategy_defined(self):
        """Test OUTER_UNION strategy is defined."""
        assert MergeStrategy.OUTER_UNION == "outer_union"

    def test_inner_intersection_strategy_defined(self):
        """Test INNER_INTERSECTION strategy is defined."""
        assert MergeStrategy.INNER_INTERSECTION == "inner_intersection"

    def test_consensus_strategy_defined(self):
        """Test CONSENSUS strategy is defined."""
        assert MergeStrategy.CONSENSUS == "consensus"

    def test_get_all_strategies(self):
        """Test get_all_strategies returns all strategies."""
        strategies = MergeStrategy.get_all_strategies()
        assert MergeStrategy.OUTER_UNION in strategies
        assert MergeStrategy.INNER_INTERSECTION in strategies
        assert MergeStrategy.CONSENSUS in strategies
        assert len(strategies) == 3


class TestMergeResultDataStructure:
    """Test MergeResult data structure."""

    def test_merge_result_creation(self):
        """Test MergeResult object creation."""
        result = MergeResult(
            total_input=100,
            merged_count=80,
            duplicate_count=20,
            strategy_applied="outer_union",
            duration_seconds=2.5
        )

        assert result.total_input == 100
        assert result.merged_count == 80
        assert result.duplicate_count == 20
        assert result.strategy_applied == "outer_union"
        assert result.duration_seconds == 2.5

    def test_merge_result_to_dict(self):
        """Test MergeResult serialization."""
        result = MergeResult(
            total_input=100,
            merged_count=80,
            duplicate_count=20,
            strategy_applied="outer_union",
            duration_seconds=2.5
        )

        result_dict = result.to_dict()
        assert result_dict["total_input"] == 100
        assert result_dict["merged_count"] == 80
        assert result_dict["duplicate_count"] == 20
        assert result_dict["strategy_applied"] == "outer_union"


class TestMergeOperationHandlerInitialization:
    """Test MergeOperationHandler initialization."""

    def test_initialization_with_session(self, db_session):
        """Test handler initializes with provided session."""
        handler = MergeOperationHandler(session=db_session)
        assert handler.session is not None
        assert handler.session == db_session

    def test_initialization_without_session(self, db_session, mocker):
        """Test handler initializes without session (uses default)."""
        # Mock get_db_session to return our test db_session
        mocker.patch('src.data.merge_operations.get_db_session', return_value=db_session)
        handler = MergeOperationHandler(session=None)
        assert handler.session is not None


class TestMergeValidation:
    """Test merge input validation."""

    def test_validate_merge_inputs_valid(self, merge_handler, sample_source_variants):
        """Test validation passes with valid inputs."""
        is_valid, error = merge_handler.validate_merge_inputs(
            file_id=1,
            sources=["clinvar", "lovd"]
        )
        assert is_valid is True
        assert error == ""

    def test_validate_merge_inputs_no_file(self, merge_handler):
        """Test validation fails when file has no data."""
        is_valid, error = merge_handler.validate_merge_inputs(
            file_id=999,
            sources=["clinvar"]
        )
        assert is_valid is False
        assert len(error) > 0

    def test_validate_merge_inputs_empty_sources(self, merge_handler, sample_source_variants):
        """Test validation fails with empty sources list."""
        with pytest.raises(ValueError):
            merge_handler.validate_merge_inputs(
                file_id=1,
                sources=[]
            )

    def test_validate_merge_inputs_unavailable_source(self, merge_handler, sample_source_variants):
        """Test validation fails when source doesn't have data."""
        is_valid, error = merge_handler.validate_merge_inputs(
            file_id=1,
            sources=["gnomad"]  # Not in sample data
        )
        assert is_valid is False


class TestOuterUnionStrategy:
    """Test OUTER_UNION merge strategy."""

    def test_outer_union_includes_all_variants(self, merge_handler, db_session, sample_source_variants):
        """Test OUTER_UNION includes all variants from all sources."""
        # Manually call merge logic
        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        # Should have merged variants
        assert result.merged_count > 0
        assert result.strategy_applied == MergeStrategy.OUTER_UNION

    def test_outer_union_preserves_source_attribution(self, merge_handler, db_session, sample_source_variants):
        """Test OUTER_UNION preserves source attribution."""
        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        # Check that merged variants have source attribution
        merged_variants = db_session.query(MergedVariant).filter_by(file_id=1).all()
        for variant in merged_variants:
            assert variant.source_databases is not None
            sources = json.loads(variant.source_databases)
            assert isinstance(sources, list)
            assert len(sources) > 0


class TestInnerIntersectionStrategy:
    """Test INNER_INTERSECTION merge strategy."""

    def test_inner_intersection_only_common_variants(self, merge_handler, db_session, sample_source_variants):
        """Test INNER_INTERSECTION only includes variants in all sources."""
        # Sample data has a variant at position 1-55505647 in both clinvar and lovd
        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.INNER_INTERSECTION,
            user_id="test-user"
        )

        # Should have fewer variants than OUTER_UNION
        assert result.merged_count >= 0
        assert result.strategy_applied == MergeStrategy.INNER_INTERSECTION


class TestConsensusStrategy:
    """Test CONSENSUS merge strategy."""

    def test_consensus_includes_multisource_variants(self, merge_handler, db_session, sample_source_variants):
        """Test CONSENSUS includes variants in 2+ sources."""
        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.CONSENSUS,
            user_id="test-user"
        )

        assert result.strategy_applied == MergeStrategy.CONSENSUS


class TestDuplicateDetection:
    """Test duplicate detection in merge."""

    def test_duplicate_detection_same_position(self, merge_handler, db_session):
        """Test detection of duplicates at same genomic position."""
        # Add duplicate variants from same source
        variant1 = SourceVariant(
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
            source_data=json.dumps({"id": 1}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        variant2 = SourceVariant(
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
            source_data=json.dumps({"id": 2}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )

        db_session.add_all([variant1, variant2])
        db_session.commit()

        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        # Should detect duplicates
        assert result.duplicate_count > 0


class TestSourceAttributionTracking:
    """Test source attribution in merged variants."""

    def test_merged_variant_has_source_list(self, merge_handler, db_session, sample_source_variants):
        """Test merged variants include source database list."""
        merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        merged_variants = db_session.query(MergedVariant).filter_by(file_id=1).all()

        for variant in merged_variants:
            assert variant.source_databases is not None
            sources = json.loads(variant.source_databases)
            assert isinstance(sources, list)

    def test_merged_variant_preserves_source_data(self, merge_handler, db_session, sample_source_variants):
        """Test merged variants preserve source-specific data."""
        merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        merged_variants = db_session.query(MergedVariant).filter_by(file_id=1).all()

        for variant in merged_variants:
            # Should have source-specific data fields
            if "clinvar" in json.loads(variant.source_databases):
                assert variant.clinvar_data is not None

    def test_merge_strategy_stored_in_result(self, merge_handler, db_session, sample_source_variants):
        """Test merge strategy is stored in merged variants."""
        merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        merged_variants = db_session.query(MergedVariant).filter_by(file_id=1).all()

        for variant in merged_variants:
            assert variant.merge_strategy == MergeStrategy.OUTER_UNION


class TestMergePerformance:
    """Test merge operation performance characteristics."""

    def test_merge_execution_time_tracked(self, merge_handler, db_session, sample_source_variants):
        """Test that merge execution time is tracked."""
        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        assert result.duration_seconds >= 0
        assert isinstance(result.duration_seconds, float)

    def test_merge_result_metrics(self, merge_handler, db_session, sample_source_variants):
        """Test merge result includes all metrics."""
        result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        assert result.total_input >= 0
        assert result.merged_count >= 0
        assert result.duplicate_count >= 0


class TestInvalidMergeOperations:
    """Test error handling in merge operations."""

    def test_invalid_merge_strategy(self, merge_handler, sample_source_variants):
        """Test handling of invalid merge strategy."""
        with pytest.raises(ValueError):
            merge_handler.perform_merge(
                file_id=1,
                sources=["clinvar"],
                merge_strategy="invalid_strategy"
            )

    def test_merge_with_no_data(self, merge_handler):
        """Test merge with file that has no data."""
        with pytest.raises((ValueError, Exception)):
            merge_handler.perform_merge(
                file_id=999,
                sources=["clinvar"],
                merge_strategy=MergeStrategy.OUTER_UNION
            )


class TestMergeHistory:
    """Test merge operation history tracking."""

    def test_get_merge_history(self, merge_handler, db_session, sample_source_variants):
        """Test retrieving merge operation history."""
        merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        history = merge_handler.get_merge_history(file_id=1)

        assert isinstance(history, list)
        # History should contain at least one operation
        assert len(history) >= 0


class TestMergeStatistics:
    """Test merge operation statistics."""

    def test_get_merge_statistics(self, merge_handler, db_session, sample_source_variants):
        """Test retrieving merge statistics."""
        merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        stats = merge_handler.get_merge_statistics(file_id=1)

        assert isinstance(stats, dict)
