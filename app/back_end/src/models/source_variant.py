"""
SourceVariant Model

Represents genetic variants as imported from external data sources
(ClinVar, LOVD, gnomAD). This table stores the pre-merge, raw data
from each source with full attribution and import metadata.
"""

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class SourceVariant(Base, TimestampMixin):
    """
    SourceVariant model for pre-merge genetic variant data.

    Stores variants exactly as imported from external sources,
    preserving all source-specific fields and metadata.

    Attributes:
        id (int): Auto-incrementing variant ID
        file_id (int): Parent file ID
        source_database (str): Source database ("clinvar", "lovd", "gnomad", or "custom")
        chromosome (str): Chromosome identifier
        position (int): Genomic position (in source coordinate system)
        ref_allele (str): Reference allele
        alt_allele (str): Alternative allele
        gen_pos (str): Canonical format "chr-pos-ref-alt" (hg38)
        variant_id (str): External variant identifier (rs number, variant ID)
        gene (str): Gene symbol
        transcript (str): Transcript ID
        consequence (str): Variant consequence/functional effect
        source_data (str): JSON with source-specific fields
        import_timestamp (datetime): When this record was imported
        source_version (str): Version/build of source database at import time
        file (relationship): Parent file
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """

    __tablename__ = "source_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)

    # Source attribution
    source_database = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Source database (clinvar, lovd, gnomad, custom)"
    )

    # Core genomic coordinates
    chromosome = Column(String(10), nullable=False, index=True, comment="Chromosome")
    position = Column(Integer, nullable=False, index=True, comment="Genomic position (hg38)")
    ref_allele = Column(String(255), nullable=False, comment="Reference allele")
    alt_allele = Column(String(255), nullable=False, comment="Alternative allele")

    # Standardized identifiers
    gen_pos = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Canonical position format: chr-pos-ref-alt"
    )
    variant_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="External variant ID (rs number, etc.)"
    )

    # Annotation fields
    gene = Column(String(255), nullable=True, index=True, comment="Gene symbol")
    transcript = Column(String(255), nullable=True, comment="Transcript ID")
    consequence = Column(String(255), nullable=True, comment="Variant consequence")

    # Source-specific data
    source_data = Column(
        Text,
        nullable=True,
        comment="JSON object with source-specific fields"
    )

    # Import metadata
    import_timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When variant was imported"
    )
    source_version = Column(
        String(50),
        nullable=True,
        comment="Source database version/build at import time"
    )

    # Relationships
    file = relationship("File", back_populates="source_variants")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_sv_file_source", "file_id", "source_database"),
        Index("idx_sv_coordinates", "chromosome", "position", "ref_allele", "alt_allele"),
        Index("idx_sv_import_time", "file_id", "import_timestamp"),
    )

    def __repr__(self):
        return (
            f"<SourceVariant(id={self.id}, source={self.source_database}, "
            f"gen_pos='{self.gen_pos}', gene='{self.gene}')>"
        )

    @property
    def source_fields(self):
        """Parse source-specific data from JSON."""
        if self.source_data:
            try:
                return json.loads(self.source_data)
            except json.JSONDecodeError:
                return {}
        return {}

    @source_fields.setter
    def source_fields(self, value):
        """Set source-specific data from dictionary."""
        if value:
            self.source_data = json.dumps(value)
        else:
            self.source_data = None

    def to_dict(self):
        """Convert source variant to dictionary representation."""
        result = {
            "id": self.id,
            "file_id": self.file_id,
            "source_database": self.source_database,
            "chromosome": self.chromosome,
            "position": self.position,
            "ref_allele": self.ref_allele,
            "alt_allele": self.alt_allele,
            "gen_pos": self.gen_pos,
            "variant_id": self.variant_id,
            "gene": self.gene,
            "transcript": self.transcript,
            "consequence": self.consequence,
            "import_timestamp": self.import_timestamp.isoformat() if self.import_timestamp else None,
            "source_version": self.source_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add source-specific fields
        if self.source_fields:
            result["source_fields"] = self.source_fields

        return result
