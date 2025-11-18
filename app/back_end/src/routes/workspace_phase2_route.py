"""
Phase 2 API Routes

Comprehensive REST API endpoints for Phase 2 database-driven pipeline operations
including merge, filtering, analysis, and data queries with full audit trails.
"""

import json
from flask import Blueprint, jsonify, request
from src.constants import (
    CONSOLE_FEEDBACK_EVENT,
    WORKSPACE_UPDATE_FEEDBACK_EVENT,
)
from src.setup.extensions import logger
from src.utils.helpers import socketio_emit_to_user_session
from src.data.delta_sync import DeltaSyncManager
from src.data.merge_operations import MergeOperationHandler, MergeStrategy
from src.data.quality_filtering import QualityFilteringEngine
from src.data.analysis_integration import AnalysisIntegrationHandler, AnalysisToolConfig
from src.database.repositories import (
    SourceVariantRepository,
    MergedVariantRepository,
    FilteredVariantRepository,
    WorkflowAuditRepository,
)

workspace_phase2_route_bp = Blueprint("workspace_phase2_route", __name__)

# Constants
WORKSPACE_PHASE2_ROUTE = "/workspace_phase2"


# ============================================================================
# Delta-Sync Endpoints
# ============================================================================

@workspace_phase2_route_bp.route("/delta-sync/status/<path:relative_path>", methods=["GET"])
def get_delta_sync_status(relative_path):
    """Get delta-sync status for a file."""
    try:
        uuid = request.headers.get("uuid")
        if not uuid:
            return jsonify({"error": "UUID header required"}), 400

        source = request.args.get("source")
        if not source:
            return jsonify({"error": "source parameter required"}), 400

        sync_mgr = DeltaSyncManager()
        # In production, would get file_id from path
        file_id = 1  # Placeholder

        status = sync_mgr.check_sync_status(uuid, file_id, source)

        return jsonify({
            "status": "success",
            "data": status.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error checking delta-sync status: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/delta-sync/statistics/<path:workspace_id>", methods=["GET"])
def get_delta_sync_statistics(workspace_id):
    """Get comprehensive delta-sync statistics for workspace."""
    try:
        sync_mgr = DeltaSyncManager()
        stats = sync_mgr.get_sync_statistics(workspace_id)

        return jsonify({
            "status": "success",
            "data": stats
        }), 200

    except Exception as e:
        logger.error(f"Error getting delta-sync statistics: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Merge Endpoints
# ============================================================================

@workspace_phase2_route_bp.route("/merge/strategies", methods=["GET"])
def get_merge_strategies():
    """Get available merge strategies."""
    try:
        strategies = MergeStrategy.get_all_strategies()
        descriptions = {
            "outer_union": "Include all variants from all sources",
            "inner_intersection": "Only variants in all sources",
            "consensus": "Variants appearing in 2+ sources"
        }

        return jsonify({
            "status": "success",
            "strategies": [
                {"name": s, "description": descriptions.get(s, "")}
                for s in strategies
            ]
        }), 200

    except Exception as e:
        logger.error(f"Error getting merge strategies: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/merge/perform", methods=["POST"])
def perform_merge():
    """Perform merge operation on source variants."""
    try:
        uuid = request.headers.get("uuid")
        sid = request.headers.get("sid")
        if not uuid or not sid:
            return jsonify({"error": "UUID and SID headers required"}), 400

        try:
            data = request.get_json(force=False, silent=False)
        except Exception as json_error:
            return jsonify({"error": f"Invalid or missing JSON body: {str(json_error)}"}), 400

        if data is None:
            return jsonify({"error": "Invalid or missing JSON body"}), 400
        file_id = data.get("file_id")
        sources = data.get("sources", [])
        strategy = data.get("strategy", MergeStrategy.OUTER_UNION)

        if not file_id or not sources:
            return jsonify({"error": "file_id and sources required"}), 400

        handler = MergeOperationHandler()

        # Validate inputs
        is_valid, error_msg = handler.validate_merge_inputs(file_id, sources)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Perform merge
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "info",
                "message": f"Starting merge of {sources} using {strategy} strategy..."
            },
            uuid, sid
        )

        result = handler.perform_merge(
            file_id=file_id,
            sources=sources,
            merge_strategy=strategy,
            user_id=uuid
        )

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"Merge completed: {result.merged_count} variants created"
            },
            uuid, sid
        )

        return jsonify({
            "status": "success",
            "result": result.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error performing merge: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/merge/history/<int:file_id>", methods=["GET"])
def get_merge_history(file_id):
    """Get merge operation history for a file."""
    try:
        handler = MergeOperationHandler()
        history = handler.get_merge_history(file_id)

        return jsonify({
            "status": "success",
            "data": history
        }), 200

    except Exception as e:
        logger.error(f"Error getting merge history: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/merge/statistics/<int:file_id>", methods=["GET"])
def get_merge_statistics(file_id):
    """Get merge statistics for a file."""
    try:
        handler = MergeOperationHandler()
        stats = handler.get_merge_statistics(file_id)

        return jsonify({
            "status": "success",
            "data": stats
        }), 200

    except Exception as e:
        logger.error(f"Error getting merge statistics: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Filtering Endpoints
# ============================================================================

@workspace_phase2_route_bp.route("/filter/apply", methods=["POST"])
def apply_quality_filters():
    """Apply quality filters to merged variants."""
    try:
        uuid = request.headers.get("uuid")
        sid = request.headers.get("sid")
        if not uuid or not sid:
            return jsonify({"error": "UUID and SID headers required"}), 400

        data = request.get_json()
        file_id = data.get("file_id")

        if not file_id:
            return jsonify({"error": "file_id required"}), 400

        engine = QualityFilteringEngine()

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {"type": "info", "message": "Applying quality filters..."},
            uuid, sid
        )

        result = engine.apply_filters(file_id=file_id, user_id=uuid)

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"Filtering complete: {result.valid_variants} valid variants"
            },
            uuid, sid
        )

        return jsonify({
            "status": "success",
            "result": result.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error applying filters: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/filter/quality-summary/<int:file_id>", methods=["GET"])
def get_quality_summary(file_id):
    """Get quality summary for filtered variants."""
    try:
        engine = QualityFilteringEngine()
        summary = engine.get_quality_summary(file_id)

        return jsonify({
            "status": "success",
            "data": summary
        }), 200

    except Exception as e:
        logger.error(f"Error getting quality summary: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/filter/history/<int:file_id>", methods=["GET"])
def get_filtering_history(file_id):
    """Get filtering operation history."""
    try:
        engine = QualityFilteringEngine()
        history = engine.get_filtering_history(file_id)

        return jsonify({
            "status": "success",
            "data": history
        }), 200

    except Exception as e:
        logger.error(f"Error getting filtering history: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Analysis Endpoints
# ============================================================================

@workspace_phase2_route_bp.route("/analysis/tools", methods=["GET"])
def get_analysis_tools():
    """Get available analysis tools and their configurations."""
    try:
        tools = AnalysisToolConfig.get_all_tools()
        tool_info = {}

        for tool in tools:
            score_range = AnalysisToolConfig.SCORE_RANGES[tool]
            threshold = AnalysisToolConfig.PATHOGENICITY_THRESHOLDS[tool]

            tool_info[tool] = {
                "name": tool.upper(),
                "description": score_range["description"],
                "score_range": score_range,
                "pathogenicity_threshold": threshold
            }

        return jsonify({
            "status": "success",
            "tools": tool_info
        }), 200

    except Exception as e:
        logger.error(f"Error getting analysis tools: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/analysis/variant-scores/<int:variant_id>", methods=["GET"])
def get_variant_scores(variant_id):
    """Get all analysis scores for a variant."""
    try:
        handler = AnalysisIntegrationHandler()
        scores = handler.get_variant_scores(variant_id)

        return jsonify({
            "status": "success",
            "variant_id": variant_id,
            "scores": scores
        }), 200

    except Exception as e:
        logger.error(f"Error getting variant scores: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/analysis/pathogenic/<int:file_id>", methods=["GET"])
def get_pathogenic_variants(file_id):
    """Get variants flagged as pathogenic by analysis tools."""
    try:
        handler = AnalysisIntegrationHandler()
        variants = handler.get_pathogenic_variants(file_id)

        return jsonify({
            "status": "success",
            "count": len(variants),
            "variants": variants
        }), 200

    except Exception as e:
        logger.error(f"Error getting pathogenic variants: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/analysis/statistics/<int:file_id>", methods=["GET"])
def get_analysis_statistics(file_id):
    """Get analysis statistics for a file."""
    try:
        handler = AnalysisIntegrationHandler()
        stats = handler.get_analysis_statistics(file_id)

        return jsonify({
            "status": "success",
            "data": stats
        }), 200

    except Exception as e:
        logger.error(f"Error getting analysis statistics: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Data Query Endpoints
# ============================================================================

@workspace_phase2_route_bp.route("/variants/source/<int:file_id>", methods=["GET"])
def get_source_variants(file_id):
    """Get source variants for a file."""
    try:
        repo = SourceVariantRepository()
        source = request.args.get("source")
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        if source:
            variants = repo.find_by_file(file_id, source)
        else:
            variants = repo.find_by_file(file_id)

        # Apply pagination
        variants = variants[offset:offset+limit]

        return jsonify({
            "status": "success",
            "count": len(variants),
            "data": [v.to_dict() for v in variants]
        }), 200

    except Exception as e:
        logger.error(f"Error getting source variants: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/variants/merged/<int:file_id>", methods=["GET"])
def get_merged_variants(file_id):
    """Get merged variants for a file."""
    try:
        repo = MergedVariantRepository()
        gene = request.args.get("gene")
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        if gene:
            variants = repo.find_by_gene(file_id, gene)
        else:
            variants = repo.find_by_file(file_id)

        variants = variants[offset:offset+limit]

        return jsonify({
            "status": "success",
            "count": len(variants),
            "data": [v.to_dict() for v in variants]
        }), 200

    except Exception as e:
        logger.error(f"Error getting merged variants: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/variants/filtered/<int:file_id>", methods=["GET"])
def get_filtered_variants(file_id):
    """Get filtered variants with optional validity filter."""
    try:
        repo = FilteredVariantRepository()
        valid_only = request.args.get("valid_only", False, type=bool)
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        variants = repo.find_by_file(file_id, valid_only=valid_only)
        variants = variants[offset:offset+limit]

        return jsonify({
            "status": "success",
            "count": len(variants),
            "data": [v.to_dict() for v in variants]
        }), 200

    except Exception as e:
        logger.error(f"Error getting filtered variants: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Audit Trail Endpoints
# ============================================================================

@workspace_phase2_route_bp.route("/audit/file/<int:file_id>", methods=["GET"])
def get_file_audit_trail(file_id):
    """Get complete audit trail for a file."""
    try:
        repo = WorkflowAuditRepository()
        audits = repo.find_by_file(file_id)

        return jsonify({
            "status": "success",
            "count": len(audits),
            "data": [a.to_dict() for a in audits]
        }), 200

    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_phase2_route_bp.route("/audit/operation/<int:file_id>/<operation>", methods=["GET"])
def get_operation_audits(file_id, operation):
    """Get audits for specific operation type."""
    try:
        repo = WorkflowAuditRepository()
        audits = repo.find_by_operation(file_id, operation)

        return jsonify({
            "status": "success",
            "operation": operation,
            "count": len(audits),
            "data": [a.to_dict() for a in audits]
        }), 200

    except Exception as e:
        logger.error(f"Error getting operation audits: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Health/Status Endpoint
# ============================================================================

@workspace_phase2_route_bp.route("/health", methods=["GET"])
def phase2_health():
    """Check Phase 2 system health."""
    try:
        return jsonify({
            "status": "healthy",
            "version": "2.0",
            "components": {
                "delta_sync": "available",
                "merge": "available",
                "filtering": "available",
                "analysis": "available"
            }
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
