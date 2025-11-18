"""
Database Models Package

This package contains SQLAlchemy ORM models for the KATH application.

Core Models:
- Workspace: User workspace management
- File: File metadata and hierarchy
- Variant: Genetic variant storage
- Annotation: Analysis tool results
- Aggregation: Cached aggregation results

Phase 2 Pipeline Models:
- SourceVariant: Pre-merge data from external sources
- MergedVariant: Combined data after merge operations
- FilteredVariant: Quality-controlled variants
- WorkflowAudit: Pipeline operation audit trail
"""

from .aggregation import Aggregation
from .annotation import Annotation
from .base import Base
from .file import File
from .filtered_variant import FilteredVariant
from .merged_variant import MergedVariant
from .source_variant import SourceVariant
from .variant import Variant
from .workflow_audit import WorkflowAudit
from .workspace import Workspace

__all__ = [
    "Base",
    "Workspace",
    "File",
    "Variant",
    "Annotation",
    "Aggregation",
    # Phase 2 models
    "SourceVariant",
    "MergedVariant",
    "FilteredVariant",
    "WorkflowAudit",
]
