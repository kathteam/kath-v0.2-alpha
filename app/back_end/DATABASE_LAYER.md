# KATH Database Layer Documentation

**Date**: 2025-10-28
**Phase**: Phase 2 - Database Migration (Task 2.2)
**Status**: [V] Complete

---

## Overview

The database layer provides a clean abstraction for data persistence in KATH, transitioning from CSV file storage to a relational SQLite database. This implementation uses the Repository Pattern for data access and Alembic for schema migrations.

---

## Architecture

### Technology Stack

- **SQLAlchemy Core**: Declarative model definitions
- **Flask-SQLAlchemy**: Session management and Flask integration
- **Alembic**: Database migrations
- **SQLite**: Embedded relational database

### Design Patterns

1. **Repository Pattern**: Encapsulates data access logic
2. **Declarative Base**: Type-safe model definitions
3. **TimestampMixin**: Automatic created_at/updated_at tracking
4. **Factory Methods**: Tool-specific annotation creation

---

## Database Schema

### Tables

#### 1. `workspaces`

User workspace management.

```sql
CREATE TABLE workspaces (
    id TEXT PRIMARY KEY,              -- User UUID
    name TEXT NOT NULL,               -- Workspace name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Relationships**: Has many `files`

---

#### 2. `files`

File metadata and directory hierarchy.

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,       -- FK to workspaces
    name TEXT NOT NULL,               -- File name
    path TEXT NOT NULL,               -- Relative path within workspace
    file_type TEXT NOT NULL,          -- 'file' or 'folder'
    parent_id INTEGER,                -- FK to files (self-referencing)
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    data_source TEXT,                 -- 'gnomAD', 'ClinVar', 'LOVD', 'Custom'
    header_json TEXT,                 -- JSON array of column names
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE (workspace_id, path)
);
```

**Relationships**:

- Belongs to `workspace`
- Belongs to `parent` file (optional)
- Has many `children` files
- Has many `variants`
- Has many `aggregations`

**Indexes**:

- `ix_files_workspace_id`: Workspace lookups
- `ix_files_path`: Path lookups
- `ix_files_parent_id`: Hierarchy navigation
- `ix_files_file_type`: Type filtering

---

#### 3. `variants`

Genetic variant storage.

```sql
CREATE TABLE variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,         -- FK to files
    row_index INTEGER NOT NULL,       -- Original CSV row number
    chromosome TEXT,
    position INTEGER,
    ref_allele TEXT,
    alt_allele TEXT,
    variant_id TEXT,                  -- External ID (rs number, gnomAD ID)
    gen_pos TEXT,                     -- 'chr-pos-ref-alt' format
    gene TEXT,
    transcript TEXT,
    consequence TEXT,
    data_json TEXT,                   -- JSON for additional columns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Relationships**:

- Belongs to `file`
- Has many `annotations`

**Indexes**:

- `ix_variants_file_id`: File lookups
- `ix_variants_file_row`: Pagination (file_id, row_index)
- `ix_variants_lookup`: Position lookup (chromosome, position, ref, alt)
- `ix_variants_chromosome`: Chromosome filtering
- `ix_variants_variant_id`: External ID lookup
- `ix_variants_gen_pos`: gen_pos lookup
- `ix_variants_gene`: Gene queries

---

#### 4. `annotations`

Analysis tool results (SpliceAI, CADD, REVEL).

```sql
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,      -- FK to variants
    tool_name TEXT NOT NULL,          -- 'SpliceAI', 'CADD', 'REVEL'
    annotation_type TEXT NOT NULL,    -- Score type
    score_value REAL,
    score_label TEXT,
    metadata_json TEXT,               -- Tool-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
);
```

**Relationships**:

- Belongs to `variant`

**Indexes**:

- `ix_annotations_variant_id`: Variant lookups
- `ix_annotations_tool_name`: Tool filtering
- `ix_annotations_tool_type`: Tool + type queries
- `ix_annotations_tool_score`: Score range queries

---

#### 5. `aggregations`

Cached aggregation results for performance.

```sql
CREATE TABLE aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,         -- FK to files
    column_name TEXT NOT NULL,
    operation TEXT NOT NULL,          -- 'SUM', 'AVG', 'MIN', 'MAX', 'COUNT'
    filter_json TEXT,                 -- JSON of applied filters
    result_value REAL NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,             -- Cache expiration
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE (file_id, column_name, operation, filter_json)
);
```

**Relationships**:

- Belongs to `file`

**Indexes**:

- `ix_aggregations_file_column`: Cache lookups
- `ix_aggregations_expires`: Expiration cleanup

---

## Repository Layer

### Base Repository

All repositories inherit from `BaseRepository` which provides:

- `create(**kwargs)`: Create new record
- `find_by_id(record_id)`: Find by primary key
- `find_all(limit, offset)`: List with pagination
- `update(record_id, **kwargs)`: Update record
- `delete(record_id)`: Delete record
- `count()`: Count total records

### WorkspaceRepository

```python
from src.database import WorkspaceRepository

