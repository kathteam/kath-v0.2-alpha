"""
Repository Pattern for Database Operations

Provides clean abstraction layer for data access, following the repository pattern.
Each repository encapsulates database queries for a specific model.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from src.database.config import get_db_session
from src.models import (
    Aggregation,
    Annotation,
    File,
    FilteredVariant,
    MergedVariant,
    SourceVariant,
    Variant,
    WorkflowAudit,
    Workspace,
)
from src.utils.cache import cached_query
from src.utils.profiling import profile_query


class BaseRepository:
    """Base repository with common CRUD operations."""

    model = None

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository with optional session.

        Args:
            session: SQLAlchemy session. If None, uses get_db_session()
        """
        self.session = session or get_db_session()

    def create(self, **kwargs) -> Any:
        """
        Create a new record.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)  # type: ignore[misc]
        self.session.add(instance)
        self.session.commit()
        return instance

    def find_by_id(self, record_id: Any) -> Optional[Any]:
        """
        Find record by ID.

        Args:
            record_id: Primary key value

        Returns:
            Model instance or None
        """
        return self.session.get(self.model, record_id)

    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Any]:
        """
        Find all records with optional pagination.

        Args:
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        query = self.session.query(self.model)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()  # type: ignore[no-any-return]

    def update(self, record_id: Any, **kwargs) -> Optional[Any]:
        """
        Update record by ID.

        Args:
            record_id: Primary key value
            **kwargs: Fields to update

        Returns:
            Updated model instance or None
        """
        instance = self.find_by_id(record_id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.utcnow()
            self.session.commit()
        return instance

    def delete(self, record_id: Any) -> bool:
        """
        Delete record by ID.

        Args:
            record_id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        instance = self.find_by_id(record_id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False

    def count(self) -> int:
        """
        Count total records.

        Returns:
            Number of records
        """
        result = self.session.query(func.count(self.model.id)).scalar()  # type: ignore[attr-defined]
        return int(result) if result is not None else 0


class WorkspaceRepository(BaseRepository):
    """Repository for Workspace operations."""

    model = Workspace  # type: ignore[assignment]

    def find_by_uuid(self, uuid: str) -> Optional[Workspace]:
        """
        Find workspace by UUID.

        Args:
            uuid: Workspace UUID

        Returns:
            Workspace instance or None
        """
        return self.session.query(Workspace).filter_by(id=uuid).first()  # type: ignore[no-any-return]

    def get_or_create(self, uuid: str, name: Optional[str] = None) -> Workspace:
        """
        Get existing workspace or create new one.

        Args:
            uuid: Workspace UUID
            name: Optional workspace name (defaults to UUID)

        Returns:
            Workspace instance
        """
        workspace = self.find_by_uuid(uuid)
        if not workspace:
            workspace = self.create(id=uuid, name=name or uuid)
        return workspace  # type: ignore[return-value]

    def list_files(self, workspace_id: str, parent_id: Optional[int] = None) -> List[File]:
        """
        List files in workspace (optionally filtered by parent directory).

        Args:
            workspace_id: Workspace UUID
            parent_id: Parent directory ID (None for root files)

        Returns:
            List of File instances
        """
        return (  # type: ignore[no-any-return]
            self.session.query(File)
            .filter_by(workspace_id=workspace_id, parent_id=parent_id)
            .order_by(File.file_type.desc(), File.name)
            .all()
        )


class FileRepository(BaseRepository):
    """Repository for File operations."""

    model = File  # type: ignore[assignment]

    def find_by_path(self, workspace_id: str, path: str) -> Optional[File]:
        """
        Find file by workspace and path.

        Args:
            workspace_id: Workspace UUID
            path: File path within workspace

        Returns:
            File instance or None
        """
        return self.session.query(File).filter_by(workspace_id=workspace_id, path=path).first()  # type: ignore[no-any-return]

    def get_or_create(self, workspace_id: str, path: str, name: str, file_type: str = "file", **kwargs) -> File:
        """
        Get existing file or create new one.

        Args:
            workspace_id: Workspace UUID
            path: File path
            name: File name
            file_type: "file" or "folder"
            **kwargs: Additional file attributes

        Returns:
            File instance
        """
        file_obj = self.find_by_path(workspace_id, path)
        if not file_obj:
            file_obj = self.create(workspace_id=workspace_id, path=path, name=name, file_type=file_type, **kwargs)
        return file_obj  # type: ignore[return-value]

    def update_counts(self, file_id: int, row_count: Optional[int] = None, column_count: Optional[int] = None):
        """
        Update file row/column counts.

        Args:
            file_id: File ID
            row_count: New row count
            column_count: New column count
        """
        updates = {}
        if row_count is not None:
            updates["row_count"] = row_count
        if column_count is not None:
            updates["column_count"] = column_count
        if updates:
            self.update(file_id, **updates)

    def rename(self, file_id: int, new_name: str, new_path: str) -> Optional[File]:
        """
        Rename file and update path.

        Args:
            file_id: File ID
            new_name: New file name
            new_path: New file path

        Returns:
            Updated File instance or None
        """
        return self.update(file_id, name=new_name, path=new_path)

    def get_children(self, file_id: int) -> List[File]:
        """
        Get all child files/folders.

        Args:
            file_id: Parent file ID

        Returns:
            List of child File instances
        """
        return self.session.query(File).filter_by(parent_id=file_id).order_by(File.file_type.desc(), File.name).all()  # type: ignore[no-any-return]

    def get_by_workspace(self, workspace_id: str) -> List[File]:
        """
        Get all files in workspace.

        Args:
            workspace_id: Workspace UUID

        Returns:
            List of File instances
        """
        return self.session.query(File).filter_by(workspace_id=workspace_id).order_by(File.path).all()  # type: ignore[no-any-return]


class VariantRepository(BaseRepository):
    """Repository for Variant operations."""

    model = Variant  # type: ignore[assignment]

    def create_bulk(self, variants: List[Dict[str, Any]]) -> int:
        """
        Bulk create variants for efficiency.

        Args:
            variants: List of variant dictionaries

        Returns:
            Number of variants created
        """
        instances = [Variant(**variant_data) for variant_data in variants]
        self.session.bulk_save_objects(instances)
        self.session.commit()
        return len(instances)

    def find_by_file(
        self,
        file_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "row_index",
    ) -> List[Variant]:
        """
        Find variants by file with pagination.

        Args:
            file_id: File ID
            limit: Maximum number of variants
            offset: Number of variants to skip
            order_by: Column to order by

        Returns:
            List of Variant instances
        """
        query = self.session.query(Variant).filter_by(file_id=file_id)

        if order_by:
            query = query.order_by(getattr(Variant, order_by))

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()  # type: ignore[no-any-return]

    def find_by_position(self, chromosome: str, position: int, ref_allele: str, alt_allele: str) -> List[Variant]:
        """
        Find variants by genomic position.

        Args:
            chromosome: Chromosome identifier
            position: Genomic position
            ref_allele: Reference allele
            alt_allele: Alternative allele

        Returns:
            List of matching Variant instances
        """
        return (  # type: ignore[no-any-return]
            self.session.query(Variant)
            .filter_by(chromosome=chromosome, position=position, ref_allele=ref_allele, alt_allele=alt_allele)
            .all()
        )

    @profile_query(log_slow=0.3)
    def find_by_gene(self, gene: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Variant]:
        """
        Find variants by gene symbol.

        Args:
            gene: Gene symbol
            limit: Maximum number of variants
            offset: Number of variants to skip

        Returns:
            List of Variant instances
        """
        query = self.session.query(Variant).filter_by(gene=gene).order_by(Variant.position)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()  # type: ignore[no-any-return]

    @profile_query(log_slow=0.5)
    def filter_variants(
        self,
        file_id: int,
        filters: Dict[str, Any],
        sort_column: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Tuple[List[Variant], int]:
        """
        Filter and sort variants with dynamic conditions.

        Args:
            file_id: File ID
            filters: Dictionary mapping column to {operator: str, value: Any}
                Supported operators: contains, does-not-contain, equals, does-not-equal,
                starts-with, ends-with, is-empty, is-not-empty, gt, gte, lt, lte
            sort_column: Column name to sort by
            sort_order: Sort order ("asc" or "desc")
            limit: Maximum number of variants
            offset: Number of variants to skip

        Returns:
            Tuple of (variants, total_count)
        """
        from sqlalchemy import String, cast

        query = self.session.query(Variant).filter_by(file_id=file_id)

        # Apply filters
        conditions = []
        for column, filter_info in filters.items():
            if not isinstance(filter_info, dict):
                # Legacy format: column->value (equality)
                if hasattr(Variant, column):
                    conditions.append(getattr(Variant, column) == filter_info)
                continue

            operator = filter_info.get("operator")
            value = filter_info.get("value")

            # Get column attribute
            if not hasattr(Variant, column):
                continue

            col_attr = getattr(Variant, column)

            # Apply operator
            if operator == "contains":
                conditions.append(cast(col_attr, String).ilike(f"%{value}%"))
            elif operator == "does-not-contain":
                conditions.append(~cast(col_attr, String).ilike(f"%{value}%"))
            elif operator == "equals":
                conditions.append(cast(col_attr, String).ilike(value))
            elif operator == "does-not-equal":
                conditions.append(~cast(col_attr, String).ilike(value))
            elif operator == "starts-with":
                conditions.append(cast(col_attr, String).ilike(f"{value}%"))
            elif operator == "ends-with":
                conditions.append(cast(col_attr, String).ilike(f"%{value}"))
            elif operator == "is-empty":
                conditions.append(or_(col_attr == "", col_attr.is_(None)))
            elif operator == "is-not-empty":
                conditions.append(and_(col_attr != "", col_attr.isnot(None)))
            elif operator == "gt":
                conditions.append(col_attr > value)
            elif operator == "gte":
                conditions.append(col_attr >= value)
            elif operator == "lt":
                conditions.append(col_attr < value)
            elif operator == "lte":
                conditions.append(col_attr <= value)

        if conditions:
            query = query.filter(and_(*conditions))

        # Apply sorting
        if sort_column and hasattr(Variant, sort_column):
            col_attr = getattr(Variant, sort_column)
            if sort_order == "desc":
                query = query.order_by(desc(col_attr))
            else:
                query = query.order_by(col_attr)
        else:
            # Default sort by row_index
            query = query.order_by(Variant.row_index)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all(), total_count

    @cached_query(ttl=600)
    @profile_query(log_slow=0.1)
    def count_by_file(self, file_id: int) -> int:
        """
        Count variants in file.

        Args:
            file_id: File ID

        Returns:
            Number of variants
        """
        result = self.session.query(func.count(Variant.id)).filter_by(file_id=file_id).scalar()
        return int(result) if result is not None else 0

    def delete_by_file(self, file_id: int) -> int:
        """
        Delete all variants in file.

        Args:
            file_id: File ID

        Returns:
            Number of variants deleted
        """
        count = self.count_by_file(file_id)
        self.session.query(Variant).filter_by(file_id=file_id).delete()
        self.session.commit()
        return count  # type: ignore[no-any-return]


class AnnotationRepository(BaseRepository):
    """Repository for Annotation operations."""

    model = Annotation  # type: ignore[assignment]

    def create_bulk(self, annotations: List[Dict[str, Any]]) -> int:
        """
        Bulk create annotations for efficiency.

        Args:
            annotations: List of annotation dictionaries

        Returns:
            Number of annotations created
        """
        instances = [Annotation(**anno_data) for anno_data in annotations]
        self.session.bulk_save_objects(instances)
        self.session.commit()
        return len(instances)

    def find_by_variant(self, variant_id: int, tool_name: Optional[str] = None) -> List[Annotation]:
        """
        Find annotations for variant.

        Args:
            variant_id: Variant ID
            tool_name: Optional tool name filter

        Returns:
            List of Annotation instances
        """
        query = self.session.query(Annotation).filter_by(variant_id=variant_id)

        if tool_name:
            query = query.filter_by(tool_name=tool_name)

        return query.all()  # type: ignore[no-any-return]

    def find_by_tool(
        self, tool_name: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Annotation]:
        """
        Find annotations by tool name.

        Args:
            tool_name: Tool name (e.g., "SpliceAI", "CADD")
            limit: Maximum number of annotations
            offset: Number of annotations to skip

        Returns:
            List of Annotation instances
        """
        query = self.session.query(Annotation).filter_by(tool_name=tool_name)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()  # type: ignore[no-any-return]

    def find_by_score_range(self, tool_name: str, min_score: float, max_score: float) -> List[Annotation]:
        """
        Find annotations by score range.

        Args:
            tool_name: Tool name
            min_score: Minimum score value
            max_score: Maximum score value

        Returns:
            List of Annotation instances
        """
        return (  # type: ignore[no-any-return]
            self.session.query(Annotation)
            .filter(
                and_(
                    Annotation.tool_name == tool_name,
                    Annotation.score_value >= min_score,
                    Annotation.score_value <= max_score,
                )
            )
            .all()
        )

    def delete_by_variant(self, variant_id: int) -> int:
        """
        Delete all annotations for variant.

        Args:
            variant_id: Variant ID

        Returns:
            Number of annotations deleted
        """
        count_result = self.session.query(func.count(Annotation.id)).filter_by(variant_id=variant_id).scalar()
        self.session.query(Annotation).filter_by(variant_id=variant_id).delete()
        self.session.commit()
        return int(count_result) if count_result is not None else 0


class AggregationRepository(BaseRepository):
    """Repository for Aggregation cache operations."""

    model = Aggregation  # type: ignore[assignment]

    def get_cached(
        self, file_id: int, column_name: str, operation: str, filter_json: Optional[str] = None
    ) -> Optional[Aggregation]:
        """
        Get cached aggregation if not expired.

        Args:
            file_id: File ID
            column_name: Column name
            operation: Aggregation operation
            filter_json: JSON string of filters

        Returns:
            Aggregation instance or None if not cached/expired
        """
        agg = (
            self.session.query(Aggregation)
            .filter_by(file_id=file_id, column_name=column_name, operation=operation, filter_json=filter_json)
            .first()
        )

        if agg and agg.expires_at and agg.expires_at < datetime.utcnow():
            # Cache expired, delete it
            self.session.delete(agg)
            self.session.commit()
            return None

        return agg  # type: ignore[no-any-return]

    def set_cache(
        self,
        file_id: int,
        column_name: str,
        operation: str,
        result_value: float,
        filter_json: Optional[str] = None,
        ttl_hours: int = 24,
    ) -> Aggregation:
        """
        Set aggregation cache with TTL.

        Args:
            file_id: File ID
            column_name: Column name
            operation: Aggregation operation
            result_value: Aggregation result
            filter_json: JSON string of filters
            ttl_hours: Time to live in hours

        Returns:
            Aggregation instance
        """
        # Check if cache exists
        existing = (
            self.session.query(Aggregation)
            .filter_by(file_id=file_id, column_name=column_name, operation=operation, filter_json=filter_json)
            .first()
        )

        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        if existing:
            # Update existing cache
            existing.result_value = result_value
            existing.cached_at = datetime.utcnow()
            existing.expires_at = expires_at
            self.session.commit()
            return existing  # type: ignore[no-any-return]
        else:
            # Create new cache entry
            return self.create(  # type: ignore[no-any-return]
                file_id=file_id,
                column_name=column_name,
                operation=operation,
                filter_json=filter_json,
                result_value=result_value,
                expires_at=expires_at,
            )

    def invalidate_by_file(self, file_id: int) -> int:
        """
        Invalidate all caches for file.

        Args:
            file_id: File ID

        Returns:
            Number of caches invalidated
        """
        count = self.session.query(func.count(Aggregation.id)).filter_by(file_id=file_id).scalar()
        self.session.query(Aggregation).filter_by(file_id=file_id).delete()
        self.session.commit()
        return int(count) if count is not None else 0

    def cleanup_expired(self) -> int:
        """
        Clean up all expired cache entries.

        Returns:
            Number of entries deleted
        """
        count = (
            self.session.query(func.count(Aggregation.id)).filter(Aggregation.expires_at < datetime.utcnow()).scalar()
        )
        self.session.query(Aggregation).filter(Aggregation.expires_at < datetime.utcnow()).delete()
        self.session.commit()
        return int(count) if count is not None else 0


class SourceVariantRepository(BaseRepository):
    """Repository for SourceVariant operations (Phase 2 pipeline)."""

    model = SourceVariant  # type: ignore[assignment]

    def create_bulk(self, variants: List[Dict[str, Any]]) -> int:
        """
        Bulk create source variants for efficiency.

        Args:
            variants: List of source variant dictionaries

        Returns:
            Number of variants created
        """
        instances = [SourceVariant(**variant_data) for variant_data in variants]
        self.session.bulk_save_objects(instances)
        self.session.commit()
        return len(instances)

    def find_by_file(self, file_id: int, source_database: Optional[str] = None) -> List[SourceVariant]:
        """
        Find source variants by file (optionally filtered by source).

        Args:
            file_id: File ID
            source_database: Optional source database name filter

        Returns:
            List of SourceVariant instances
        """
        query = self.session.query(SourceVariant).filter_by(file_id=file_id)
        if source_database:
            query = query.filter_by(source_database=source_database)
        return query.all()  # type: ignore[no-any-return]

    def count_by_source(self, file_id: int) -> Dict[str, int]:
        """
        Count source variants by source database.

        Args:
            file_id: File ID

        Returns:
            Dictionary mapping source database to count
        """
        results = (
            self.session.query(SourceVariant.source_database, func.count(SourceVariant.id))
            .filter_by(file_id=file_id)
            .group_by(SourceVariant.source_database)
            .all()
        )
        return {source: count for source, count in results}

    def find_by_position(self, file_id: int, chromosome: str, position: int) -> List[SourceVariant]:
        """
        Find source variants by genomic position.

        Args:
            file_id: File ID
            chromosome: Chromosome identifier
            position: Genomic position

        Returns:
            List of matching SourceVariant instances
        """
        return (
            self.session.query(SourceVariant)
            .filter_by(file_id=file_id, chromosome=chromosome, position=position)
            .all()
        )  # type: ignore[no-any-return]

    def find_by_gene(self, file_id: int, gene: str) -> List[SourceVariant]:
        """
        Find source variants by gene symbol.

        Args:
            file_id: File ID
            gene: Gene symbol

        Returns:
            List of matching SourceVariant instances
        """
        return (
            self.session.query(SourceVariant)
            .filter_by(file_id=file_id, gene=gene)
            .all()
        )  # type: ignore[no-any-return]

    def delete_by_file(self, file_id: int) -> int:
        """
        Delete all source variants for a file.

        Args:
            file_id: File ID

        Returns:
            Number of records deleted
        """
        count = self.session.query(SourceVariant).filter_by(file_id=file_id).delete()
        self.session.commit()
        return count


class MergedVariantRepository(BaseRepository):
    """Repository for MergedVariant operations (Phase 2 pipeline)."""

    model = MergedVariant  # type: ignore[assignment]

    def create_bulk(self, variants: List[Dict[str, Any]]) -> int:
        """
        Bulk create merged variants for efficiency.

        Args:
            variants: List of merged variant dictionaries

        Returns:
            Number of variants created
        """
        instances = [MergedVariant(**variant_data) for variant_data in variants]
        self.session.bulk_save_objects(instances)
        self.session.commit()
        return len(instances)

    def find_by_file(self, file_id: int) -> List[MergedVariant]:
        """
        Find merged variants by file.

        Args:
            file_id: File ID

        Returns:
            List of MergedVariant instances
        """
        return self.session.query(MergedVariant).filter_by(file_id=file_id).all()  # type: ignore[no-any-return]

    def find_by_gene(self, file_id: int, gene: str) -> List[MergedVariant]:
        """
        Find merged variants by gene.

        Args:
            file_id: File ID
            gene: Gene symbol

        Returns:
            List of MergedVariant instances
        """
        return (
            self.session.query(MergedVariant)
            .filter_by(file_id=file_id, gene=gene)
            .all()
        )  # type: ignore[no-any-return]

    def find_by_position(self, file_id: int, chromosome: str, position: int) -> List[MergedVariant]:
        """
        Find merged variants by genomic position.

        Args:
            file_id: File ID
            chromosome: Chromosome identifier
            position: Genomic position

        Returns:
            List of matching MergedVariant instances
        """
        return (
            self.session.query(MergedVariant)
            .filter_by(file_id=file_id, chromosome=chromosome, position=position)
            .all()
        )  # type: ignore[no-any-return]

    def count_by_file(self, file_id: int) -> int:
        """
        Count merged variants for a file.

        Args:
            file_id: File ID

        Returns:
            Number of merged variants
        """
        count = self.session.query(func.count(MergedVariant.id)).filter_by(file_id=file_id).scalar()
        return int(count) if count else 0

    def delete_by_file(self, file_id: int) -> int:
        """
        Delete all merged variants for a file.

        Args:
            file_id: File ID

        Returns:
            Number of records deleted
        """
        count = self.session.query(MergedVariant).filter_by(file_id=file_id).delete()
        self.session.commit()
        return count


class FilteredVariantRepository(BaseRepository):
    """Repository for FilteredVariant operations (Phase 2 pipeline)."""

    model = FilteredVariant  # type: ignore[assignment]

    def create_bulk(self, variants: List[Dict[str, Any]]) -> int:
        """
        Bulk create filtered variants for efficiency.

        Args:
            variants: List of filtered variant dictionaries

        Returns:
            Number of variants created
        """
        instances = [FilteredVariant(**variant_data) for variant_data in variants]
        self.session.bulk_save_objects(instances)
        self.session.commit()
        return len(instances)

    def find_by_file(self, file_id: int, valid_only: bool = False) -> List[FilteredVariant]:
        """
        Find filtered variants by file.

        Args:
            file_id: File ID
            valid_only: If True, return only valid variants

        Returns:
            List of FilteredVariant instances
        """
        query = self.session.query(FilteredVariant).filter_by(file_id=file_id)
        if valid_only:
            query = query.filter_by(is_valid=True)
        return query.all()  # type: ignore[no-any-return]

    def count_by_validity(self, file_id: int) -> Dict[str, int]:
        """
        Count filtered variants by validity status.

        Args:
            file_id: File ID

        Returns:
            Dictionary with validity counts
        """
        total = self.session.query(func.count(FilteredVariant.id)).filter_by(file_id=file_id).scalar()
        valid = self.session.query(func.count(FilteredVariant.id)).filter_by(file_id=file_id, is_valid=True).scalar()
        complete = self.session.query(func.count(FilteredVariant.id)).filter_by(file_id=file_id, is_complete=True).scalar()

        return {
            "total": int(total) if total else 0,
            "valid": int(valid) if valid else 0,
            "complete": int(complete) if complete else 0,
            "invalid": int(total - valid) if total and valid else 0,
        }

    def find_by_validity(self, file_id: int, is_valid: bool, is_complete: Optional[bool] = None) -> List[FilteredVariant]:
        """
        Find filtered variants by validity flags.

        Args:
            file_id: File ID
            is_valid: Validity status
            is_complete: Optional completeness status

        Returns:
            List of matching FilteredVariant instances
        """
        query = self.session.query(FilteredVariant).filter_by(file_id=file_id, is_valid=is_valid)
        if is_complete is not None:
            query = query.filter_by(is_complete=is_complete)
        return query.all()  # type: ignore[no-any-return]

    def find_by_source_variant(self, source_variant_id: int) -> List[FilteredVariant]:
        """
        Find filtered variants by source variant reference.

        Args:
            source_variant_id: Source variant ID

        Returns:
            List of matching FilteredVariant instances
        """
        return (
            self.session.query(FilteredVariant)
            .filter_by(source_variant_id=source_variant_id)
            .all()
        )  # type: ignore[no-any-return]

    def delete_by_file(self, file_id: int) -> int:
        """
        Delete all filtered variants for a file.

        Args:
            file_id: File ID

        Returns:
            Number of records deleted
        """
        count = self.session.query(FilteredVariant).filter_by(file_id=file_id).delete()
        self.session.commit()
        return count


class WorkflowAuditRepository(BaseRepository):
    """Repository for WorkflowAudit operations (Phase 2 pipeline)."""

    model = WorkflowAudit  # type: ignore[assignment]

    def find_by_file(self, file_id: int) -> List[WorkflowAudit]:
        """
        Find workflow audits by file.

        Args:
            file_id: File ID

        Returns:
            List of WorkflowAudit instances
        """
        return self.session.query(WorkflowAudit).filter_by(file_id=file_id).order_by(
            WorkflowAudit.started_at.desc()
        ).all()  # type: ignore[no-any-return]

    def find_by_operation(self, file_id: int, operation: str) -> List[WorkflowAudit]:
        """
        Find workflow audits by operation type.

        Args:
            file_id: File ID
            operation: Operation type (import, merge, filter, analyze)

        Returns:
            List of matching WorkflowAudit instances
        """
        return (
            self.session.query(WorkflowAudit)
            .filter_by(file_id=file_id, operation=operation)
            .order_by(WorkflowAudit.started_at.desc())
            .all()
        )  # type: ignore[no-any-return]

    def count_by_status(self, file_id: int) -> Dict[str, int]:
        """
        Count workflow audits by status.

        Args:
            file_id: File ID

        Returns:
            Dictionary with status counts
        """
        results = (
            self.session.query(WorkflowAudit.status, func.count(WorkflowAudit.id))
            .filter_by(file_id=file_id)
            .group_by(WorkflowAudit.status)
            .all()
        )
        return {status: count for status, count in results}

    def get_latest_by_operation(self, file_id: int, operation: str) -> Optional[WorkflowAudit]:
        """
        Get the latest workflow audit for an operation.

        Args:
            file_id: File ID
            operation: Operation type

        Returns:
            Latest WorkflowAudit instance or None
        """
        return (
            self.session.query(WorkflowAudit)
            .filter_by(file_id=file_id, operation=operation)
            .order_by(WorkflowAudit.started_at.desc())
            .first()
        )  # type: ignore[no-any-return]

    def get_all_by_status(self, status: str) -> List[WorkflowAudit]:
        """
        Get all workflow audits by status across all files.

        Args:
            status: Status to filter by (pending, completed, failed)

        Returns:
            List of WorkflowAudit instances with matching status
        """
        return (
            self.session.query(WorkflowAudit)
            .filter_by(status=status)
            .order_by(WorkflowAudit.started_at.desc())
            .all()
        )  # type: ignore[no-any-return]

    def delete_by_file(self, file_id: int) -> int:
        """
        Delete all workflow audits for a file.

        Args:
            file_id: File ID

        Returns:
            Number of records deleted
        """
        count = self.session.query(WorkflowAudit).filter_by(file_id=file_id).delete()
        self.session.commit()
        return count


# Export all repositories
__all__ = [
    "BaseRepository",
    "WorkspaceRepository",
    "FileRepository",
    "VariantRepository",
    "AnnotationRepository",
    "AggregationRepository",
    "SourceVariantRepository",
    "MergedVariantRepository",
    "FilteredVariantRepository",
    "WorkflowAuditRepository",
]
