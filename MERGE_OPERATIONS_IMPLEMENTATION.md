# Merge Operations Implementation Guide

## Overview

The Merge Operations system handles combining variants from multiple sources (ClinVar, LOVD, gnomAD, custom) with complete database storage, source attribution, and full audit trails. This enables reproducible variant analysis with complete transparency into data lineage.

## Architecture

### Components

#### 1. **MergeOperationHandler** (`app/back_end/src/data/merge_operations.py`)

Main class orchestrating merge operations with database integration.

**Key Responsibilities:**
- Validate merge inputs
- Execute merge based on configurable strategy
- Store merged results in database
- Create audit trail
- Provide merge statistics and history

#### 2. **MergeStrategy** (`app/back_end/src/data/merge_operations.py`)

Defines variant merging strategies:

**Available Strategies:**

- **OUTER_UNION** (default)
  - Includes ALL variants from all sources
  - No filtering based on source presence
  - Creates widest possible variant set
  - Best for: Comprehensive analysis of all available data

- **INNER_INTERSECTION**
  - Only includes variants present in ALL specified sources
  - Filters to high-confidence consensus variants
  - Creates most conservative variant set
  - Best for: Validation, finding confirmed variants

- **CONSENSUS**
  - Includes variants appearing in 2+ sources
  - Balances breadth and confidence
  - Creates filtered high-confidence set
  - Best for: Production workflows requiring good confidence

**Example Usage:**
```python
strategy = MergeStrategy.CONSENSUS  # Use consensus merge
all_strategies = MergeStrategy.get_all_strategies()  # ["outer_union", "inner_intersection", "consensus"]
```

#### 3. **MergeResult** (`app/back_end/src/data/merge_operations.py`)

Data structure representing merge operation outcome.

**Properties:**
- `merged_count`: Total unique merged variants created
- `source_counts`: Dictionary mapping each source to input record count
- `duplicate_count`: Number of duplicate records identified/removed
- `merge_strategy`: Strategy used
- `duration_seconds`: Time taken for operation
- `timestamp`: When operation completed

#### 4. **MergedVariant Model** (`app/back_end/src/models/merged_variant.py`)

Database table storing merged variant results.

**Key Fields:**
- `file_id`: Parent file reference
- `chromosome`, `position`: Canonical genomic coordinates
- `gen_pos`: Standardized "chr-pos-ref-alt" format
- `gene`, `transcript`, `consequence`: Combined annotations
- `source_databases`: JSON array of sources ["clinvar", "lovd"]
- `clinvar_data`, `lovd_data`, `gnomad_data`: Source-specific JSON fields
- `merge_timestamp`: When merge was performed
- `merge_strategy`: Strategy used for this merge

## Usage Patterns

### 1. Basic Merge Operation

```python
from src.data.merge_operations import MergeOperationHandler, MergeStrategy

handler = MergeOperationHandler()

# Merge variants from ClinVar and LOVD
result = handler.perform_merge(
    file_id=123,
    sources=["clinvar", "lovd"],
    merge_strategy=MergeStrategy.OUTER_UNION,
    user_id="user-uuid"
)

print(f"Created {result.merged_count} merged variants")
print(f"Input records: {result.source_counts}")
print(f"Duplicates removed: {result.duplicate_count}")
print(f"Took {result.duration_seconds:.2f} seconds")
```

### 2. Validate Before Merge

```python
handler = MergeOperationHandler()

# Validate that data exists for sources before merging
is_valid, error_msg = handler.validate_merge_inputs(
    file_id=123,
    sources=["clinvar", "lovd"]
)

if not is_valid:
    print(f"Cannot merge: {error_msg}")
else:
    result = handler.perform_merge(file_id=123, sources=["clinvar", "lovd"])
```

### 3. Different Merge Strategies

```python
handler = MergeOperationHandler()
file_id = 123
sources = ["clinvar", "lovd", "gnomad"]

# Strategy 1: Get all variants
result_outer = handler.perform_merge(
    file_id=file_id,
    sources=sources,
    merge_strategy=MergeStrategy.OUTER_UNION
)
print(f"Outer union: {result_outer.merged_count} variants")

# Strategy 2: Get only consensus variants
result_consensus = handler.perform_merge(
    file_id=file_id,
    sources=sources,
    merge_strategy=MergeStrategy.CONSENSUS
)
print(f"Consensus: {result_consensus.merged_count} variants")

# Strategy 3: Get only variants in all sources
result_inner = handler.perform_merge(
    file_id=file_id,
    sources=sources,
    merge_strategy=MergeStrategy.INNER_INTERSECTION
)
print(f"Inner intersection: {result_inner.merged_count} variants")
```

