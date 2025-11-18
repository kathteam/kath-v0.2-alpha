"""
Unit Tests for Phase 2 Quality Filtering Module

Comprehensive unit tests for quality filters, filtering engine,
and quality assessment functionality.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.quality_filtering import (
    QualityFilteringEngine,
    QualityFilter,
    RequiredFieldsFilter,
    GenomicCoordinateFilter,
    AlleleValidityFilter,
    CanonicalFormatFilter,
    AnnotationPresenceFilter,
    SourceAttributionFilter,
    FilterResult
)
from src.models.base import Base
from src.models.merged_variant import MergedVariant
from src.models.filtered_variant import FilteredVariant


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
def filtering_engine(db_session):
    """Create QualityFilteringEngine instance."""
    return QualityFilteringEngine(session=db_session)


@pytest.fixture
def sample_merged_variant():
    """Create sample merged variant for testing."""
    return MergedVariant(
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


@pytest.fixture
def sample_merged_variants_invalid():
    """Create sample merged variants with quality issues."""
    return [
        # Invalid chromosome
        MergedVariant(
            file_id=1,
            chromosome="99",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="99-55505647-G-A",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        ),
        # Invalid allele characters
        MergedVariant(
            file_id=1,
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="X",  # Invalid DNA character
            gen_pos="1-55505647-G-X",
            gene="BRCA2",
            transcript="NM_000059",
            consequence="missense_variant",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        ),
        # No gene annotation
        MergedVariant(
            file_id=1,
            chromosome="1",
            position=55505647,
            ref_allele="G",
            alt_allele="A",
            gen_pos="1-55505647-G-A",
            gene=None,
            transcript=None,
            consequence="missense_variant",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        ),
    ]


class TestQualityFilterInitialization:
    """Test QualityFilter initialization."""

    def test_required_fields_filter_creation(self):
        """Test RequiredFieldsFilter creation."""
        filter_obj = RequiredFieldsFilter()
        assert filter_obj.name == "has_required_fields"
        assert filter_obj.is_critical is True

    def test_genomic_coordinate_filter_creation(self):
        """Test GenomicCoordinateFilter creation."""
        filter_obj = GenomicCoordinateFilter()
        assert filter_obj.name == "valid_coordinates"
        assert filter_obj.is_critical is True

    def test_allele_validity_filter_creation(self):
        """Test AlleleValidityFilter creation."""
        filter_obj = AlleleValidityFilter()
        assert filter_obj.name == "valid_alleles"
        assert filter_obj.is_critical is True

    def test_canonical_format_filter_creation(self):
        """Test CanonicalFormatFilter creation."""
        filter_obj = CanonicalFormatFilter()
        assert filter_obj.name == "valid_gen_pos"
        assert filter_obj.is_critical is True

    def test_annotation_presence_filter_creation(self):
        """Test AnnotationPresenceFilter creation."""
        filter_obj = AnnotationPresenceFilter()
        assert filter_obj.name == "has_annotation"
        assert filter_obj.is_critical is False  # Soft filter

    def test_source_attribution_filter_creation(self):
        """Test SourceAttributionFilter creation."""
        filter_obj = SourceAttributionFilter()
        assert filter_obj.name == "has_source_data"
        assert filter_obj.is_critical is False  # Soft filter


class TestRequiredFieldsFilter:
    """Test RequiredFieldsFilter functionality."""

    def test_required_fields_all_present(self, sample_merged_variant):
        """Test filter passes when all required fields present."""
        filter_obj = RequiredFieldsFilter()
        passed, reason = filter_obj.apply(sample_merged_variant)
        assert passed is True
        assert reason is None

    def test_required_fields_missing_chromosome(self):
        """Test filter fails when chromosome missing."""
        variant = Mock()
        variant.chromosome = None
        variant.position = 1000
        variant.ref_allele = "A"
        variant.alt_allele = "T"

        filter_obj = RequiredFieldsFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False
        assert "Missing required field" in reason

    def test_required_fields_missing_position(self):
        """Test filter fails when position missing."""
        variant = Mock()
        variant.chromosome = "1"
        variant.position = None
        variant.ref_allele = "A"
        variant.alt_allele = "T"

        filter_obj = RequiredFieldsFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False

    def test_required_fields_empty_allele(self):
        """Test filter fails when allele is empty string."""
        variant = Mock()
        variant.chromosome = "1"
        variant.position = 1000
        variant.ref_allele = ""
        variant.alt_allele = "T"

        filter_obj = RequiredFieldsFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False


class TestGenomicCoordinateFilter:
    """Test GenomicCoordinateFilter functionality."""

    def test_valid_chromosomes(self, sample_merged_variant):
        """Test filter passes for valid chromosomes."""
        filter_obj = GenomicCoordinateFilter()

        for chrom in ["1", "2", "22", "X", "Y", "MT"]:
            sample_merged_variant.chromosome = chrom
            passed, reason = filter_obj.apply(sample_merged_variant)
            assert passed is True, f"Failed for chromosome {chrom}"

    def test_invalid_chromosome(self):
        """Test filter fails for invalid chromosomes."""
        variant = Mock()
        variant.chromosome = "99"
        variant.position = 1000
        variant.ref_allele = "A"
        variant.alt_allele = "T"

        filter_obj = GenomicCoordinateFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False
        assert "Invalid chromosome" in reason

    def test_zero_position(self):
        """Test filter fails for zero position."""
        variant = Mock()
        variant.chromosome = "1"
        variant.position = 0
        variant.ref_allele = "A"
        variant.alt_allele = "T"

        filter_obj = GenomicCoordinateFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False
        assert "must be positive" in reason

    def test_negative_position(self):
        """Test filter fails for negative position."""
        variant = Mock()
        variant.chromosome = "1"
        variant.position = -1000
        variant.ref_allele = "A"
        variant.alt_allele = "T"

        filter_obj = GenomicCoordinateFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False

    def test_valid_positions(self, sample_merged_variant):
        """Test filter passes for valid positions."""
        filter_obj = GenomicCoordinateFilter()

        for pos in [1, 100, 1000000, 248956422]:
            sample_merged_variant.position = pos
            passed, reason = filter_obj.apply(sample_merged_variant)
            assert passed is True


class TestAlleleValidityFilter:
    """Test AlleleValidityFilter functionality."""

    def test_valid_dna_characters(self, sample_merged_variant):
        """Test filter passes for valid DNA characters."""
        filter_obj = AlleleValidityFilter()

        for ref, alt in [("A", "T"), ("G", "C"), ("N", "A"), ("ATG", "C")]:
            sample_merged_variant.ref_allele = ref
            sample_merged_variant.alt_allele = alt
            passed, reason = filter_obj.apply(sample_merged_variant)
            assert passed is True

    def test_invalid_dna_characters(self):
        """Test filter fails for invalid DNA characters."""
        variant = Mock()
        variant.chromosome = "1"
        variant.position = 1000
        variant.ref_allele = "A"
        variant.alt_allele = "X"  # Invalid

        filter_obj = AlleleValidityFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False
        assert "Invalid" in reason

    def test_lowercase_dna_accepted(self):
        """Test filter handles lowercase DNA characters."""
        variant = Mock()
        variant.chromosome = "1"
        variant.position = 1000
        variant.ref_allele = "a"  # lowercase
        variant.alt_allele = "t"  # lowercase

        filter_obj = AlleleValidityFilter()
        passed, reason = filter_obj.apply(variant)
        # Should handle case-insensitively
        assert passed is True


class TestCanonicalFormatFilter:
    """Test CanonicalFormatFilter functionality."""

    def test_valid_gen_pos_format(self, sample_merged_variant):
        """Test filter passes for valid gen_pos format."""
        filter_obj = CanonicalFormatFilter()
        passed, reason = filter_obj.apply(sample_merged_variant)
        assert passed is True

    def test_invalid_gen_pos_format(self):
        """Test filter fails for invalid gen_pos format."""
        variant = Mock()
        variant.gen_pos = "invalid-format"  # Only 2 parts instead of 4

        filter_obj = CanonicalFormatFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False

    def test_missing_gen_pos(self):
        """Test filter fails when gen_pos is missing."""
        variant = Mock()
        variant.gen_pos = None

        filter_obj = CanonicalFormatFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False


class TestAnnotationPresenceFilter:
    """Test AnnotationPresenceFilter functionality."""

    def test_annotation_filter_with_gene(self, sample_merged_variant):
        """Test filter passes when gene present."""
        filter_obj = AnnotationPresenceFilter()
        passed, reason = filter_obj.apply(sample_merged_variant)
        assert passed is True

    def test_annotation_filter_with_transcript(self):
        """Test filter passes when transcript present."""
        variant = Mock()
        variant.gene = None
        variant.transcript = "NM_000059"

        filter_obj = AnnotationPresenceFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is True

    def test_annotation_filter_no_annotations(self):
        """Test filter fails when no annotations present."""
        variant = Mock()
        variant.gene = None
        variant.transcript = None

        filter_obj = AnnotationPresenceFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False


class TestSourceAttributionFilter:
    """Test SourceAttributionFilter functionality."""

    def test_source_attribution_filter_with_sources(self, sample_merged_variant):
        """Test filter passes when source data present."""
        filter_obj = SourceAttributionFilter()
        passed, reason = filter_obj.apply(sample_merged_variant)
        assert passed is True

    def test_source_attribution_filter_no_sources(self):
        """Test filter fails when no source data."""
        variant = Mock()
        variant.source_list = []

        filter_obj = SourceAttributionFilter()
        passed, reason = filter_obj.apply(variant)
        assert passed is False


class TestFilteringEngineInitialization:
    """Test QualityFilteringEngine initialization."""

    def test_engine_initialization(self, filtering_engine):
        """Test filtering engine initializes with filters."""
        assert filtering_engine.critical_filters is not None
        assert filtering_engine.soft_filters is not None
        assert filtering_engine.all_filters is not None
        assert len(filtering_engine.all_filters) == 6

    def test_critical_filters_count(self, filtering_engine):
        """Test critical filters are initialized."""
        assert len(filtering_engine.critical_filters) == 4

    def test_soft_filters_count(self, filtering_engine):
        """Test soft filters are initialized."""
        assert len(filtering_engine.soft_filters) == 2


class TestFilterResultDataStructure:
    """Test FilterResult data structure."""

    def test_filter_result_creation(self):
        """Test FilterResult object creation."""
        result = FilterResult(
            total_variants=100,
            valid_variants=95,
            complete_variants=90,
            invalid_variants=5,
            filter_details={},
            duration_seconds=1.5
        )

        assert result.total_variants == 100
        assert result.valid_variants == 95
        assert result.complete_variants == 90
        assert result.invalid_variants == 5
        assert result.duration_seconds == 1.5

    def test_filter_result_to_dict(self):
        """Test FilterResult serialization."""
        result = FilterResult(
            total_variants=100,
            valid_variants=95,
            complete_variants=90,
            invalid_variants=5,
            filter_details={},
            duration_seconds=1.5
        )

        result_dict = result.to_dict()
        assert result_dict["total_variants"] == 100
        assert result_dict["valid_variants"] == 95
        assert "timestamp" in result_dict


class TestFilterApplication:
    """Test filter application functionality."""

    def test_apply_filters_with_valid_variants(self, filtering_engine, db_session, sample_merged_variant):
        """Test filter application with valid variants."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        result = filtering_engine.apply_filters(file_id=1, user_id="test-user")

        assert result.total_variants > 0
        assert result.valid_variants > 0

    def test_apply_filters_with_invalid_variants(self, filtering_engine, db_session, sample_merged_variants_invalid):
        """Test filter application detects invalid variants."""
        for variant in sample_merged_variants_invalid:
            db_session.add(variant)
        db_session.commit()

        result = filtering_engine.apply_filters(file_id=1, user_id="test-user")

        assert result.total_variants > 0
        assert result.invalid_variants > 0

    def test_apply_filters_empty_file(self, filtering_engine):
        """Test filter application with empty file."""
        with pytest.raises(ValueError):
            filtering_engine.apply_filters(file_id=999)


