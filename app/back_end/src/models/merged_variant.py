"""
MergedVariant Model

Represents genetic variants after merging multiple sources.
This table stores the combined results of merge operations with
complete source attribution and composition metadata.
"""

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class MergedVariant(Base, TimestampMixin):
    """
    MergedVariant model for post-merge combined variant data.

    Stores variants after merging multiple source databases,
    maintaining full source attribution and merge metadata.

    Attributes:
        id (int): Auto-incrementing variant ID
        file_id (int): Parent merged file ID
        chromosome (str): Canonical chromosome identifier
        position (int): Canonical genomic position (hg38)
        ref_allele (str): Canonical reference allele
        alt_allele (str): Canonical alternative allele
        gen_pos (str): Canonical format "chr-pos-ref-alt"
        gene (str): Gene symbol (combined from all sources)
        transcript (str): Transcript ID (primary source)
        consequence (str): Variant consequence (combined)
        source_databases (str): JSON array of source databases ["clinvar", "lovd"]
        clinvar_data (str): JSON with ClinVar-specific fields
        lovd_data (str): JSON with LOVD-specific fields
        gnomad_data (str): JSON with gnomAD-specific fields
        merge_timestamp (datetime): When merge operation occurred
        merge_strategy (str): Merge operation type ("outer_join", "inner_join", etc.)
        file (relationship): Parent merged file
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """

    __tablename__ = "merged_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent merged file"
    )

    # Canonical merged coordinates
    chromosome = Column(String(10), nullable=False, index=True, comment="Chromosome")
    position = Column(Integer, nullable=False, index=True, comment="Genomic position (hg38)")
    ref_allele = Column(String(255), nullable=False, comment="Reference allele")
    alt_allele = Column(String(255), nullable=False, comment="Alternative allele")

    # Standardized identifiers
    gen_pos = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Canonical position: chr-pos-ref-alt"
    )

    # Merged annotation fields
    gene = Column(String(255), nullable=True, index=True, comment="Gene symbol")
    transcript = Column(String(255), nullable=True, comment="Transcript ID (primary)")
    consequence = Column(String(255), nullable=True, comment="Variant consequence")

    # Source composition
    source_databases = Column(
        Text,
        nullable=False,
        comment="JSON array of source databases present in merge"
    )

    # Source-specific data columns
    clinvar_data = Column(
        Text,
        nullable=True,
        comment="JSON object with ClinVar-specific fields"
    )
    lovd_data = Column(
        Text,
        nullable=True,
        comment="JSON object with LOVD-specific fields"
    )
    gnomad_data = Column(
        Text,
        nullable=True,
        comment="JSON object with gnomAD-specific fields"
    )

    # Merge metadata
    merge_timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When this merged record was created"
    )
    merge_strategy = Column(
        String(50),
        nullable=True,
        comment="Merge strategy (outer_join, inner_join, union, etc.)"
    )

    # Relationships
    file = relationship("File", back_populates="merged_variants")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_mv_file_id", "file_id"),
        Index("idx_mv_coordinates", "chromosome", "position", "ref_allele", "alt_allele"),
        Index("idx_mv_gene", "file_id", "gene"),
    )

    def __repr__(self):
        return (
            f"<MergedVariant(id={self.id}, gen_pos='{self.gen_pos}', "
            f"sources={self.source_list}, gene='{self.gene}')>"
        )

    @property
    def source_list(self):
        """Get list of source databases in this merge."""
        if self.source_databases:
            try:
                return json.loads(self.source_databases)
            except json.JSONDecodeError:
                return []
        return []

    @source_list.setter
    def source_list(self, value):
        """Set source database list from array."""
        if value:
            self.source_databases = json.dumps(value)
        else:
            self.source_databases = "[]"

    @property
    def clinvar_fields(self):
        """Parse ClinVar-specific data from JSON."""
        if self.clinvar_data:
            try:
                return json.loads(self.clinvar_data)
            except json.JSONDecodeError:
                return {}
        return {}

    @clinvar_fields.setter
    def clinvar_fields(self, value):
        """Set ClinVar data from dictionary."""
        if value:
            self.clinvar_data = json.dumps(value)
        else:
            self.clinvar_data = None

    @property
    def lovd_fields(self):
        """Parse LOVD-specific data from JSON."""
        if self.lovd_data:
            try:
                return json.loads(self.lovd_data)
            except json.JSONDecodeError:
                return {}
        return {}

    @lovd_fields.setter
    def lovd_fields(self, value):
        """Set LOVD data from dictionary."""
        if value:
            self.lovd_data = json.dumps(value)
        else:
            self.lovd_data = None

    @property
    def gnomad_fields(self):
        """Parse gnomAD-specific data from JSON."""
        if self.gnomad_data:
            try:
                return json.loads(self.gnomad_data)
            except json.JSONDecodeError:
                return {}
        return {}

    @gnomad_fields.setter
    def gnomad_fields(self, value):
        """Set gnomAD data from dictionary."""
        if value:
            self.gnomad_data = json.dumps(value)
        else:
            self.gnomad_data = None

    def to_dict(self):
        """Convert merged variant to dictionary representation."""
        result = {
            "id": self.id,
            "file_id": self.file_id,
            "chromosome": self.chromosome,
            "position": self.position,
            "ref_allele": self.ref_allele,
            "alt_allele": self.alt_allele,
            "gen_pos": self.gen_pos,
            "gene": self.gene,
            "transcript": self.transcript,
            "consequence": self.consequence,
            "source_databases": self.source_list,
            "merge_timestamp": self.merge_timestamp.isoformat() if self.merge_timestamp else None,
            "merge_strategy": self.merge_strategy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add source-specific data if present
        if self.clinvar_fields:
            result["clinvar"] = self.clinvar_fields
        if self.lovd_fields:
            result["lovd"] = self.lovd_fields
        if self.gnomad_fields:
            result["gnomad"] = self.gnomad_fields

        return result

    def get_source_data(self, source_name):
        """
        Get data from a specific source.

        Args:
            source_name (str): Source database name ("clinvar", "lovd", "gnomad")

        Returns:
            dict: Source-specific data or empty dict if not present
        """
        source_name = source_name.lower()

        if source_name == "clinvar":
            return self.clinvar_fields
        elif source_name == "lovd":
            return self.lovd_fields
        elif source_name == "gnomad":
            return self.gnomad_fields

        return {}