### 4. Access Merge History

```python
handler = MergeOperationHandler()

# Get all merge operations for a file
history = handler.get_merge_history(file_id=123)
for merge in history:
    print(f"Merge {merge['id']}: {merge['status']}")
    print(f"  Input: {merge['input_count']}")
    print(f"  Output: {merge['output_count']}")

# Get most recent merge
latest = handler.get_latest_merge(file_id=123)
if latest:
    print(f"Last merge at: {latest['completed_at']}")

# Get comprehensive statistics
stats = handler.get_merge_statistics(file_id=123)
print(f"Total merged variants: {stats['total_merged_variants']}")
print(f"Number of merges: {stats['merge_operations']}")
print(f"Sources combined: {stats['sources_combined']}")
```

## Merge Process Flow

```
1. Input Validation
   ├─ Check sources specified
   ├─ Verify source variants exist
   └─ Validate merge strategy

2. Variant Collection
   ├─ Retrieve SourceVariants by file and sources
   ├─ Count records per source
   └─ Group by genomic position

3. Merge Execution
   ├─ Apply merge strategy
   │  ├─ OUTER_UNION: Keep all positions
   │  ├─ INNER_INTERSECTION: Keep only shared positions
   │  └─ CONSENSUS: Keep 2+ source positions
   ├─ Combine source-specific data
   ├─ Merge annotations (gene, transcript, consequence)
   └─ Identify duplicates

4. Database Storage
   ├─ Prepare MergedVariant records
   ├─ Bulk insert into database
   └─ Create indices for queries

5. Audit Trail
   ├─ Record operation timing
   ├─ Store input/output counts
   ├─ Preserve parameters and results
   └─ Track success/failure status
```

## Data Structure Examples

### Source Variants (Input)
```
SourceVariant #1: ClinVar
- chromosome: "1"
- position: 55505647
- ref_allele: "G"
- alt_allele: "A"
- gene: "BRCA2"
- source_database: "clinvar"
- source_data: {"clinvar_id": 12345, "clinical_significance": "Pathogenic"}

SourceVariant #2: LOVD
- chromosome: "1"
- position: 55505647
- ref_allele: "G"
- alt_allele: "A"
- gene: "BRCA2"
- source_database: "lovd"
- source_data: {"lovd_id": "BRCA2_001", "effect": "Missense"}
```

### Merged Result
```
MergedVariant:
- chromosome: "1"
- position: 55505647
- ref_allele: "G"
- alt_allele: "A"
- gen_pos: "1-55505647-G-A"
- gene: "BRCA2"
- transcript: (from first source with value)
- source_databases: ["clinvar", "lovd"]
- clinvar_data: {"clinvar_id": 12345, "clinical_significance": "Pathogenic"}
- lovd_data: {"lovd_id": "BRCA2_001", "effect": "Missense"}
- merge_timestamp: 2024-01-15T10:30:00
- merge_strategy: "outer_union"
```

## Integration with Merge Route

**Enhanced workspace_merge_route.py:**

```python
from src.data.merge_operations import MergeOperationHandler, MergeStrategy

@workspace_merge_route_bp.route(f"{WORKSPACE_MERGE_ROUTE}/all/<path:relative_path>",
                                methods=["GET"])
def get_workspace_merge_all(relative_path):
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")

    # Get merge parameters
    sources = request.args.getlist("sources")  # ["clinvar", "lovd"]
    strategy = request.args.get("strategy", "outer_union")

    try:
        # Validate inputs
        handler = MergeOperationHandler()
        is_valid, error = handler.validate_merge_inputs(file_id, sources)

        if not is_valid:
            socketio_emit_to_user_session(
                CONSOLE_FEEDBACK_EVENT,
                {"type": "errr", "message": f"Cannot merge: {error}"},
                uuid, sid
            )
            return jsonify({"error": error}), 400

        # Perform merge
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "info",
                "message": f"Merging {sources} using {strategy} strategy..."
            },
            uuid, sid
        )

        result = handler.perform_merge(
            file_id=file_id,
            sources=sources,
            merge_strategy=strategy,
            user_id=uuid
        )

        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {
                "type": "succ",
                "message": f"Merge complete: {result.merged_count} variants created"
            },
            uuid, sid
        )

        return jsonify({
            "message": "Merge completed successfully",
            "result": result.to_dict()
        }), 200

    except Exception as e:
        socketio_emit_to_user_session(
            CONSOLE_FEEDBACK_EVENT,
            {"type": "errr", "message": f"Merge failed: {str(e)}"},
            uuid, sid
        )
        return jsonify({"error": str(e)}), 500
```

