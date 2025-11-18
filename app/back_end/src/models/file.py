"""
File Model

Represents files and directories within user workspaces.
Supports hierarchical file structure with parent-child relationships.
"""

import json

from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class File(Base, TimestampMixin):
    """
    File model for workspace files and directories.

    Attributes:
        id (int): Auto-incrementing file ID
        workspace_id (str): Parent workspace UUID
        name (str): File name
        path (str): Relative path within workspace
        file_type (str): "file" or "folder"
        parent_id (int): Parent directory ID (NULL for root)
        row_count (int): Number of variant rows (for CSV files)
        column_count (int): Number of columns
        data_source (str): Data source ("gnomAD", "ClinVar", "LOVD", "Custom")
        header_json (str): JSON array of column names
        workspace (relationship): Parent workspace
        parent (relationship): Parent directory
        children (relationship): Child files/directories
        variants (relationship): Variant records
        aggregations (relationship): Cached aggregations
    """

    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(String(255), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, comment="File name")
    path = Column(String(512), nullable=False, comment="Relative path within workspace")
    file_type = Column(String(10), nullable=False, comment="file or folder")
    parent_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=True)
    row_count = Column(Integer, default=0, comment="Number of variant rows")
    column_count = Column(Integer, default=0, comment="Number of columns")
    data_source = Column(String(50), nullable=True, comment="gnomAD, ClinVar, LOVD, Custom")
    header_json = Column(Text, nullable=True, comment="JSON array of column names")

    # Relationships
    workspace = relationship("Workspace", back_populates="files")
    parent = relationship("File", remote_side=[id], back_populates="children")
    children = relationship("File", back_populates="parent", cascade="all, delete-orphan")
    variants = relationship("Variant", back_populates="file", cascade="all, delete-orphan", lazy="dynamic")
    aggregations = relationship("Aggregation", back_populates="file", cascade="all, delete-orphan")

    # Phase 2 pipeline relationships
    source_variants = relationship("SourceVariant", back_populates="file", cascade="all, delete-orphan", lazy="dynamic")
    merged_variants = relationship("MergedVariant", back_populates="file", cascade="all, delete-orphan", lazy="dynamic")
    filtered_variants = relationship("FilteredVariant", back_populates="file", cascade="all, delete-orphan", lazy="dynamic")
    workflow_audits = relationship("WorkflowAudit", back_populates="file", cascade="all, delete-orphan", lazy="dynamic")

    # Unique constraint on workspace + path
    __table_args__ = (UniqueConstraint("workspace_id", "path", name="uq_workspace_path"),)

    def __repr__(self):
        return f"<File(id={self.id}, path='{self.path}', type='{self.file_type}')>"

    @property
    def header(self):
        """Parse header JSON to list."""
        if self.header_json:
            try:
                return json.loads(self.header_json)
            except json.JSONDecodeError:
                return []
        return []

    @header.setter
    def header(self, value):
        """Set header from list."""
        if value:
            self.header_json = json.dumps(value)
        else:
            self.header_json = None

    def to_dict(self, include_children=False):
        """Convert file to dictionary representation."""
        result = {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "path": self.path,
            "file_type": self.file_type,
            "parent_id": self.parent_id,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "data_source": self.data_source,
            "header": self.header,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_children and self.file_type == "folder":
            result["children"] = [child.to_dict(include_children=True) for child in self.children]

        return result
