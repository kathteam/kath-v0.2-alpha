# KATH Database Schema Design

**Date**: 2025-10-28
**Phase**: Phase 2 - Database Migration (Task 2.1)
**Purpose**: Replace CSV-based storage with SQLite database

---

## Executive Summary

This document defines the database schema for KATH's genetic analysis platform, transitioning from CSV file storage to a relational SQLite database. The schema supports:

- Multi-user workspaces with file hierarchies
- Genetic variant storage with annotations
- Integration with analysis tools (SpliceAI, CADD, REVEL)
- Cached aggregations for performance
- Pagination and filtering

---

## Current CSV Data Structure Analysis

### Data Sources Supported

1. **gnomAD** - Genome Aggregation Database
2. **ClinVar** - Clinical significance database
3. **LOVD** - Leiden Open Variation Database
4. **Custom Files** - User-uploaded genetic data

### Current CSV Columns (Inferred from Code)

Based on analysis of `src/tools/` and `src/data/refactoring.py`:

**Core Variant Data**:

- `gen_pos` - Genomic position in format: `chrom-pos-ref-alt` (e.g., `1-12345-A-G`)
- `chromosome` - Chromosome number/name
- `position` - Genomic position
- `ref_allele` - Reference allele
- `alt_allele` - Alternative allele
- `variant_id` - Variant identifier (gnomAD ID, rs number)
- `gene` - Gene symbol
- `transcript` - Transcript ID
- `consequence` - Variant consequence/effect

**Analysis Tool Annotations**:

- SpliceAI scores (delta scores for splice sites)
- CADD scores (pathogenicity prediction)
- REVEL scores (pathogenicity prediction)

### Current File Operations

Based on `src/routes/workspace_route.py`:

- GET `/workspace` - List files in workspace
- GET `/workspace/<path>` - Read file with pagination
- PUT `/workspace/<path>` - Save/update file
- POST `/workspace/<path>` - Create new file/directory
- DELETE `/workspace/<path>` - Delete file/directory
- PUT `/workspace/rename/<path>` - Rename file/directory

### Current Pagination/Filtering

- Page-based pagination (`page`, `rowsPerPage`)
- Filtering by column values
- Sorting by columns
- Aggregations (SUM, AVG, MIN, MAX, COUNT)

---

## Proposed Database Schema

### Design Principles

1. **Normalized Structure**: Reduce data redundancy
2. **Performance**: Indexes on frequently queried columns
3. **Backward Compatibility**: Support existing API operations
4. **Extensibility**: Easy to add new analysis tools
5. **Data Integrity**: Foreign key constraints

### Entity-Relationship Diagram (Textual)

```
Workspaces (1) ----< (N) Files
Files (1) ----< (N) Variants
Variants (1) ----< (N) Annotations
Files (1) ----< (N) Aggregations
```

---

## Table Definitions

### 1. `workspaces` Table

Stores user workspace information.

```sql
CREATE TABLE workspaces (
    id TEXT PRIMARY KEY,                          -- UUID from headers
    name TEXT NOT NULL,                           -- Workspace name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workspaces_created_at ON workspaces(created_at);
```

**Columns**:

- `id` (TEXT, PK): User's UUID from request headers
- `name` (TEXT): Workspace name (defaults to UUID if not set)
- `created_at` (TIMESTAMP): Workspace creation time
- `updated_at` (TIMESTAMP): Last modification time

**Use Cases**:

- Track user workspaces
- Manage workspace-level settings
- Support future multi-user features

---

### 2. `files` Table

Stores file metadata within workspaces.

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,                   -- Foreign key to workspaces
    name TEXT NOT NULL,                           -- File name (e.g., "variants.csv")
    path TEXT NOT NULL,                           -- Relative path within workspace
    file_type TEXT NOT NULL,                      -- "file" or "folder"
    parent_id INTEGER,                            -- For directory hierarchy
    row_count INTEGER DEFAULT 0,                  -- Number of variant rows
    column_count INTEGER DEFAULT 0,               -- Number of columns
    data_source TEXT,                             -- "gnomAD", "ClinVar", "LOVD", "Custom"
    header_json TEXT,                             -- JSON array of column names
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE (workspace_id, path)
);

