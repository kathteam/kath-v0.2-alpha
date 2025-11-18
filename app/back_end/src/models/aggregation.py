"""
Aggregation Model

Represents cached aggregation results for performance optimization.
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from .base import Base


class Aggregation(Base):
    """
    Aggregation model for caching computed aggregations.

    Attributes:
        id (int): Auto-incrementing aggregation ID
        file_id (int): File being aggregated
        column_name (str): Column name being aggregated
        operation (str): Aggregation operation (SUM, AVG, MIN, MAX, COUNT)
        filter_json (str): JSON representation of applied filters
        result_value (float): Cached aggregation result
        cached_at (datetime): When cache was created
        expires_at (datetime): Cache expiration time
        file (relationship): Parent file
    """

    __tablename__ = "aggregations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(255), nullable=False, comment="Column being aggregated")
    operation = Column(String(10), nullable=False, comment="SUM, AVG, MIN, MAX, COUNT")
    filter_json = Column(Text, nullable=True, comment="JSON of applied filters")
    result_value = Column(Float, nullable=False, comment="Aggregation result")
    cached_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=True, comment="Cache expiration")

    # Relationships
    file = relationship("File", back_populates="aggregations")

    # Unique constraint on file + column + operation + filters
    __table_args__ = (
        UniqueConstraint("file_id", "column_name", "operation", "filter_json", name="uq_aggregation_key"),
        Index("idx_aggregations_file_column", "file_id", "column_name"),
        Index("idx_aggregations_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<Aggregation(id={self.id}, operation='{self.operation}', column='{self.column_name}', value={self.result_value})>"

    @property
    def filters(self):
        """Parse filter JSON to dictionary."""
        if self.filter_json:
            try:
                return json.loads(self.filter_json)
            except json.JSONDecodeError:
                return {}
        return {}

    @filters.setter
    def filters(self, value):
        """Set filters from dictionary."""
        if value:
            # Sort keys for consistent cache keys
            sorted_value = {k: value[k] for k in sorted(value.keys())}
            self.filter_json = json.dumps(sorted_value)
        else:
            self.filter_json = None

    @property
    def is_expired(self):
        """Check if cache has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def set_expiration(self, hours=24):
        """Set cache expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)

    def to_dict(self):
        """Convert aggregation to dictionary representation."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "column_name": self.column_name,
            "operation": self.operation,
            "filters": self.filters,
            "result_value": self.result_value,
            "cached_at": self.cached_at.isoformat() if self.cached_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
        }

    @classmethod
    def get_or_compute(cls, session, file_id, column_name, operation, filters=None, compute_fn=None):
        """
        Get cached aggregation or compute if not found/expired.

        Args:
            session: Database session
            file_id (int): File ID
            column_name (str): Column to aggregate
            operation (str): Aggregation operation
            filters (dict): Optional filters
            compute_fn (callable): Function to compute aggregation if cache miss

        Returns:
            Aggregation: Cached or newly computed aggregation
        """
        # Build filter JSON for lookup
        filter_json = None
        if filters:
            sorted_filters = {k: filters[k] for k in sorted(filters.keys())}
            filter_json = json.dumps(sorted_filters)

        # Try to find existing aggregation
        aggregation = (
            session.query(cls)
            .filter_by(file_id=file_id, column_name=column_name, operation=operation, filter_json=filter_json)
            .first()
        )

        # If found and not expired, return it
        if aggregation and not aggregation.is_expired:
            return aggregation

        # Otherwise, compute new value
        if compute_fn is None:
            raise ValueError("compute_fn required for cache miss")

        result_value = compute_fn()

        # Create or update aggregation
        if aggregation:
            aggregation.result_value = result_value
            aggregation.cached_at = datetime.utcnow()
            aggregation.set_expiration()
        else:
            aggregation = cls(
                file_id=file_id,
                column_name=column_name,
                operation=operation,
                filter_json=filter_json,
                result_value=result_value,
            )
            aggregation.set_expiration()
            session.add(aggregation)

        session.commit()
        return aggregation

    @classmethod
    def invalidate_file_cache(cls, session, file_id):
        """
        Invalidate all cached aggregations for a file.

        Args:
            session: Database session
            file_id (int): File ID
        """
        session.query(cls).filter_by(file_id=file_id).delete()
        session.commit()

    @classmethod
    def cleanup_expired(cls, session):
        """
        Remove all expired aggregations.

        Args:
            session: Database session

        Returns:
            int: Number of deleted aggregations
        """
        count = session.query(cls).filter(cls.expires_at < datetime.utcnow()).delete()
        session.commit()
        return count
