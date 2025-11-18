# Delta-Sync Implementation Guide

## Overview

Delta-Sync is an intelligent data synchronization system that detects existing data and only downloads new/updated records from external sources. This optimization reduces bandwidth usage, improves performance, and enables smarter data management for variant databases.

## Architecture

### Components

#### 1. **DeltaSyncManager** (`app/back_end/src/data/delta_sync.py`)

Main class managing delta-sync detection and download optimization.

**Key Responsibilities:**
- Detect existing data in database for each source
- Check source version compatibility
- Determine freshness of existing data
- Track import timestamps
- Manage sync statistics

**Source Configuration:**
```python
SOURCE_VERSIONS = {
    "clinvar": "2024.01",     # Update when ClinVar format changes
    "lovd": "2024.01",         # Update when LOVD format changes
    "gnomad": "4.0",           # Update when gnomAD version changes
    "custom": "1.0",           # Custom data version
}

FRESHNESS_WINDOW = {
    "clinvar": 24,    # Hours - ClinVar updated daily
    "lovd": 168,      # Hours - LOVD updated weekly
    "gnomad": 720,    # Hours - gnomAD updated monthly
    "custom": 8760,   # Hours - Custom data considered fresh for 1 year
}
```

#### 2. **DeltaSyncStatus** (`app/back_end/src/data/delta_sync.py`)

Data structure representing sync status for a source.

**Properties:**
- `has_existing_data`: Whether database has records for this source
- `record_count`: Number of existing records
- `latest_import`: Timestamp of latest import
- `source_version`: Version of source data currently in database
- `requires_full_sync`: Whether full resync is needed

#### 3. **SourceVariant Model** (`app/back_end/src/models/source_variant.py`)

Stores pre-merge variants from external sources with import tracking.

**Key Fields:**
- `file_id`: Parent file reference
- `source_database`: Source name (clinvar, lovd, gnomad, custom)
- `chromosome`, `position`: Genomic coordinates
- `gen_pos`: Canonical "chr-pos-ref-alt" format
- `import_timestamp`: When this record was imported
- `source_version`: Version of source data at import time
- `source_data`: JSON field with source-specific attributes

#### 4. **Repository Classes** (`app/back_end/src/database/repositories.py`)

Database access layer for Phase 2 models.

**SourceVariantRepository:**
- `create_bulk()`: Efficiently create multiple variants
- `find_by_file()`: Query variants by file and source
- `count_by_source()`: Get count breakdown by source
- `find_by_position()`: Find variants at genomic location

**MergedVariantRepository, FilteredVariantRepository, WorkflowAuditRepository:**
- Similar specialized query methods
- Bulk operations for performance
- Aggregation queries for statistics

## Usage Patterns

### 1. Check Sync Status

```python
from src.data.delta_sync import DeltaSyncManager

sync_mgr = DeltaSyncManager()

# Check status for a specific source
status = sync_mgr.check_sync_status(
    workspace_id="user-uuid",
    file_id=123,
    source_database="clinvar",
    current_version="2024.01"
)

if status.has_existing_data:
    print(f"Found {status.record_count} existing records")
    print(f"Last import: {status.latest_import}")

if status.requires_full_sync:
    print("Version mismatch or data too old - full resync needed")
```

### 2. Determine Download Decision

```python
should_download = sync_mgr.should_download(
    workspace_id="user-uuid",
    file_id=123,
    source_database="clinvar",
    current_version="2024.01",
    force_refresh=False  # Set True to force download
)

if should_download:
    # Proceed with download
    download_clinvar_data(...)
    sync_mgr.mark_download_complete(
        file_id=123,
        source_database="clinvar",
        imported_record_count=1500,
        source_version="2024.01"
    )
else:
    print("Using existing data - skip download")
```

### 3. Get Comprehensive Statistics

```python
# Get status for all sources in a file
all_statuses = sync_mgr.get_sync_status_for_file(
    workspace_id="user-uuid",
    file_id=123
)

for source_db, status in all_statuses.items():
    print(f"{source_db}: {status.record_count} records")

# Get workspace-wide statistics
stats = sync_mgr.get_sync_statistics(workspace_id="user-uuid")
print(f"Workspace has {stats['total_files']} files")
print(f"Files with source data: {stats['files_with_source_data']}")
print(f"Sources available: {stats['sources_represented']}")
print(f"By source: {stats['by_source']}")
```

### 4. Integration with Download Route

**Enhanced workflow_download_route.py:**

```python
@workspace_download_route_bp.route(f"{WORKSPACE_DOWNLOAD_ROUTE}/<path:relative_path>",
                                   methods=["GET"])
def get_workspace_download(relative_path):
    # ... validation ...

    source = request.args.get("source")
    uuid = request.headers.get("uuid")
    file_id = get_or_create_file(uuid, relative_path).id

    # Check delta-sync status
    sync_mgr = DeltaSyncManager()
    should_download = sync_mgr.should_download(
        workspace_id=uuid,
        file_id=file_id,
        source_database=source,
        force_refresh=request.args.get("force_refresh", False)
    )

    if not should_download:
        return jsonify({
            "message": "Using existing database records",
            "action": "skip_download"
        }), 200

    # Proceed with download
    try:
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {"type": "info", "message": f"Downloading new data from {source}..."},
            uuid, sid
        )

        record_count = download_selected_database_for_eys_gene(
            database_name=source,
            save_path=destination_path,
            override=override
        )

        # Update delta-sync metadata
        sync_mgr.mark_download_complete(
            file_id=file_id,
            source_database=source,
            imported_record_count=record_count,
            source_version="2024.01"
        )

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"Downloaded {record_count} new records from {source}"
            },
            uuid, sid
        )
    except Exception as e:
        # Error handling
        pass
```