CREATE INDEX idx_files_workspace ON files(workspace_id);
CREATE INDEX idx_files_path ON files(workspace_id, path);
CREATE INDEX idx_files_parent ON files(parent_id);
CREATE INDEX idx_files_type ON files(file_type);
```

**Columns**:

- `id` (INTEGER, PK): Auto-incrementing file ID
- `workspace_id` (TEXT, FK): Workspace owner
- `name` (TEXT): File name without path
- `path` (TEXT): Full relative path (e.g., "folder/subfolder/file.csv")
- `file_type` (TEXT): "file" or "folder" (for directory support)
- `parent_id` (INTEGER, FK): Parent directory (NULL for root files)
- `row_count` (INTEGER): Cached row count for pagination
- `column_count` (INTEGER): Number of columns
- `data_source` (TEXT): Data source identifier
- `header_json` (TEXT): JSON array of column names (e.g., `["chr", "pos", "ref", "alt"]`)
- `created_at` (TIMESTAMP): File creation time
- `updated_at` (TIMESTAMP): Last modification time

**Use Cases**:

- File tree navigation
- Pagination metadata (row counts)
- File type identification

---

### 3. `variants` Table

Stores genetic variant data (the core CSV data).

```sql
CREATE TABLE variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,                     -- Foreign key to files
    row_index INTEGER NOT NULL,                   -- Original CSV row index

    -- Core variant information
    chromosome TEXT,                              -- Chromosome (1-22, X, Y, MT)
    position INTEGER,                             -- Genomic position
    ref_allele TEXT,                              -- Reference allele
    alt_allele TEXT,                              -- Alternative allele
    variant_id TEXT,                              -- gnomAD ID, rs number, etc.
    gen_pos TEXT,                                 -- Combined: "chr-pos-ref-alt"

    -- Gene/transcript information
    gene TEXT,                                    -- Gene symbol
    transcript TEXT,                              -- Transcript ID
    consequence TEXT,                             -- Variant consequence

    -- Additional data (JSON for flexibility)
    data_json TEXT,                               -- JSON object for other columns

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX idx_variants_file ON variants(file_id);
CREATE INDEX idx_variants_row_index ON variants(file_id, row_index);
CREATE INDEX idx_variants_lookup ON variants(chromosome, position, ref_allele, alt_allele);
CREATE INDEX idx_variants_gene ON variants(gene);
CREATE INDEX idx_variants_gen_pos ON variants(gen_pos);
CREATE INDEX idx_variants_variant_id ON variants(variant_id);
```

**Columns**:

- `id` (INTEGER, PK): Auto-incrementing variant ID
- `file_id` (INTEGER, FK): Parent file
- `row_index` (INTEGER): Original CSV row number (for ordering/pagination)
- `chromosome` (TEXT): Chromosome identifier
- `position` (INTEGER): Genomic position
- `ref_allele` (TEXT): Reference nucleotide(s)
- `alt_allele` (TEXT): Alternative nucleotide(s)
- `variant_id` (TEXT): External identifier (rs number, gnomAD ID)
- `gen_pos` (TEXT): Combined position format `chr-pos-ref-alt`
- `gene` (TEXT): Gene symbol
- `transcript` (TEXT): Transcript identifier
- `consequence` (TEXT): Variant effect/consequence
- `data_json` (TEXT): JSON object storing other CSV columns not explicitly modeled
- `created_at` (TIMESTAMP): Row creation time

**Use Cases**:

- Primary data storage for variants
- Fast lookups by genomic position
- Gene-based queries
- Pagination support via row_index

**Example `data_json`**:

```json
{
  "af_global": 0.001234,
  "ac_global": 152,
  "quality_score": 30,
  "filter": "PASS",
  "additional_field": "value"
}
```

---

### 4. `annotations` Table

Stores analysis tool results (SpliceAI, CADD, REVEL).

```sql
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,                  -- Foreign key to variants
    tool_name TEXT NOT NULL,                      -- "SpliceAI", "CADD", "REVEL"
    annotation_type TEXT NOT NULL,                -- Score type (e.g., "delta_score", "phred")
    score_value REAL,                             -- Numeric score
    score_label TEXT,                             -- Label/classification (e.g., "High", "Pathogenic")
    metadata_json TEXT,                           -- JSON for additional tool-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
);

