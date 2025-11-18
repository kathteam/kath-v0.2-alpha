"""
Analysis Tool Integration Layer

Bridges external analysis tools (CADD, REVEL, SpliceAI) with database storage,
enabling seamless integration of variant scoring and annotation results into
the Phase 2 pipeline with complete tracking and audit trails.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

from sqlalchemy.orm import Session

from src.database.config import get_db_session
from src.models import Annotation, FilteredVariant, Variant, WorkflowAudit
from src.database.repositories import (
    VariantRepository,
    WorkflowAuditRepository,
)

logger = logging.getLogger(__name__)


class AnalysisToolConfig:
    """Configuration for analysis tools."""

    # Tool definitions
    CADD = "cadd"
    REVEL = "revel"
    SPLICEAI = "spliceai"

    # Default score ranges
    SCORE_RANGES = {
        CADD: {"min": 0, "max": 100, "description": "CADD score (higher = more deleterious)"},
        REVEL: {"min": 0, "max": 1, "description": "REVEL score (higher = more deleterious)"},
        SPLICEAI: {"min": 0, "max": 1, "description": "SpliceAI max score (higher = more impact)"},
    }

    # Default thresholds for pathogenicity
    PATHOGENICITY_THRESHOLDS = {
        CADD: 20,      # CADD >20 considered likely damaging
        REVEL: 0.5,    # REVEL >0.5 considered deleterious
        SPLICEAI: 0.2, # SpliceAI >0.2 considered potentially damaging
    }

    @staticmethod
    def get_all_tools() -> List[str]:
        """Get list of available tools."""
        return [AnalysisToolConfig.CADD, AnalysisToolConfig.REVEL, AnalysisToolConfig.SPLICEAI]

    @staticmethod
    def is_pathogenic(tool: str, score: float) -> bool:
        """
        Determine if variant is pathogenic based on tool score.

        Args:
            tool: Tool name
            score: Score from tool

        Returns:
            True if score indicates pathogenic variant
        """
        if tool not in AnalysisToolConfig.PATHOGENICITY_THRESHOLDS:
            return False

        threshold = AnalysisToolConfig.PATHOGENICITY_THRESHOLDS[tool]
        return score >= threshold


class AnalysisResult:
    """Data structure for analysis result."""

    def __init__(
        self,
        variant_id: int,
        tool: str,
        score: float,
        raw_output: Dict[str, Any],
        timestamp: datetime,
    ):
        """
        Initialize analysis result.

        Args:
            variant_id: ID of analyzed variant
            tool: Analysis tool name
            score: Primary score from tool
            raw_output: Complete raw output from tool
            timestamp: When analysis was performed
        """
        self.variant_id = variant_id
        self.tool = tool
        self.score = score
        self.raw_output = raw_output
        self.timestamp = timestamp
        self.is_pathogenic = AnalysisToolConfig.is_pathogenic(tool, score)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "variant_id": self.variant_id,
            "tool": self.tool,
            "score": self.score,
            "is_pathogenic": self.is_pathogenic,
            "timestamp": self.timestamp.isoformat(),
            "raw_output": self.raw_output,
        }


class AnalysisIntegrationHandler:
    """Manages integration of external analysis tools with database."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize analysis integration handler.

        Args:
            session: SQLAlchemy session. If None, uses get_db_session()
        """
        self.session = session or get_db_session()
        self.variant_repo = VariantRepository(session)
        self.workflow_audit_repo = WorkflowAuditRepository(session)

    def store_analysis_result(
        self,
        variant_id: int,
        tool: str,
        score: float,
        raw_output: Dict[str, Any],
        file_id: int,
        user_id: Optional[str] = None,
    ) -> Annotation:
        """
        Store analysis result in database.

        Args:
            variant_id: Variant ID being analyzed
            tool: Tool name (cadd, revel, spliceai)
            score: Primary score from tool
            raw_output: Complete output from tool
            file_id: File ID for audit trail
            user_id: User performing analysis

        Returns:
            Created Annotation record
        """
        if tool not in AnalysisToolConfig.get_all_tools():
            raise ValueError(f"Unknown tool: {tool}")

        # Create annotation record
        annotation = Annotation(
            variant_id=variant_id,
            tool=tool,
            score=score,
            result=json.dumps(raw_output),
            created_at=datetime.utcnow(),
        )

        self.session.add(annotation)
        self.session.commit()

        logger.info(
            f"Stored {tool} analysis for variant {variant_id}: score={score:.2f}"
        )

        return annotation

    def bulk_store_analysis_results(
        self,
        results: List[AnalysisResult],
        file_id: int,
        user_id: Optional[str] = None,
    ) -> int:
        """
        Bulk store analysis results for efficiency.

        Args:
            results: List of AnalysisResult instances
            file_id: File ID for audit trail
            user_id: User performing analysis

        Returns:
            Number of results stored
        """
        start_time = datetime.utcnow()

        # Create workflow audit entry
        audit = self.workflow_audit_repo.create(
            file_id=file_id,
            operation="analyze",
            status="pending",
            user_id=user_id,
            started_at=start_time,
            input_count=len(results),
        )

        try:
            # Prepare annotation records
            annotations = []
            for result in results:
                annotation = Annotation(
                    variant_id=result.variant_id,
                    tool=result.tool,
                    score=result.score,
                    result=json.dumps(result.raw_output),
                    created_at=result.timestamp,
                )
                annotations.append(annotation)

            # Bulk insert
            self.session.bulk_save_objects(annotations)
            self.session.commit()

            # Update audit
            audit.output_count = len(results)
            audit.status = "completed"
            audit.completed_at = datetime.utcnow()
            audit.params = json.dumps({
                "tools": list(set(r.tool for r in results)),
                "result_count": len(results),
            })
            self.session.commit()

            logger.info(f"Bulk stored {len(results)} analysis results")
            return len(results)

        except Exception as e:
            audit.status = "failed"
            audit.error_message = str(e)
            audit.completed_at = datetime.utcnow()
            self.session.commit()
            logger.error(f"Failed to store analysis results: {e}")
            raise

    def get_variant_scores(
        self,
        variant_id: int,
        tools: Optional[List[str]] = None,
    ) -> Dict[str, Dict]:
        """
        Get all analysis scores for a variant.

        Args:
            variant_id: Variant ID
            tools: Optional list of tools to retrieve

        Returns:
            Dictionary mapping tool to score and metadata
        """
        query = self.session.query(Annotation).filter_by(variant_id=variant_id)

        if tools:
            query = query.filter(Annotation.tool.in_(tools))

        annotations = query.all()
        results = {}

        for annotation in annotations:
            results[annotation.tool] = {
                "score": annotation.score,
                "is_pathogenic": AnalysisToolConfig.is_pathogenic(
                    annotation.tool, annotation.score
                ),
                "created_at": annotation.created_at.isoformat(),
                "tool": annotation.tool,
            }

        return results

    def get_variants_by_tool_score(
        self,
        file_id: int,
        tool: str,
        min_score: float,
        max_score: Optional[float] = None,
    ) -> List[Tuple[int, float]]:
        """
        Get variants with scores in specified range for a tool.

        Args:
            file_id: File ID
            tool: Tool name
            min_score: Minimum score (inclusive)
            max_score: Maximum score (inclusive), defaults to tool max

        Returns:
            List of (variant_id, score) tuples
        """
        if tool not in AnalysisToolConfig.get_all_tools():
            raise ValueError(f"Unknown tool: {tool}")

        if max_score is None:
            max_score = AnalysisToolConfig.SCORE_RANGES[tool]["max"]

        query = self.session.query(Annotation.variant_id, Annotation.score).filter(
            Annotation.tool_name == tool,
            Annotation.score_value >= min_score,
            Annotation.score_value <= max_score,
        )

        return query.all()

    def get_pathogenic_variants(
        self,
        file_id: int,
        tools: Optional[List[str]] = None,
    ) -> Dict[int, Dict]:
        """
        Get variants flagged as pathogenic by analysis tools.

        Args:
            file_id: File ID
            tools: Optional list of tools to check

        Returns:
            Dictionary mapping variant_id to tool results
        """
        if tools is None:
            tools = AnalysisToolConfig.get_all_tools()

        pathogenic_variants = {}

        for tool in tools:
            threshold = AnalysisToolConfig.PATHOGENICITY_THRESHOLDS[tool]
            annotations = self.session.query(Annotation).filter(
                Annotation.tool_name == tool,
                Annotation.score_value >= threshold,
            )

            for annotation in annotations:
                if annotation.variant_id not in pathogenic_variants:
                    pathogenic_variants[annotation.variant_id] = {}

                pathogenic_variants[annotation.variant_id][tool] = {
                    "score": annotation.score_value,
                    "threshold": threshold,
                }

        return pathogenic_variants

    def get_analysis_statistics(
        self,
        file_id: int,
    ) -> Dict:
        """
        Get analysis statistics for a file.

        Args:
            file_id: File ID

        Returns:
            Dictionary with analysis statistics
        """
        stats = {
            "by_tool": {},
            "pathogenic_counts": {},
            "total_analyses": 0,
        }

        for tool in AnalysisToolConfig.get_all_tools():
            annotations = self.session.query(Annotation).filter_by(tool_name=tool).all()
            count = len(annotations)

            if count == 0:
                continue

            threshold = AnalysisToolConfig.PATHOGENICITY_THRESHOLDS[tool]
            pathogenic_count = sum(
                1 for a in annotations if a.score_value >= threshold
            )

            scores = [a.score_value for a in annotations]
            avg_score = sum(scores) / len(scores) if scores else 0

            stats["by_tool"][tool] = {
                "count": count,
                "pathogenic": pathogenic_count,
                "avg_score": avg_score,
                "min_score": min(scores) if scores else None,
                "max_score": max(scores) if scores else None,
            }

            stats["pathogenic_counts"][tool] = pathogenic_count
            stats["total_analyses"] += count

        return stats

    def create_filtered_variant_from_analysis(
        self,
        filtered_variant_id: int,
        analysis_tools: Optional[List[str]] = None,
        pathogenic_only: bool = False,
    ) -> Optional[Dict]:
        """
        Create analysis summary for filtered variant.

        Args:
            filtered_variant_id: FilteredVariant ID
            analysis_tools: Tools to include
            pathogenic_only: Only include pathogenic results

        Returns:
            Dictionary with analysis summary or None
        """
        # This is a placeholder for integrating filtered variants with analysis
        # In full implementation, would query FilteredVariant and get its annotations

        if analysis_tools is None:
            analysis_tools = AnalysisToolConfig.get_all_tools()

        summary = {
            "tools_applied": analysis_tools,
            "results": {},
        }

        return summary

    def export_analysis_results(
        self,
        file_id: int,
        format: str = "json",
    ) -> str:
        """
        Export analysis results in specified format.

        Args:
            file_id: File ID
            format: Export format (json, csv, tsv)

        Returns:
            Formatted export string
        """
        annotations = self.session.query(Annotation).all()

        if format == "json":
            data = [
                {
                    "variant_id": a.variant_id,
                    "tool": a.tool,
                    "score": a.score,
                    "timestamp": a.created_at.isoformat(),
                }
                for a in annotations
            ]
            return json.dumps(data, indent=2)

        elif format == "csv":
            lines = ["variant_id,tool,score,timestamp"]
            for a in annotations:
                lines.append(
                    f"{a.variant_id},{a.tool},{a.score},{a.created_at.isoformat()}"
                )
            return "\n".join(lines)

        elif format == "tsv":
            lines = ["variant_id\ttool\tscore\ttimestamp"]
            for a in annotations:
                lines.append(
                    f"{a.variant_id}\t{a.tool}\t{a.score}\t{a.created_at.isoformat()}"
                )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown export format: {format}")

    def reanalyze_pathogenic_variants(
        self,
        file_id: int,
        analysis_function,
        user_id: Optional[str] = None,
    ) -> int:
        """
        Reanalyze variants flagged as pathogenic.

        Args:
            file_id: File ID
            analysis_function: Function to call for each variant
            user_id: User performing reanalysis

        Returns:
            Number of variants reanalyzed
        """
        pathogenic = self.get_pathogenic_variants(file_id)
        reanalyzed_count = 0

        for variant_id in pathogenic.keys():
            try:
                # Call analysis function
                result = analysis_function(variant_id)
                if result:
                    reanalyzed_count += 1
            except Exception as e:
                logger.warning(f"Failed to reanalyze variant {variant_id}: {e}")

        logger.info(f"Reanalyzed {reanalyzed_count} pathogenic variants")
        return reanalyzed_count