class TestQualitySummary:
    """Test quality summary reporting."""

    def test_get_quality_summary(self, filtering_engine, db_session, sample_merged_variant):
        """Test quality summary generation."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        filtering_engine.apply_filters(file_id=1)

        summary = filtering_engine.get_quality_summary(file_id=1)

        assert "total" in summary
        assert "valid" in summary
        assert "invalid" in summary
        assert "quality_rate" in summary

    def test_quality_rate_calculation(self, filtering_engine, db_session, sample_merged_variant):
        """Test quality rate is calculated correctly."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        filtering_engine.apply_filters(file_id=1)

        summary = filtering_engine.get_quality_summary(file_id=1)

        if summary["total"] > 0:
            expected_rate = (summary["valid"] / summary["total"]) * 100
            assert abs(summary["quality_rate"] - expected_rate) < 0.1


class TestFilterVersioning:
    """Test filter versioning functionality."""

    def test_filter_version_tracked(self, filtering_engine, db_session, sample_merged_variant):
        """Test filter version is tracked."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        result = filtering_engine.apply_filters(file_id=1)

        # Check that filtered variants have version info
        filtered_variants = db_session.query(FilteredVariant).filter_by(file_id=1).all()
        for variant in filtered_variants:
            assert variant.filter_version is not None

    def test_filter_version_update(self, filtering_engine, db_session, sample_merged_variant):
        """Test filter can be updated with new version."""
        db_session.add(sample_merged_variant)
        db_session.commit()

        # Apply filters with version update
        result = filtering_engine.refilter_with_version(
            file_id=1,
            new_version="2.0",
            user_id="test-user"
        )

        assert result is not None