CREATE INDEX idx_annotations_variant ON annotations(variant_id);
CREATE INDEX idx_annotations_tool ON annotations(tool_name);
CREATE INDEX idx_annotations_type ON annotations(tool_name, annotation_type);
CREATE INDEX idx_annotations_score ON annotations(tool_name, score_value);
```

**Columns**:

- `id` (INTEGER, PK): Auto-incrementing annotation ID
- `variant_id` (INTEGER, FK): Associated variant
- `tool_name` (TEXT): Analysis tool name
- `annotation_type` (TEXT): Type of score/annotation
- `score_value` (REAL): Numeric score value
- `score_label` (TEXT): Classification label
- `metadata_json` (TEXT): Additional tool-specific data
- `created_at` (TIMESTAMP): Annotation creation time

**Tool-Specific Examples**:

**SpliceAI**:

```json
{
  "variant_id": 123,
  "tool_name": "SpliceAI",
  "annotation_type": "delta_score",
  "score_value": 0.85,
  "metadata_json": "{\"acceptor_gain\": 0.02, \"acceptor_loss\": 0.85, \"donor_gain\": 0.01, \"donor_loss\": 0.05}"
}
```

**CADD**:

```json
{
  "variant_id": 123,
  "tool_name": "CADD",
  "annotation_type": "phred_score",
  "score_value": 25.3,
  "score_label": "Likely Pathogenic"
}
```

**REVEL**:

```json
{
  "variant_id": 123,
  "tool_name": "REVEL",
  "annotation_type": "pathogenicity_score",
  "score_value": 0.72,
  "score_label": "Pathogenic"
}
```

---

### 5. `aggregations` Table

Caches computed aggregations for performance.

```sql
CREATE TABLE aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,                     -- Foreign key to files
    column_name TEXT NOT NULL,                    -- Column being aggregated
    operation TEXT NOT NULL,                      -- "SUM", "AVG", "MIN", "MAX", "COUNT"
    filter_json TEXT,                             -- JSON of applied filters
    result_value REAL NOT NULL,                   -- Aggregation result
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,                         -- Cache expiration

    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE (file_id, column_name, operation, filter_json)
);

CREATE INDEX idx_aggregations_file ON aggregations(file_id);
CREATE INDEX idx_aggregations_column ON aggregations(file_id, column_name);
CREATE INDEX idx_aggregations_expires ON aggregations(expires_at);
```

**Columns**:

- `id` (INTEGER, PK): Auto-incrementing aggregation ID
- `file_id` (INTEGER, FK): File being aggregated
- `column_name` (TEXT): Column name
- `operation` (TEXT): Aggregation operation
- `filter_json` (TEXT): JSON representation of applied filters
- `result_value` (REAL): Cached result
- `cached_at` (TIMESTAMP): When cache was created
- `expires_at` (TIMESTAMP): Cache expiration time

**Use Cases**:

- Cache expensive aggregations (COUNT, AVG, SUM)
- Invalidate cache on file update
- Support filtered aggregations

**Example**:

```json
{
  "file_id": 5,
  "column_name": "CADD_score",
  "operation": "AVG",
  "filter_json": "{\"gene\": \"BRCA1\", \"consequence\": \"missense_variant\"}",
  "result_value": 18.7
}
```

---

## Migration Strategy

### Phase 1: Dual Storage (Weeks 1-2)

1. Implement database layer alongside CSV storage
2. Write to both CSV and database
3. Read from CSV (existing behavior)
4. Validate data consistency

### Phase 2: Read from Database (Week 3)

1. Switch reads to database
2. Keep CSV writes for rollback safety
3. Performance testing and optimization
4. Fix any issues

### Phase 3: Database-Only (Week 4)

1. Remove CSV write operations
2. Keep CSV files as backup
3. Add database migrations (Alembic)
4. Full production deployment

### Rollback Plan

- Keep CSV files for 30 days after migration
- Database dump scripts for backup
- Quick switch back to CSV if needed

---

## Data Migration Script

### High-Level Process

1. **Scan workspaces**: Iterate through `src/workspace/` directories
2. **Create workspace records**: Insert into `workspaces` table
3. **Process files**: For each CSV file:
   - Insert into `files` table
   - Parse CSV rows
   - Insert variants into `variants` table
   - Preserve row order via `row_index`
4. **Migrate annotations**: Extract existing tool results
5. **Verify integrity**: Compare row counts, spot-check data

### Example Migration Script Structure

```python
def migrate_csv_to_database(workspace_dir: str, db_session):
    for workspace_uuid in os.listdir(workspace_dir):
        # Create workspace
        workspace = Workspace(id=workspace_uuid, name=workspace_uuid)
        db_session.add(workspace)

        # Process files
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                if file.endswith('.csv'):
                    # Create file record
                    # Import CSV data
                    # Create variant records
                    pass

    db_session.commit()