repo = WorkspaceRepository()

# Get or create workspace
workspace = repo.get_or_create(uuid="user-uuid", name="My Workspace")

# List files in workspace
files = repo.list_files(workspace_id="user-uuid", parent_id=None)
```

### FileRepository

```python
from src.database import FileRepository

repo = FileRepository()

# Find by path
file = repo.find_by_path(workspace_id="uuid", path="folder/file.csv")

# Get or create file
file = repo.get_or_create(
    workspace_id="uuid",
    path="data/variants.csv",
    name="variants.csv",
    file_type="file",
    data_source="gnomAD"
)

# Update counts
repo.update_counts(file_id=1, row_count=1000, column_count=15)

# Rename file
repo.rename(file_id=1, new_name="new_name.csv", new_path="data/new_name.csv")

# Get children
children = repo.get_children(file_id=1)
```

### VariantRepository

```python
from src.database import VariantRepository

repo = VariantRepository()

# Bulk create
variants = [
    {"file_id": 1, "row_index": 0, "chromosome": "1", "position": 12345, ...},
    {"file_id": 1, "row_index": 1, "chromosome": "1", "position": 12346, ...},
]
count = repo.create_bulk(variants)

# Find by file with pagination
variants = repo.find_by_file(file_id=1, limit=100, offset=0)

# Find by genomic position
variants = repo.find_by_position(
    chromosome="1", position=12345, ref_allele="A", alt_allele="G"
)

# Find by gene
variants = repo.find_by_gene(gene="BRCA1", limit=50)

# Filter variants
variants, total = repo.filter_variants(
    file_id=1,
    filters={"gene": "BRCA1", "consequence": "missense_variant"},
    limit=100,
    offset=0
)

# Count variants
count = repo.count_by_file(file_id=1)
```

### AnnotationRepository

```python
from src.database import AnnotationRepository

repo = AnnotationRepository()

# Bulk create
annotations = [
    {"variant_id": 1, "tool_name": "SpliceAI", "score_value": 0.85, ...},
    {"variant_id": 2, "tool_name": "CADD", "score_value": 25.3, ...},
]
count = repo.create_bulk(annotations)

# Find by variant
annotations = repo.find_by_variant(variant_id=1, tool_name="SpliceAI")

# Find by score range
high_scores = repo.find_by_score_range(
    tool_name="CADD", min_score=20.0, max_score=30.0
)
```

### AggregationRepository

```python
from src.database import AggregationRepository

repo = AggregationRepository()

# Get cached value
agg = repo.get_cached(
    file_id=1,
    column_name="CADD_score",
    operation="AVG",
    filter_json='{"gene": "BRCA1"}'
)

# Set cache with TTL
repo.set_cache(
    file_id=1,
    column_name="CADD_score",
    operation="AVG",
    result_value=18.7,
    filter_json='{"gene": "BRCA1"}',
    ttl_hours=24
)

# Invalidate file caches
count = repo.invalidate_by_file(file_id=1)

# Cleanup expired caches
count = repo.cleanup_expired()
```

---

## Database Initialization

### Using init_db()

```python
from flask import Flask
from src.database import init_db