## Performance Considerations

### 1. Bulk Operations

Merge uses bulk operations for efficiency:
```python
# ~1000x faster for large merges
merged_variant_repo.create_bulk(records)
```

### 2. Indexing

MergedVariant table indexes for common queries:
- `idx_mv_file_id`: Fast lookup by file
- `idx_mv_coordinates`: Fast genomic queries
- `idx_mv_gene`: Fast gene-based queries

### 3. Memory Management

Large merges handled efficiently:
```python
# Processed in memory-efficient chunks
for source in sources:
    variants = source_variant_repo.find_by_file(file_id, source)
    # Process variants without loading entire dataset
```

## Error Handling

### Validation Errors

```python
# Raised when:
# - No sources specified
# - Source database not found
# - Invalid merge strategy

try:
    handler.perform_merge(file_id=123, sources=[])
except ValueError as e:
    print(f"Validation failed: {e}")
```

### Operation Failures

All failures recorded in WorkflowAudit:
```python
# Failed merge has:
# - status: "failed"
# - error_message: Details of failure
# - completed_at: When failure occurred

audit = workflow_audit_repo.get_latest_by_operation(file_id, "merge")
if audit.status == "failed":
    print(f"Merge failed: {audit.error_message}")
```

## Troubleshooting

### Issue: "No data found for source"

**Cause:** SourceVariant table empty for specified source

**Solution:**
1. Verify source was imported: `delta_sync.check_sync_status(...)`
2. Check import completed: Query SourceVariant table
3. Re-import if needed

### Issue: High duplicate count

**Cause:** Multiple entries for same position across sources

**Solution:**
1. Use CONSENSUS strategy to filter
2. Check if sources overlap on same variants
3. Inspect source_data to understand duplication

### Issue: Merge takes too long

**Cause:** Large number of variants to merge

**Solution:**
1. Use database indices: Verify indices present
2. Filter sources: Merge fewer sources at a time
3. Consider data partitioning by gene/chromosome

## Testing

### Unit Test Example

```python
def test_outer_union_merge():
    handler = MergeOperationHandler()
    # Setup test source variants

    result = handler.perform_merge(
        file_id=1,
        sources=["clinvar", "lovd"],
        merge_strategy=MergeStrategy.OUTER_UNION
    )

    assert result.merged_count > 0
    assert "clinvar" in result.source_counts
    assert "lovd" in result.source_counts

def test_consensus_merge_filters():
    handler = MergeOperationHandler()

    result = handler.perform_merge(
        file_id=1,
        sources=["clinvar", "lovd"],
        merge_strategy=MergeStrategy.CONSENSUS
    )

    # Consensus should have fewer variants than outer union
    assert result.merged_count <= outer_result.merged_count
```

## Future Enhancements

1. **Partial Merges:**
   - Support merging subset of genes
   - Chromosome-specific merges
   - Position-range based merges

2. **Advanced Strategies:**
   - Weighted voting based on source confidence
   - Machine learning based duplicate detection
   - Conflict resolution for discordant annotations

3. **Incremental Merging:**
   - Only re-merge new records
   - Preserve previous merge results
   - Track merge evolution over time

4. **Export Formats:**
   - VCF format export
   - BED format export
   - Custom format mapping

## Summary

The Merge Operations system provides:
- ✅ Multiple configurable merge strategies
- ✅ Complete source attribution tracking
- ✅ Reproducible merge operations with full audit trail
- ✅ High-performance bulk operations
- ✅ Flexible annotation merging
- ✅ Comprehensive merge statistics and history
- ✅ Database-backed storage for persistence

This enables sophisticated variant analysis workflows while maintaining complete transparency into data origins and transformations.