```

---

## Performance Considerations

### Indexes

- **File lookups**: `idx_files_workspace`, `idx_files_path`
- **Variant queries**: `idx_variants_lookup`, `idx_variants_gene`
- **Pagination**: `idx_variants_row_index`
- **Tool results**: `idx_annotations_tool`

### Query Optimization

1. **Pagination**: Use `LIMIT` and `OFFSET` with row_index
2. **Filtering**: Indexed columns for WHERE clauses
3. **Aggregations**: Cached in `aggregations` table
4. **Joins**: Minimize joins, use indexed foreign keys

### Expected Performance Gains

- **Lookups**: 10-100x faster than CSV scanning
- **Aggregations**: Instant (cached) vs seconds (CSV scan)
- **Concurrent Access**: No file locking issues
- **Scalability**: Handles millions of variants

---

## API Compatibility

### Current API  Database Mapping

| Current Endpoint | Database Tables | Notes |
|------------------|-----------------|-------|
| GET `/workspace` | `files` | List files in workspace |
| GET `/workspace/<path>` | `files`, `variants` | Paginated variant data |
| PUT `/workspace/<path>` | `files`, `variants` | Update variant rows |
| POST `/workspace/<path>` | `files` | Create file/folder |
| DELETE `/workspace/<path>` | `files` (cascade) | Delete file and variants |
| PUT `/workspace/rename/<path>` | `files` | Update file path/name |

### Pagination

- **CSV**: Read entire file, slice rows
- **Database**: `SELECT * FROM variants WHERE file_id = ? ORDER BY row_index LIMIT ? OFFSET ?`

### Filtering

- **CSV**: Pandas DataFrame filtering
- **Database**: SQL WHERE clauses with indexes

### Aggregations

- **CSV**: Pandas groupby/agg operations
- **Database**: SQL aggregation functions with caching

---

## Success Criteria

- [x] Schema supports all current CSV data types
- [x] Indexes defined for common query patterns
- [x] Foreign key relationships maintain data integrity
- [x] Backward compatible with existing API
- [x] Migration strategy documented
- [x] Performance improvement plan defined
- [ ] ER diagram created (visual)
- [ ] SQLAlchemy models implemented
- [ ] Migration script written

---

## Next Steps

1. **Create SQLAlchemy Models** (Task 2.1 continuation)
2. **Implement Database Layer** (Task 2.2)
3. **Write Migration Script**
4. **Test with Sample Data**
5. **Deploy to Staging**

---

## References

- Flask-SQLAlchemy: <https://flask-sqlalchemy.palletsprojects.com/>
- Alembic Migrations: <https://alembic.sqlalchemy.org/>
- SQLite Documentation: <https://www.sqlite.org/docs.html>
- gnomAD: <https://gnomad.broadinstitute.org/>
- ClinVar: <https://www.ncbi.nlm.nih.gov/clinvar/>
