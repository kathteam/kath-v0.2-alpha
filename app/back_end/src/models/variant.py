"""
Variant Model

Represents genetic variants stored in the database.
Each variant corresponds to a row in the original CSV files.
"""

import json

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base


class Variant(Base):
    """
    Variant model for genetic variant data.

    Attributes:
        id (int): Auto-incrementing variant ID
        file_id (int): Parent file ID
        row_index (int): Original CSV row index (for pagination/ordering)
        chromosome (str): Chromosome identifier
        position (int): Genomic position
        ref_allele (str): Reference allele
        alt_allele (str): Alternative allele
        variant_id (str): External variant identifier (rs number, gnomAD ID)
        gen_pos (str): Combined position format "chr-pos-ref-alt"
        gene (str): Gene symbol
        transcript (str): Transcript ID
        consequence (str): Variant consequence/effect
        data_json (str): JSON object for additional CSV columns
        file (relationship): Parent file
        annotations (relationship): Tool annotations
        created_at (datetime): Row creation timestamp
    """

    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    row_index = Column(Integer, nullable=False, comment="Original CSV row number")

    # Core variant information
    chromosome = Column(String(10), nullable=True, index=True, comment="Chromosome")
    position = Column(Integer, nullable=True, comment="Genomic position")
    ref_allele = Column(String(255), nullable=True, comment="Reference allele")
    alt_allele = Column(String(255), nullable=True, comment="Alternative allele")
    variant_id = Column(String(255), nullable=True, index=True, comment="External variant ID")
    gen_pos = Column(String(255), nullable=True, index=True, comment="chr-pos-ref-alt format")

    # Gene/transcript information
    gene = Column(String(255), nullable=True, index=True, comment="Gene symbol")
    transcript = Column(String(255), nullable=True, comment="Transcript ID")
    consequence = Column(String(255), nullable=True, comment="Variant consequence")

    # Additional data (flexible storage)
    data_json = Column(Text, nullable=True, comment="JSON object for other columns")

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    file = relationship("File", back_populates="variants")
    annotations = relationship("Annotation", back_populates="variant", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_variants_file_row", "file_id", "row_index"),
        Index("idx_variants_lookup", "chromosome", "position", "ref_allele", "alt_allele"),
    )

    def __repr__(self):
        return f"<Variant(id={self.id}, gen_pos='{self.gen_pos}', gene='{self.gene}')>"

    @property
    def data(self):
        """Parse data JSON to dictionary."""
        if self.data_json:
            try:
                return json.loads(self.data_json)
            except json.JSONDecodeError:
                return {}
        return {}

    @data.setter
    def data(self, value):
        """Set data from dictionary."""
        if value:
            self.data_json = json.dumps(value)
        else:
            self.data_json = None

    def to_dict(self, include_annotations=False):
        """Convert variant to dictionary representation."""
        result = {
            "id": self.id,
            "file_id": self.file_id,
            "row_index": self.row_index,
            "chromosome": self.chromosome,
            "position": self.position,
            "ref_allele": self.ref_allele,
            "alt_allele": self.alt_allele,
            "variant_id": self.variant_id,
            "gen_pos": self.gen_pos,
            "gene": self.gene,
            "transcript": self.transcript,
            "consequence": self.consequence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Merge additional data from JSON
        if self.data:
            result.update(self.data)

        if include_annotations:
            result["annotations"] = [ann.to_dict() for ann in self.annotations]

        return result

    def to_csv_row(self, columns=None):
        """
        Convert variant to CSV row format.

        Args:
            columns (list): List of column names to include (None = all)

        Returns:
            dict: Dictionary with CSV column values
        """
        row = self.to_dict()

        # If specific columns requested, filter
        if columns:
            row = {k: row.get(k) for k in columns}

        return row
