"""
FilteredVariant Model

Represents genetic variants after quality control and validation filtering.
Stores variants that pass quality thresholds with flag results and audit trail.
"""

import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class FilteredVariant(Base, TimestampMixin):
    """
    FilteredVariant model for quality-controlled variant data.

    Stores variants after validation and filtering operations,
    with complete audit trail of which filters passed/failed.

    Attributes:
        id (int): Auto-incrementing variant ID
        file_id (int): Parent filtered file ID
        source_variant_id (int): Original source variant ID (if applicable)
        merged_variant_id (int): Original merged variant ID (if applicable)
        chromosome (str): Chromosome identifier
        position (int): Genomic position
        ref_allele (str): Reference allele
        alt_allele (str): Alternative allele
        gen_pos (str): Canonical format "chr-pos-ref-alt"
        is_complete (bool): Has all required genomic fields
        is_valid (bool): Passes all validation rules
        filter_results (str): JSON with individual filter pass/fail results
        filter_timestamp (datetime): When filtering was applied
        filter_version (str): Version of filter rules applied
        file (relationship): Parent filtered file
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """

    __tablename__ = "filtered_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent filtered file"
    )

    # Links to previous pipeline stages
    source_variant_id = Column(
        Integer,
        ForeignKey("source_variants.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original source variant ID"
    )
    merged_variant_id = Column(
        Integer,
        ForeignKey("merged_variants.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original merged variant ID"
    )

    # Genomic coordinates
    chromosome = Column(String(10), nullable=False, index=True, comment="Chromosome")
    position = Column(Integer, nullable=False, index=True, comment="Genomic position")
    ref_allele = Column(String(255), nullable=False, comment="Reference allele")
    alt_allele = Column(String(255), nullable=False, comment="Alternative allele")
    gen_pos = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Canonical position: chr-pos-ref-alt"
    )

    # Quality flags
    is_complete = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Has all required fields"
    )
    is_valid = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Passes all validation rules"
    )

    # Filter audit trail
    filter_results = Column(
        Text,
        nullable=True,
        comment="JSON with individual filter results"
    )

    # Filter metadata
    filter_timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When filtering was applied"
    )
    filter_version = Column(
        String(50),
        nullable=True,
        comment="Version of filter rules applied"
    )

    # Relationships
    file = relationship("File", back_populates="filtered_variants")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_fv_file_id", "file_id"),
        Index("idx_fv_coordinates", "chromosome", "position", "ref_allele", "alt_allele"),
        Index("idx_fv_validity", "file_id", "is_valid"),
        Index("idx_fv_completeness", "file_id", "is_complete"),
    )

    def __repr__(self):
        return (
            f"<FilteredVariant(id={self.id}, gen_pos='{self.gen_pos}', "
            f"valid={self.is_valid}, complete={self.is_complete})>"
        )

    @property
    def filter_flags(self):
        """Parse filter results from JSON."""
        if self.filter_results:
            try:
                return json.loads(self.filter_results)
            except json.JSONDecodeError:
                return {}
        return {}

    @filter_flags.setter
    def filter_flags(self, value):
        """Set filter results from dictionary."""
        if value:
            self.filter_results = json.dumps(value)
        else:
            self.filter_results = None

    def passed_all_filters(self):
        """Check if variant passed all filters."""
        return self.is_valid and self.is_complete

    def to_dict(self):
        """Convert filtered variant to dictionary representation."""
        result = {
            "id": self.id,
            "file_id": self.file_id,
            "chromosome": self.chromosome,
            "position": self.position,
            "ref_allele": self.ref_allele,
            "alt_allele": self.alt_allele,
            "gen_pos": self.gen_pos,
            "is_complete": self.is_complete,
            "is_valid": self.is_valid,
            "passed_all_filters": self.passed_all_filters(),
            "filter_timestamp": self.filter_timestamp.isoformat() if self.filter_timestamp else None,
            "filter_version": self.filter_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add source variant link if present
        if self.source_variant_id:
            result["source_variant_id"] = self.source_variant_id

        # Add merged variant link if present
        if self.merged_variant_id:
            result["merged_variant_id"] = self.merged_variant_id

        # Add filter details
        if self.filter_flags:
            result["filter_details"] = self.filter_flags

        return result
