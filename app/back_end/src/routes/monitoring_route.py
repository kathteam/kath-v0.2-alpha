"""
Performance monitoring routes.

Provides endpoints for monitoring database query performance and cache statistics.
"""

from typing import Any, Dict

from flask import Blueprint, jsonify

from src.utils.cache import get_cache_stats
from src.utils.profiling import get_query_stats

monitoring_route_bp = Blueprint("monitoring_route", __name__)


@monitoring_route_bp.route("/monitoring/cache-stats", methods=["GET"])
def get_cache_statistics():
    """
    Get cache performance statistics.

    Returns:
        JSON response with cache hits, misses, size, and hit rate
    """
    stats = get_cache_stats()
    return jsonify(stats)


@monitoring_route_bp.route("/monitoring/query-stats", methods=["GET"])
def get_query_statistics():
    """
    Get query performance statistics.

    Query Parameters:
        sort_by: Sort key (total_time, count, avg_time) - default: total_time
        top_n: Number of queries to return - default: 20

    Returns:
        JSON response with query performance metrics
    """
    from flask import request

    sort_by = request.args.get("sort_by", "total_time")
    top_n = int(request.args.get("top_n", 20))

    stats = get_query_stats(sort_by=sort_by, top_n=top_n)

    # Convert times to milliseconds for readability
    for stat in stats:
        stat["total_time_ms"] = stat["total_time"] * 1000
        stat["avg_time_ms"] = stat["avg_time"] * 1000
        stat["min_time_ms"] = stat["min_time"] * 1000
        stat["max_time_ms"] = stat["max_time"] * 1000

    return jsonify({"queries": stats, "total_queries": len(stats)})


@monitoring_route_bp.route("/monitoring/db-stats", methods=["GET"])
def get_database_statistics():
    """
    Get database statistics.

    Returns:
        JSON response with database size, table row counts, etc.
    """
    from sqlalchemy import create_engine, text

    from src.database.config import get_database_uri

    uri = get_database_uri()
    engine = create_engine(uri)

    stats: Dict[str, Any] = {}

    try:
        with engine.connect() as conn:
            # Get table row counts
            tables = ["workspaces", "files", "variants", "annotations", "aggregations"]
            row_counts = {}

            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                row_counts[table] = count

            stats["row_counts"] = row_counts

            # Get database file size (SQLite specific)
            import os

            db_path = uri.replace("sqlite:///", "")
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                size_mb: float = size_bytes / (1024 * 1024)
                stats["database_size_mb"] = round(size_mb, 2)

            # Get index count
            index_count = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")).scalar()
            stats["index_count"] = index_count

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(stats)


@monitoring_route_bp.route("/monitoring/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with health status
    """
    from sqlalchemy import create_engine, text

    from src.database.config import get_database_uri

    uri = get_database_uri()
    engine = create_engine(uri)

    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()

        return jsonify({"status": "healthy", "database": "connected"})

    except Exception as e:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 503
