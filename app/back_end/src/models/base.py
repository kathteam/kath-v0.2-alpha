"""
Base Database Configuration

Provides the base SQLAlchemy configuration for KATH models.
Uses SQLAlchemy Core's declarative base for Alembic compatibility.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, MetaData
from sqlalchemy.orm import declarative_base

# Define naming convention for constraints
# This ensures consistent naming across migrations
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)

# Create declarative base using SQLAlchemy Core
Base = declarative_base(metadata=metadata)


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
