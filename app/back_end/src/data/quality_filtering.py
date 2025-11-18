"""
Quality Filtering System

Implements variant quality control and validation filtering with configurable
rules, individual filter pass/fail tracking, and complete audit trails.
Ensures only high-quality variants pass through the analysis pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from src.database.config import get_db_session
from src.models import File, FilteredVariant, MergedVariant, WorkflowAudit
from src.database.repositories import (
    FilteredVariantRepository,
    MergedVariantRepository,
    WorkflowAuditRepository,
)

logger = logging.getLogger(__name__)


class QualityFilter:
    """Base class for quality filters."""

    def __init__(self, name: str, description: str, is_critical: bool = False):
        """
        Initialize quality filter.

        Args:
            name: Filter name (e.g., "has_required_fields")
            description: Human-readable filter description
            is_critical: If True, failure means variant is invalid
        """
        self.name = name
        self.description = description
        self.is_critical = is_critical

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        """
        Apply filter to variant.

        Args:
            variant: MergedVariant to filter

        Returns:
            Tuple of (passed, failure_reason)
            If passed=True, failure_reason is None
            If passed=False, failure_reason explains why
        """
        raise NotImplementedError("Subclasses must implement apply()")


class RequiredFieldsFilter(QualityFilter):
    """Validates that all required genomic fields are present."""

    def __init__(self):
        super().__init__(
            name="has_required_fields",
            description="Has all required genomic fields (chromosome, position, ref, alt)",
            is_critical=True,
        )

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        required_fields = ["chromosome", "position", "ref_allele", "alt_allele"]

        for field in required_fields:
            value = getattr(variant, field, None)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return False, f"Missing required field: {field}"

        return True, None


class GenomicCoordinateFilter(QualityFilter):
    """Validates genomic coordinate format and values."""

    def __init__(self):
        super().__init__(
            name="valid_coordinates",
            description="Genomic coordinates are valid (position > 0, valid chromosome)",
            is_critical=True,
        )

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        # Validate chromosome format
        valid_chromosomes = {str(i) for i in range(1, 23)} | {"X", "Y", "MT"}
        chr_val = str(variant.chromosome).upper()
        if chr_val not in valid_chromosomes and not chr_val.startswith("CHR"):
            return False, f"Invalid chromosome: {chr_val}"

        # Validate position is positive integer
        try:
            pos = int(variant.position)
            if pos <= 0:
                return False, f"Invalid position: {pos} (must be positive)"
        except (ValueError, TypeError):
            return False, f"Position not numeric: {variant.position}"

        return True, None


class AlleleValidityFilter(QualityFilter):
    """Validates allele sequences."""

    def __init__(self):
        super().__init__(
            name="valid_alleles",
            description="Alleles contain only valid DNA characters (A, T, G, C, N)",
            is_critical=True,
        )

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        valid_chars = set("ATGCN")

        for allele, name in [(variant.ref_allele, "ref"), (variant.alt_allele, "alt")]:
            allele_upper = str(allele).upper()
            if not all(c in valid_chars for c in allele_upper):
                return False, f"Invalid {name} allele characters: {allele}"

        return True, None


class CanonicalFormatFilter(QualityFilter):
    """Validates canonical gen_pos format."""

    def __init__(self):
        super().__init__(
            name="valid_gen_pos",
            description="gen_pos follows canonical chr-pos-ref-alt format",
            is_critical=True,
        )

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        if not variant.gen_pos:
            return False, "Missing gen_pos"

        parts = str(variant.gen_pos).split("-")
        if len(parts) != 4:
            return False, f"gen_pos format incorrect: {variant.gen_pos}"

        return True, None


class AnnotationPresenceFilter(QualityFilter):
    """Checks for presence of annotations (softer filter)."""

    def __init__(self):
        super().__init__(
            name="has_annotation",
            description="Has at least one annotation (gene or transcript)",
            is_critical=False,
        )

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        has_gene = variant.gene and str(variant.gene).strip()
        has_transcript = variant.transcript and str(variant.transcript).strip()

        if not (has_gene or has_transcript):
            return False, "No annotations (gene or transcript) present"

        return True, None


class SourceAttributionFilter(QualityFilter):
    """Validates source attribution data."""

    def __init__(self):
        super().__init__(
            name="has_source_data",
            description="Has source database attribution data",
            is_critical=False,
        )

    def apply(self, variant: MergedVariant) -> Tuple[bool, Optional[str]]:
        try:
            sources = variant.source_list
            if not sources or len(sources) == 0:
                return False, "No source databases attributed"
        except Exception as e:
            return False, f"Error parsing source data: {str(e)}"

        return True, None


class FilterResult:
    """Data structure representing filtering operation results."""

    def __init__(
        self,
        total_variants: int,
        valid_variants: int,
        complete_variants: int,
        invalid_variants: int,
        filter_details: Dict[str, Dict],
        duration_seconds: float,
    ):
        """
        Initialize filter result.

        Args:
            total_variants: Total variants processed
            valid_variants: Variants passing validity checks
            complete_variants: Variants with all required fields
            invalid_variants: Variants failing critical filters
            filter_details: Dict with results per filter
            duration_seconds: Time taken for filtering
        """
        self.total_variants = total_variants
        self.valid_variants = valid_variants
        self.complete_variants = complete_variants
        self.invalid_variants = invalid_variants
        self.filter_details = filter_details
        self.duration_seconds = duration_seconds
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "total_variants": self.total_variants,
            "valid_variants": self.valid_variants,
            "complete_variants": self.complete_variants,
            "invalid_variants": self.invalid_variants,
            "filter_details": self.filter_details,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


class QualityFilteringEngine:
    """Manages variant quality filtering with configurable rules."""

    FILTER_VERSION = "1.0"  # Update when filter rules change significantly

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize quality filtering engine.

        Args:
            session: SQLAlchemy session. If None, uses get_db_session()
        """
        self.session = session or get_db_session()
        self.filtered_variant_repo = FilteredVariantRepository(session)
        self.merged_variant_repo = MergedVariantRepository(session)
        self.workflow_audit_repo = WorkflowAuditRepository(session)

        # Initialize filter suite
        self._init_filters()

    def _init_filters(self) -> None:
        """Initialize default filter suite."""
        self.critical_filters = [
            RequiredFieldsFilter(),
            GenomicCoordinateFilter(),
            AlleleValidityFilter(),
            CanonicalFormatFilter(),
        ]

        self.soft_filters = [
            AnnotationPresenceFilter(),
            SourceAttributionFilter(),
        ]

        self.all_filters = self.critical_filters + self.soft_filters

    def apply_filters(
        self,
        file_id: int,
        user_id: Optional[str] = None,
    ) -> FilterResult:
        """
        Apply quality filters to merged variants.

        Args:
            file_id: File ID containing merged variants
            user_id: User performing filtering

        Returns:
            FilterResult with operation details

        Raises:
            ValueError: If no merged variants found
        """
        start_time = datetime.utcnow()

        # Create workflow audit entry
        audit = self.workflow_audit_repo.create(
            file_id=file_id,
            operation="filter",
            operation_stage="quality_control",
            status="pending",
            user_id=user_id,
            started_at=start_time,
        )

        try:
            # Get merged variants for this file
            merged_variants = self.merged_variant_repo.find_by_file(file_id)

            if not merged_variants:
                audit.status = "failed"
                audit.error_message = "No merged variants found for filtering"
                self.session.commit()
                raise ValueError("No merged variants found for filtering")

            total_count = len(merged_variants)
            audit.input_count = total_count

            # Apply filters to each variant
            filter_results = self._evaluate_variants(merged_variants)

            # Store filtered variants in database
            filtered_records = self._prepare_filtered_records(
                merged_variants, filter_results
            )

            created_count = self.filtered_variant_repo.create_bulk(filtered_records)

            # Calculate statistics
            stats = self._calculate_statistics(filter_results)
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Update audit entry
            audit.output_count = created_count
            audit.status = "completed"
            audit.completed_at = datetime.utcnow()
            audit.params = json.dumps({"filter_version": self.FILTER_VERSION})
            audit.results = json.dumps(stats)
            self.session.commit()

            result = FilterResult(
                total_variants=total_count,
                valid_variants=stats["valid_count"],
                complete_variants=stats["complete_count"],
                invalid_variants=stats["invalid_count"],
                filter_details=stats["by_filter"],
                duration_seconds=duration,
            )

            logger.info(
                f"Filtering completed: {created_count} variants stored, "
                f"{stats['valid_count']} valid, {stats['invalid_count']} invalid"
            )

            return result

        except Exception as e:
            audit.status = "failed"
            audit.completed_at = datetime.utcnow()
            audit.error_message = str(e)
            self.session.commit()
            logger.error(f"Filtering operation failed: {e}")
            raise

    def _evaluate_variants(
        self, variants: List[MergedVariant]
    ) -> Dict[int, Dict]:
        """
        Evaluate all variants against filter suite.

        Args:
            variants: List of MergedVariant instances

        Returns:
            Dictionary mapping variant.id to filter results
        """
        results = {}

        for variant in variants:
            variant_results = {
                "variant_id": variant.id,
                "filters": {},
                "is_complete": True,
                "is_valid": True,
            }

            # Apply critical filters
            for filter_obj in self.critical_filters:
                passed, reason = filter_obj.apply(variant)
                variant_results["filters"][filter_obj.name] = {
                    "passed": passed,
                    "reason": reason,
                }

                if not passed:
                    if filter_obj.name == "has_required_fields":
                        variant_results["is_complete"] = False
                    variant_results["is_valid"] = False

            # Apply soft filters
            for filter_obj in self.soft_filters:
                passed, reason = filter_obj.apply(variant)
                variant_results["filters"][filter_obj.name] = {
                    "passed": passed,
                    "reason": reason,
                }

            results[variant.id] = variant_results

        return results

    def _prepare_filtered_records(
        self,
        variants: List[MergedVariant],
        filter_results: Dict[int, Dict],
    ) -> List[Dict]:
        """
        Prepare filtered variant records for database storage.

        Args:
            variants: List of MergedVariant instances
            filter_results: Filter evaluation results

        Returns:
            List of FilteredVariant records ready for insertion
        """
        records = []

        for variant in variants:
            eval_result = filter_results.get(variant.id, {})

            record = {
                "file_id": variant.file_id,
                "chromosome": variant.chromosome,
                "position": variant.position,
                "ref_allele": variant.ref_allele,
                "alt_allele": variant.alt_allele,
                "gen_pos": variant.gen_pos,
                "is_complete": eval_result.get("is_complete", False),
                "is_valid": eval_result.get("is_valid", False),
                "filter_results": json.dumps(eval_result.get("filters", {})),
                "source_variant_id": None,  # Link if needed
                "merged_variant_id": variant.id,  # Link to source merged variant
                "filter_timestamp": datetime.utcnow(),
                "filter_version": self.FILTER_VERSION,
            }

            records.append(record)

        return records

    def _calculate_statistics(self, filter_results: Dict[int, Dict]) -> Dict:
        """
        Calculate filtering statistics.

        Args:
            filter_results: Filter evaluation results

        Returns:
            Dictionary with statistics
        """
        total = len(filter_results)
        valid_count = sum(1 for r in filter_results.values() if r["is_valid"])
        complete_count = sum(1 for r in filter_results.values() if r["is_complete"])
        invalid_count = total - valid_count

        # Count by individual filter
        by_filter = {}
        for filter_obj in self.all_filters:
            passed = sum(
                1
                for r in filter_results.values()
                if r["filters"].get(filter_obj.name, {}).get("passed", False)
            )
            by_filter[filter_obj.name] = {
                "passed": passed,
                "failed": total - passed,
                "description": filter_obj.description,
                "critical": filter_obj.is_critical,
            }

        return {
            "total_count": total,
            "valid_count": valid_count,
            "complete_count": complete_count,
            "invalid_count": invalid_count,
            "by_filter": by_filter,
        }

    def get_filtering_history(self, file_id: int) -> List[Dict]:
        """
        Get filtering operation history for a file.

        Args:
            file_id: File ID

        Returns:
            List of filtering operation records
        """
        audits = self.workflow_audit_repo.find_by_operation(file_id, "filter")
        return [audit.to_dict() for audit in audits]

    def get_quality_summary(self, file_id: int) -> Dict:
        """
        Get quality summary for filtered variants.

        Args:
            file_id: File ID

        Returns:
            Quality summary statistics
        """
        counts = self.filtered_variant_repo.count_by_validity(file_id)

        return {
            "total": counts["total"],
            "valid": counts["valid"],
            "invalid": counts["invalid"],
            "complete": counts["complete"],
            "quality_rate": (
                (counts["valid"] / counts["total"] * 100)
                if counts["total"] > 0
                else 0
            ),
        }

    def refilter_with_version(
        self,
        file_id: int,
        new_version: str,
        user_id: Optional[str] = None,
    ) -> FilterResult:
        """
        Re-apply filters with new version (supports versioning of filter rules).

        Args:
            file_id: File ID
            new_version: New filter version to use
            user_id: User performing filtering

        Returns:
            FilterResult from filtering operation
        """
        # Update filter version
        old_version = self.FILTER_VERSION
        self.FILTER_VERSION = new_version

        try:
            result = self.apply_filters(file_id, user_id)
            return result
        finally:
            # Restore old version
            self.FILTER_VERSION = old_version
