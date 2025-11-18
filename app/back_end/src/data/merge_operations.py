"""
Merge Operations Handler

Manages variant merge operations with complete database storage, tracking,
and audit trail. Supports merging variants from multiple sources (ClinVar,
LOVD, gnomAD, custom) with source attribution and merge history.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from src.database.config import get_db_session
from src.models import File, MergedVariant, SourceVariant, WorkflowAudit
from src.database.repositories import (
    MergedVariantRepository,
    SourceVariantRepository,
    WorkflowAuditRepository,
)

logger = logging.getLogger(__name__)


class MergeResult:
    """Data structure representing merge operation results."""

    def __init__(
        self,
        merged_count: int,
        duplicate_count: int,
        duration_seconds: float,
        total_input: Optional[int] = None,
        strategy_applied: Optional[str] = None,
        source_counts: Optional[Dict[str, int]] = None,
        merge_strategy: Optional[str] = None,
    ):
        """
        Initialize merge result.

        Args:
            merged_count: Total number of unique merged variants
            duplicate_count: Number of duplicates identified
            duration_seconds: Time taken for merge operation
            total_input: Total input variants before merge
            strategy_applied: Name of strategy applied
            source_counts: Count of variants from each source (optional, for backward compatibility)
            merge_strategy: Strategy used (optional, for backward compatibility)
        """
        self.merged_count = merged_count
        self.duplicate_count = duplicate_count
        self.duration_seconds = duration_seconds
        self.timestamp = datetime.utcnow()
        self.total_input = total_input if total_input is not None else 0
        self.strategy_applied = strategy_applied or merge_strategy or ""
        self.source_counts = source_counts or {}
        self.merge_strategy = merge_strategy or strategy_applied or ""

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "merged_count": self.merged_count,
            "source_counts": self.source_counts,
            "duplicate_count": self.duplicate_count,
            "merge_strategy": self.merge_strategy,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
            "total_input": self.total_input,
            "strategy_applied": self.strategy_applied,
        }


class MergeStrategy:
    """Merge strategy implementations."""

    # Strategy: OUTER_UNION - Include all variants from all sources
    # Keeps variants even if they appear in only one source
    OUTER_UNION = "outer_union"

    # Strategy: INNER_INTERSECTION - Only include variants in all sources
    # Removes variants that don't appear in every source
    INNER_INTERSECTION = "inner_intersection"

    # Strategy: CONSENSUS - Variants appearing in 2+ sources
    # Filters to high-confidence variants present in multiple sources
    CONSENSUS = "consensus"

    @staticmethod
    def get_all_strategies() -> List[str]:
        """Get list of available merge strategies."""
        return [
            MergeStrategy.OUTER_UNION,
            MergeStrategy.INNER_INTERSECTION,
            MergeStrategy.CONSENSUS,
        ]


class MergeOperationHandler:
    """Manages variant merge operations with database storage."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize merge operation handler.

        Args:
            session: SQLAlchemy session. If None, uses get_db_session()
        """
        self.session = session or get_db_session()
        self.source_variant_repo = SourceVariantRepository(session)
        self.merged_variant_repo = MergedVariantRepository(session)
        self.workflow_audit_repo = WorkflowAuditRepository(session)

    def perform_merge(
        self,
        file_id: int,
        sources: List[str],
        merge_strategy: str = MergeStrategy.OUTER_UNION,
        user_id: Optional[str] = None,
    ) -> MergeResult:
        """
        Perform merge operation on source variants.

        Args:
            file_id: File ID containing source variants
            sources: List of source databases to merge (["clinvar"], ["clinvar", "lovd"], etc.)
            merge_strategy: Merge strategy to apply
            user_id: User performing the merge

        Returns:
            MergeResult with operation details

        Raises:
            ValueError: If invalid strategy or no sources specified
        """
        start_time = datetime.utcnow()

        if not sources:
            raise ValueError("Must specify at least one source database")

        if merge_strategy not in MergeStrategy.get_all_strategies():
            raise ValueError(f"Invalid merge strategy: {merge_strategy}")

        # Create workflow audit entry
        audit = self.workflow_audit_repo.create(
            file_id=file_id,
            operation="merge",
            operation_stage="combining_sources",
            status="pending",
            user_id=user_id,
            started_at=start_time,
        )

        try:
            # Get source variants for specified sources
            source_variants = self._get_source_variants(file_id, sources)

            if not source_variants:
                audit.status = "failed"
                audit.error_message = f"No source variants found for sources: {sources}"
                self.session.commit()
                logger.error(f"No source variants found for merge: {sources}")
                raise ValueError(f"No source variants found for sources: {sources}")

            # Count input records by source
            input_counts = self._count_variants_by_source(source_variants, sources)
            total_input = sum(input_counts.values())

            audit.input_count = total_input
            self.session.commit()

            # Perform merge based on strategy
            merged_variants, duplicate_count = self._execute_merge_strategy(
                source_variants, merge_strategy, sources
            )

            # Store merged variants in database
            merged_records = self._prepare_merged_records(
                merged_variants, file_id, sources, merge_strategy
            )

            created_count = self.merged_variant_repo.create_bulk(merged_records)

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Update audit entry
            audit.output_count = created_count
            audit.status = "completed"
            audit.completed_at = datetime.utcnow()
            audit.params = json.dumps(
                {
                    "sources": sources,
                    "merge_strategy": merge_strategy,
                    "input_counts": input_counts,
                }
            )
            audit.results = json.dumps(
                {
                    "merged_count": created_count,
                    "duplicates_removed": duplicate_count,
                    "merge_strategy": merge_strategy,
                }
            )
            self.session.commit()

            result = MergeResult(
                merged_count=created_count,
                duplicate_count=duplicate_count,
                duration_seconds=duration,
                total_input=total_input,
                strategy_applied=merge_strategy,
                source_counts=input_counts,
                merge_strategy=merge_strategy,
            )

            logger.info(
                f"Merge completed: {created_count} variants created from "
                f"{total_input} input records, {duplicate_count} duplicates"
            )

            return result

        except Exception as e:
            # Mark audit as failed
            audit.status = "failed"
            audit.completed_at = datetime.utcnow()
            audit.error_message = str(e)
            self.session.commit()
            logger.error(f"Merge operation failed: {e}")
            raise

    def _get_source_variants(self, file_id: int, sources: List[str]) -> List[SourceVariant]:
        """
        Get source variants for specified sources.

        Args:
            file_id: File ID
            sources: List of source database names

        Returns:
            List of SourceVariant instances
        """
        variants = []
        for source in sources:
            source_variants = self.source_variant_repo.find_by_file(file_id, source)
            variants.extend(source_variants)

        return variants

    def _count_variants_by_source(
        self, variants: List[SourceVariant], sources: List[str]
    ) -> Dict[str, int]:
        """
        Count variants by source database.

        Args:
            variants: List of SourceVariant instances
            sources: List of source names (for completeness)

        Returns:
            Dictionary mapping source to count
        """
        counts = {source: 0 for source in sources}
        for variant in variants:
            if variant.source_database in counts:
                counts[variant.source_database] += 1
        return counts

    def _execute_merge_strategy(
        self,
        variants: List[SourceVariant],
        strategy: str,
        sources: List[str],
    ) -> Tuple[List[Dict], int]:
        """
        Execute merge strategy on source variants.

        Args:
            variants: List of source variants
            strategy: Merge strategy to apply
            sources: List of source names

        Returns:
            Tuple of (merged_variants_list, duplicate_count)
        """
        # Group variants by genomic position
        position_map: Dict[str, List[SourceVariant]] = {}

        for variant in variants:
            key = variant.gen_pos
            if key not in position_map:
                position_map[key] = []
            position_map[key].append(variant)

        # Apply merge strategy
        merged = []
        duplicates = 0

        if strategy == MergeStrategy.OUTER_UNION:
            # Include all variants from all sources
            for gen_pos, pos_variants in position_map.items():
                merged_dict = self._combine_variants_outer(pos_variants, sources)
                merged.append(merged_dict)
                # Count variants beyond first as duplicates
                duplicates += len(pos_variants) - 1

        elif strategy == MergeStrategy.INNER_INTERSECTION:
            # Only include variants in all sources
            for gen_pos, pos_variants in position_map.items():
                source_set = {v.source_database for v in pos_variants}
                if source_set == set(sources):
                    merged_dict = self._combine_variants_outer(pos_variants, sources)
                    merged.append(merged_dict)
                else:
                    duplicates += len(pos_variants)

        elif strategy == MergeStrategy.CONSENSUS:
            # Include variants in 2+ sources
            for gen_pos, pos_variants in position_map.items():
                if len(pos_variants) >= 2:
                    merged_dict = self._combine_variants_outer(pos_variants, sources)
                    merged.append(merged_dict)
                    duplicates += len(pos_variants) - 1
                else:
                    duplicates += 1

        return merged, duplicates

    def _combine_variants_outer(
        self, variants: List[SourceVariant], sources: List[str]
    ) -> Dict:
        """
        Combine variants from multiple sources into one merged record.

        Args:
            variants: List of SourceVariant instances at same position
            sources: List of source names

        Returns:
            Dictionary representation of merged variant
        """
        # Use first variant as template
        template = variants[0]

        # Collect source data
        source_data = {}
        source_databases = []

        for variant in variants:
            source_databases.append(variant.source_database)
            if variant.source_data:
                try:
                    source_data[variant.source_database] = json.loads(variant.source_data)
                except json.JSONDecodeError:
                    source_data[variant.source_database] = {}
            else:
                source_data[variant.source_database] = {}

        # Merge gene annotations (take first non-null value)
        gene = None
        transcript = None
        consequence = None

        for variant in variants:
            if not gene and variant.gene:
                gene = variant.gene
            if not transcript and variant.transcript:
                transcript = variant.transcript
            if not consequence and variant.consequence:
                consequence = variant.consequence

        # Create merged variant record
        merged_record = {
            "file_id": template.file_id,
            "chromosome": template.chromosome,
            "position": template.position,
            "ref_allele": template.ref_allele,
            "alt_allele": template.alt_allele,
            "gen_pos": template.gen_pos,
            "gene": gene,
            "transcript": transcript,
            "consequence": consequence,
            "source_databases": json.dumps(sorted(list(set(source_databases)))),
            "merge_timestamp": datetime.utcnow(),
            "merge_strategy": "outer_union",
        }

        # Store source-specific data
        for source in sources:
            if source == "clinvar":
                merged_record["clinvar_data"] = json.dumps(source_data.get("clinvar", {}))
            elif source == "lovd":
                merged_record["lovd_data"] = json.dumps(source_data.get("lovd", {}))
            elif source == "gnomad":
                merged_record["gnomad_data"] = json.dumps(source_data.get("gnomad", {}))

        return merged_record

    def _prepare_merged_records(
        self,
        variants: List[Dict],
        file_id: int,
        sources: List[str],
        merge_strategy: str,
    ) -> List[Dict]:
        """
        Prepare merged variant records for database insertion.

        Args:
            variants: List of merged variant dictionaries
            file_id: File ID
            sources: Source databases used
            merge_strategy: Merge strategy applied

        Returns:
            List of prepared records ready for insertion
        """
        prepared = []

        for variant in variants:
            record = {
                "file_id": file_id,
                "chromosome": variant.get("chromosome"),
                "position": variant.get("position"),
                "ref_allele": variant.get("ref_allele"),
                "alt_allele": variant.get("alt_allele"),
                "gen_pos": variant.get("gen_pos"),
                "gene": variant.get("gene"),
                "transcript": variant.get("transcript"),
                "consequence": variant.get("consequence"),
                "source_databases": variant.get("source_databases", json.dumps(sources)),
                "clinvar_data": variant.get("clinvar_data"),
                "lovd_data": variant.get("lovd_data"),
                "gnomad_data": variant.get("gnomad_data"),
                "merge_timestamp": datetime.utcnow(),
                "merge_strategy": merge_strategy,
            }
            prepared.append(record)

        return prepared

    def get_merge_history(self, file_id: int) -> List[Dict]:
        """
        Get merge operation history for a file.

        Args:
            file_id: File ID

        Returns:
            List of merge operation records
        """
        audits = self.workflow_audit_repo.find_by_operation(file_id, "merge")
        return [audit.to_dict() for audit in audits]

    def get_latest_merge(self, file_id: int) -> Optional[Dict]:
        """
        Get the most recent merge operation for a file.

        Args:
            file_id: File ID

        Returns:
            Latest merge operation record or None
        """
        audit = self.workflow_audit_repo.get_latest_by_operation(file_id, "merge")
        return audit.to_dict() if audit else None

    def get_merge_statistics(self, file_id: int) -> Dict:
        """
        Get comprehensive merge statistics for a file.

        Args:
            file_id: File ID

        Returns:
            Dictionary with merge statistics
        """
        merges = self.workflow_audit_repo.find_by_operation(file_id, "merge")
        merged_variants = self.merged_variant_repo.find_by_file(file_id)

        if not merged_variants:
            return {
                "total_merged_variants": 0,
                "merge_operations": 0,
                "last_merge": None,
                "sources_combined": [],
            }

        # Get unique sources from merged variants
        all_sources = set()
        for variant in merged_variants:
            sources = variant.source_list
            all_sources.update(sources)

        return {
            "total_merged_variants": len(merged_variants),
            "merge_operations": len(merges),
            "last_merge": merges[0].to_dict() if merges else None,
            "sources_combined": sorted(list(all_sources)),
        }

    def validate_merge_inputs(self, file_id: int, sources: List[str]) -> Tuple[bool, str]:
        """
        Validate merge inputs before performing merge.

        Args:
            file_id: File ID
            sources: List of source databases

        Returns:
            Tuple of (is_valid, error_message)

        Raises:
            ValueError: If sources list is empty
        """
        if not sources:
            raise ValueError("Must specify at least one source database")

        # Check if source variants exist
        source_counts = self.source_variant_repo.count_by_source(file_id)

        for source in sources:
            if source not in source_counts or source_counts[source] == 0:
                return False, f"No data found for source: {source}"

        return True, ""
