"""
Workspace Model

Represents a user workspace in the KATH application.
Each workspace contains files and is associated with a user UUID.
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Workspace(Base, TimestampMixin):
    """
    Workspace model for user workspaces.

    Attributes:
        id (str): User UUID (primary key)
        name (str): Workspace name
        files (relationship): Related files in this workspace
        created_at (datetime): Workspace creation timestamp
        updated_at (datetime): Last modification timestamp
    """

    __tablename__ = "workspaces"

    id = Column(String(255), primary_key=True, comment="User UUID")
    name = Column(String(255), nullable=False, comment="Workspace name")

    # Relationships
    files = relationship("File", back_populates="workspace", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<Workspace(id='{self.id}', name='{self.name}')>"

    def to_dict(self):
        """Convert workspace to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