## Version Management

### Source Version Updates

Update `SOURCE_VERSIONS` in `DeltaSyncManager` when:
1. Source database schema changes
2. New major version of source is released
3. Data format or field structure changes

**Example:**
```python
# Update ClinVar version from 2024.01 to 2024.06
SOURCE_VERSIONS = {
    "clinvar": "2024.06",  # Version incremented
    ...
}
```

When version changes, existing data triggers `requires_full_sync=True`, forcing re-download and database update.

### Freshness Window Updates

Adjust `FRESHNESS_WINDOW` when:
1. Source updates schedule changes
2. Data staleness tolerance changes
3. Network/bandwidth constraints change

**Example:**
```python
# ClinVar now updates twice daily instead of daily
FRESHNESS_WINDOW = {
    "clinvar": 12,  # Reduced from 24 to 12 hours
    ...
}
```

## Database Schema

### SourceVariant Table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Auto-incrementing primary key |
| `file_id` | Integer FK | Parent file reference |
| `source_database` | String(50) | Source name, indexed |
| `chromosome` | String(10) | Chromosome identifier |
| `position` | Integer | Genomic position |
| `ref_allele` | String(255) | Reference allele |
| `alt_allele` | String(255) | Alternative allele |
| `gen_pos` | String(255) | Canonical format, indexed |
| `import_timestamp` | DateTime | When record was imported, indexed |
| `source_version` | String(50) | Version of source at import |
| `source_data` | Text | JSON with source-specific fields |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

**Indexes:**
- `idx_sv_file_source`: (file_id, source_database)
- `idx_sv_coordinates`: (chromosome, position, ref_allele, alt_allele)
- `idx_sv_import_time`: (import_timestamp)

## Performance Considerations

### 1. Bulk Operations

Use repository bulk methods for large imports:

```python
# ✓ Good: ~1000x faster for large datasets
repo = SourceVariantRepository()
count = repo.create_bulk([variant1, variant2, ...])

# ✗ Bad: Creates N database transactions
for variant in variants:
    repo.create(variant)
```

### 2. Lazy Loading

Use `lazy="dynamic"` for relationships to avoid loading all records:

```python
# ✓ Good: Only loads records when accessed
variants = file.source_variants.filter(...).limit(100).all()

# ✗ Bad: Loads all variants into memory
all_variants = file.source_variants.all()
```

### 3. Caching

Import timestamps are cached with 5-minute TTL to reduce queries:

```python
# ✓ Uses cache - fast
latest = sync_mgr.get_last_import_timestamp(...)  # Cached

# Cache invalidated after modifications
sync_mgr.mark_download_complete(...)  # Invalidates cache
```

## Troubleshooting

### Issue: "Version mismatch requires full resync"

**Cause:** Source version in database differs from current version

**Solution:**
1. Check if source actually updated (check release notes)
2. Update `SOURCE_VERSIONS` if intentional
3. Users can force refresh with `?force_refresh=true`

### Issue: Stale data not re-downloading

**Cause:** Freshness window is too long

**Solution:**
1. Reduce `FRESHNESS_WINDOW` for that source
2. Manually trigger refresh: `?force_refresh=true`

### Issue: Performance degradation

**Cause:** Too many records in SourceVariant table

**Solution:**
1. Archive old imports: `SourceVariantRepository().delete()` old file_ids
2. Implement retention policy
3. Use pagination for queries

## Migration Guide

### From Phase 1 to Phase 2

1. **Install Models:**
   ```bash
   # Models already present in codebase
   alembic upgrade head
   ```

2. **Enable Delta-Sync in Download Route:**
   - Import `DeltaSyncManager`
   - Add sync status check before download
   - Call `mark_download_complete` after successful import

3. **Update Download Functions:**
   - Return record count from import functions
   - Pass count to `mark_download_complete`

4. **Testing:**
   ```bash
   pytest tests/test_delta_sync.py -v
   pytest tests/test_repositories.py -v
   ```

## Future Enhancements

1. **Incremental Syncing:**
   - Support downloading only changed records
   - Requires source API support for change detection

2. **Merge Optimization:**
   - Use import timestamps to identify new records for merging
   - Skip re-merging unchanged records

3. **Distributed Sync:**
   - Support multiple worker nodes
   - Coordinate imports across instances

4. **Analytics Dashboard:**
   - Visualize source composition over time
   - Track import frequency and volume
   - Monitor sync performance metrics

## Testing

### Unit Tests

```python
def test_check_sync_status_no_existing_data():
    sync_mgr = DeltaSyncManager()
    status = sync_mgr.check_sync_status(
        workspace_id="test", file_id=1, source_database="clinvar"
    )
    assert not status.has_existing_data
    assert status.requires_full_sync

def test_should_download_with_existing_fresh_data():
    # Setup existing records
    sync_mgr = DeltaSyncManager()
    assert not sync_mgr.should_download(
        workspace_id="test", file_id=1, source_database="clinvar"
    )

def test_force_refresh_overrides_freshness():
    sync_mgr = DeltaSyncManager()
    assert sync_mgr.should_download(
        workspace_id="test", file_id=1,
        source_database="clinvar",
        force_refresh=True
    )
```

## Summary

Delta-Sync provides:
- ✅ Intelligent download detection
- ✅ Version-aware synchronization
- ✅ Freshness tracking
- ✅ Source-specific configuration
- ✅ Performance optimization through bulk operations
- ✅ Comprehensive statistics and monitoring
- ✅ Flexible refresh policies

This enables the system to manage large genetic datasets efficiently while maintaining data currency and accuracy.
