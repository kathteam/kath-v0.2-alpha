"""
Annotation Model

Represents analysis tool results (SpliceAI, CADD, REVEL) for genetic variants.
"""

import json

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base


class Annotation(Base):
    """
    Annotation model for tool analysis results.

    Attributes:
        id (int): Auto-incrementing annotation ID
        variant_id (int): Associated variant ID
        tool_name (str): Analysis tool name (SpliceAI, CADD, REVEL)
        annotation_type (str): Type of score/annotation
        score_value (float): Numeric score value
        score_label (str): Classification label
        metadata_json (str): JSON for additional tool-specific data
        variant (relationship): Parent variant
        created_at (datetime): Annotation creation timestamp
    """

    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    variant_id = Column(Integer, ForeignKey("variants.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(50), nullable=False, index=True, comment="Tool name")
    annotation_type = Column(String(50), nullable=False, comment="Score/annotation type")
    score_value = Column(Float, nullable=True, comment="Numeric score")
    score_label = Column(String(100), nullable=True, comment="Classification label")
    metadata_json = Column(Text, nullable=True, comment="Additional tool data")

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    variant = relationship("Variant", back_populates="annotations")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_annotations_tool_type", "tool_name", "annotation_type"),
        Index("idx_annotations_tool_score", "tool_name", "score_value"),
    )

    def __repr__(self):
        return f"<Annotation(id={self.id}, tool='{self.tool_name}', type='{self.annotation_type}', value={self.score_value})>"

    @property
    def metadata_dict(self):
        """Parse metadata JSON to dictionary."""
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}

    @metadata_dict.setter
    def metadata_dict(self, value):
        """Set metadata from dictionary."""
        if value:
            self.metadata_json = json.dumps(value)
        else:
            self.metadata_json = None

    def to_dict(self):
        """Convert annotation to dictionary representation."""
        result = {
            "id": self.id,
            "variant_id": self.variant_id,
            "tool_name": self.tool_name,
            "annotation_type": self.annotation_type,
            "score_value": self.score_value,
            "score_label": self.score_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Merge metadata
        if self.metadata_dict:
            result["metadata"] = self.metadata_dict

        return result

    @classmethod
    def create_spliceai_annotation(cls, variant_id, delta_scores):
        """
        Factory method to create SpliceAI annotation from delta scores.

        Args:
            variant_id (int): Variant ID
            delta_scores (dict): Dictionary with keys: acceptor_gain, acceptor_loss, donor_gain, donor_loss

        Returns:
            Annotation: SpliceAI annotation instance
        """
        max_score = max(delta_scores.values())
        return cls(
            variant_id=variant_id,
            tool_name="SpliceAI",
            annotation_type="delta_score",
            score_value=max_score,
            metadata_dict=delta_scores,
        )

    @classmethod
    def create_cadd_annotation(cls, variant_id, phred_score, raw_score=None):
        """
        Factory method to create CADD annotation.

        Args:
            variant_id (int): Variant ID
            phred_score (float): CADD PHRED score
            raw_score (float): Optional raw score

        Returns:
            Annotation: CADD annotation instance
        """
        label = None
        if phred_score >= 20:
            label = "Likely Pathogenic"
        elif phred_score >= 10:
            label = "Uncertain"
        else:
            label = "Likely Benign"

        metadata = {}
        if raw_score is not None:
            metadata["raw_score"] = raw_score

        return cls(
            variant_id=variant_id,
            tool_name="CADD",
            annotation_type="phred_score",
            score_value=phred_score,
            score_label=label,
            metadata_dict=metadata if metadata else None,
        )

    @classmethod
    def create_revel_annotation(cls, variant_id, revel_score):
        """
        Factory method to create REVEL annotation.

        Args:
            variant_id (int): Variant ID
            revel_score (float): REVEL pathogenicity score

        Returns:
            Annotation: REVEL annotation instance
        """
        label = None
        if revel_score >= 0.7:
            label = "Pathogenic"
        elif revel_score >= 0.5:
            label = "Uncertain"
        else:
            label = "Benign"

        return cls(
            variant_id=variant_id,
            tool_name="REVEL",
            annotation_type="pathogenicity_score",
            score_value=revel_score,
            score_label=label,
        )
