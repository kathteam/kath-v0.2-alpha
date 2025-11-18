"""
Query profiling and performance monitoring utilities.

Provides decorators and tools for measuring database query performance.
"""

import functools
import time
from typing import Callable, Optional

from src.setup.extensions import logger


class QueryProfiler:
    """
    Profiler for tracking query performance.

    Collects statistics on query execution times and counts.
    """

    def __init__(self):
        """Initialize profiler."""
        self._stats = {}

    def record(self, query_name: str, duration: float):
        """
        Record query execution.

        Args:
            query_name: Name of the query
            duration: Execution time in seconds
        """
        if query_name not in self._stats:
            self._stats[query_name] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
            }

        stats = self._stats[query_name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)

    def get_stats(self, sort_by: str = "total_time") -> list:
        """
        Get query statistics.

        Args:
            sort_by: Sort key (total_time, count, avg_time)

        Returns:
            List of query statistics
        """
        results = []

        for query_name, stats in self._stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0

            results.append(
                {
                    "query": query_name,
                    "count": stats["count"],
                    "total_time": stats["total_time"],
                    "avg_time": avg_time,
                    "min_time": stats["min_time"],
                    "max_time": stats["max_time"],
                }
            )

        # Sort results
        if sort_by == "count":
            results.sort(key=lambda x: x["count"], reverse=True)
        elif sort_by == "avg_time":
            results.sort(key=lambda x: x["avg_time"], reverse=True)
        else:  # total_time
            results.sort(key=lambda x: x["total_time"], reverse=True)

        return results

    def reset(self):
        """Reset all statistics."""
        self._stats.clear()

    def print_stats(self, top_n: int = 10):
        """
        Print query statistics.

        Args:
            top_n: Number of top queries to print
        """
        stats = self.get_stats()

        print("\n" + "=" * 80)
        print("Query Performance Statistics")
        print("=" * 80)
        print(f"{'Query':<30} {'Count':>8} {'Total(s)':>10} {'Avg(ms)':>10} {'Min(ms)':>10} {'Max(ms)':>10}")
        print("-" * 80)

        for stat in stats[:top_n]:
            print(
                f"{stat['query']:<30} "
                f"{stat['count']:>8} "
                f"{stat['total_time']:>10.3f} "
                f"{stat['avg_time']*1000:>10.2f} "
                f"{stat['min_time']*1000:>10.2f} "
                f"{stat['max_time']*1000:>10.2f}"
            )

        print("=" * 80 + "\n")


# Global profiler instance
_profiler = QueryProfiler()


def profile_query(query_name: Optional[str] = None, log_slow: float = 1.0):
    """
    Decorator to profile query execution time.

    Args:
        query_name: Name for the query (default: function name)
        log_slow: Log warning if query takes longer than this (seconds)

    Usage:
        @profile_query(log_slow=0.5)
        def my_query():
            return db.query(...)
    """

    def decorator(func: Callable) -> Callable:
        nonlocal query_name
        if query_name is None:
            query_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time

                # Record statistics
                _profiler.record(query_name, duration)

                # Log slow queries
                if duration > log_slow:
                    logger.warning(
                        f"Slow query detected: {query_name} took {duration*1000:.2f}ms "
                        f"(threshold: {log_slow*1000:.0f}ms)"
                    )
                else:
                    logger.debug(f"Query {query_name} completed in {duration*1000:.2f}ms")

        return wrapper

    return decorator


def get_query_stats(sort_by: str = "total_time", top_n: Optional[int] = None) -> list:
    """
    Get query performance statistics.

    Args:
        sort_by: Sort key (total_time, count, avg_time)
        top_n: Return only top N queries (None = all)

    Returns:
        List of query statistics
    """
    stats = _profiler.get_stats(sort_by=sort_by)
    return stats[:top_n] if top_n else stats


def print_query_stats(top_n: int = 10):
    """
    Print query performance statistics to stdout.

    Args:
        top_n: Number of top queries to print
    """
    _profiler.print_stats(top_n=top_n)


def reset_query_stats():
    """Reset all query statistics."""
    _profiler.reset()
    logger.info("Query profiler reset")
