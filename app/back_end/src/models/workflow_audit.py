"""
WorkflowAudit Model

Tracks all operations in the variant processing pipeline for reproducibility,
debugging, and audit trail purposes.
"""

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class WorkflowAudit(Base):
    """
    WorkflowAudit model for operation tracking and audit trail.

    Records every significant operation in the pipeline with full metadata,
    parameters, and results for reproducibility and debugging.

    Attributes:
        id (int): Auto-incrementing audit entry ID
        file_id (int): File being operated on
        operation (str): Operation type (import, merge, filter, analyze)
        operation_stage (str): Specific pipeline stage
        input_count (int): Records before operation
        output_count (int): Records after operation
        parameters (str): JSON with operation parameters
        results (str): JSON with operation results/summary
        started_at (datetime): When operation started
        completed_at (datetime): When operation completed
        status (str): Operation status (pending, completed, failed)
        error_message (str): Error details if failed
        user_id (str): User who triggered operation
        file (relationship): File being operated on
    """

    __tablename__ = "workflow_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        comment="File being operated on"
    )

    # Operation details
    operation = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Operation type (import, merge, filter, analyze)"
    )
    operation_stage = Column(
        String(50),
        nullable=True,
        comment="Specific pipeline stage"
    )

    # Data metrics
    input_count = Column(
        Integer,
        nullable=True,
        comment="Number of records before operation"
    )
    output_count = Column(
        Integer,
        nullable=True,
        comment="Number of records after operation"
    )

    # Operation metadata
    parameters = Column(
        Text,
        nullable=True,
        comment="JSON with operation parameters"
    )
    results = Column(
        Text,
        nullable=True,
        comment="JSON with operation results/summary"
    )

    # Timing information
    started_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When operation started"
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="When operation completed"
    )

    # Status tracking
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Operation status (pending, completed, failed)"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error details if operation failed"
    )

    # User tracking
    user_id = Column(
        String(255),
        nullable=True,
        comment="User who triggered operation"
    )

    # Relationships
    file = relationship("File", back_populates="workflow_audits")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_wa_file_id", "file_id"),
        Index("idx_wa_operation", "operation"),
        Index("idx_wa_status", "status"),
        Index("idx_wa_timestamp", "file_id", "started_at"),
    )

    def __repr__(self):
        return (
            f"<WorkflowAudit(id={self.id}, operation='{self.operation}', "
            f"status='{self.status}', file_id={self.file_id})>"
        )

    @property
    def params(self):
        """Parse operation parameters from JSON."""
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except json.JSONDecodeError:
                return {}
        return {}

    @params.setter
    def params(self, value):
        """Set operation parameters from dictionary."""
        if value:
            self.parameters = json.dumps(value)
        else:
            self.parameters = None

    @property
    def output_data(self):
        """Parse operation results from JSON."""
        if self.results:
            try:
                return json.loads(self.results)
            except json.JSONDecodeError:
                return {}
        return {}

    @output_data.setter
    def output_data(self, value):
        """Set operation results from dictionary."""
        if value:
            self.results = json.dumps(value)
        else:
            self.results = None

    def get_duration_seconds(self):
        """Get operation duration in seconds."""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def get_delta_count(self):
        """Get change in record count (output - input)."""
        if self.input_count is not None and self.output_count is not None:
            return self.output_count - self.input_count
        return None

    def mark_completed(self):
        """Mark operation as completed."""
        self.completed_at = datetime.utcnow()
        self.status = "completed"

    def mark_failed(self, error_msg):
        """Mark operation as failed with error message."""
        self.completed_at = datetime.utcnow()
        self.status = "failed"
        self.error_message = error_msg

    def to_dict(self):
        """Convert audit entry to dictionary representation."""
        result = {
            "id": self.id,
            "file_id": self.file_id,
            "operation": self.operation,
            "operation_stage": self.operation_stage,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "delta_count": self.get_delta_count(),
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.get_duration_seconds(),
            "user_id": self.user_id,
        }

        # Add parameters and results if present
        if self.params:
            result["parameters"] = self.params

        if self.output_data:
            result["results"] = self.output_data

        if self.error_message:
            result["error_message"] = self.error_message

        return result