app = Flask(__name__)
init_db(app, create_tables=True)
```

### Using Alembic Migrations

```bash
# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Downgrade
alembic downgrade -1

# Create new migration (manual)
alembic revision -m "Description"
```

---

## Configuration

### Settings

Configure database in `.env.development`:

```bash
DATABASE_PATH=instance/kath.db
DATABASE_ECHO=false
```

### Python Settings

```python
from src.settings import get_settings

settings = get_settings()
print(settings.database_path)  # "instance/kath.db"
print(settings.database_echo)  # False
```

---

## Connection Pooling

SQLite connection pooling configuration:

- **Pool Size**: 10 connections
- **Pool Recycle**: 3600 seconds (1 hour)
- **Pool Pre-Ping**: True (verify before use)
- **Connection Timeout**: 30 seconds
- **Check Same Thread**: False (multi-threaded access)

---

## Migrations

### Current Migrations

1. **94de6bf2874c** - Initial database schema (2025-10-28)
   - Creates: workspaces, files, variants, annotations, aggregations
   - 22 indexes for performance

### Creating Manual Migrations

```python
"""Description

Revision ID: <generated>
Revises: 94de6bf2874c
Create Date: <timestamp>
"""
from alembic import op
import sqlalchemy as sa

revision = '<generated>'
down_revision = '94de6bf2874c'

def upgrade() -> None:
    # Add new column
    op.add_column('variants', sa.Column('new_field', sa.String(255)))

def downgrade() -> None:
    # Remove column
    op.drop_column('variants', 'new_field')
```

---

## Performance Optimization

### Index Strategy

- **Primary Keys**: Auto-indexed
- **Foreign Keys**: Indexed for JOIN performance
- **Lookup Fields**: chromosome, gene, variant_id, gen_pos
- **Composite Indexes**: file_id + row_index, tool_name + score_value

### Query Optimization

```python
# Use bulk operations
repo.create_bulk(variants)  # Much faster than individual creates

# Use pagination
variants = repo.find_by_file(file_id=1, limit=100, offset=0)

# Leverage indexes
variants = repo.find_by_gene("BRCA1")  # Uses ix_variants_gene

# Cache aggregations
agg = repo.get_cached(...)  # Instant if cached
```

### Expected Performance

- **Lookups**: 10-100x faster than CSV scanning
- **Aggregations**: Instant (cached) vs seconds (CSV)
- **Concurrent Access**: No file locking issues
- **Scalability**: Handles millions of variants

---

## Testing

### Unit Tests

```python
from src.database import WorkspaceRepository, db

def test_workspace_creation():
    repo = WorkspaceRepository()
    workspace = repo.create(id="test-uuid", name="Test")
    assert workspace.id == "test-uuid"
    assert workspace.name == "Test"
```

### Integration Tests

```python
from src.database import init_db
from flask import Flask

def test_full_workflow():
    app = Flask(__name__)
    init_db(app)

    with app.app_context():
        # Test workspace -> file -> variant creation
        workspace_repo = WorkspaceRepository()
        workspace = workspace_repo.create(id="uuid", name="Test")

        file_repo = FileRepository()
        file = file_repo.create(
            workspace_id="uuid",
            name="test.csv",
            path="test.csv",
            file_type="file"
        )

        variant_repo = VariantRepository()
        variant = variant_repo.create(
            file_id=file.id,
            row_index=0,
            chromosome="1",
            position=12345
        )

        assert variant.file_id == file.id
```

---

## Troubleshooting

### Common Issues

**1. Database Locked**

```
Solution: Check connection pool settings, ensure proper session cleanup
```

**2. Foreign Key Constraint Failed**

```
Solution: Ensure parent records exist before creating children
```

**3. Migration Conflicts**

```bash
# Check current version
alembic current

# Reset to specific version
alembic downgrade <revision>
```

---

## Future Enhancements

- [ ] Add Flask-Migrate for autogenerate support
- [ ] Implement database replication
- [ ] Add query result caching layer
- [ ] Create database backup utilities
- [ ] Add full-text search indexes

---

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Schema design document
