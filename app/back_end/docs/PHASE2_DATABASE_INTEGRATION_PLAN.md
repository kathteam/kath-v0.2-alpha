# Phase 2 Database Integration Plan

**Status**: Design Document
**Date**: 2025-11-18
**Version**: 1.0
**Scope**: Complete database integration for Phase 2 pipeline operations

---

## 1. Executive Summary

The Phase 2 pipeline implements a comprehensive variant analysis workflow with database-driven operations:

- **Delta-Sync**: Intelligent data synchronization with version control
- **Merge**: Multi-source variant consolidation with strategy options
- **Filter**: Quality control with 6 critical/soft validation rules
- **Analysis**: Integration of CADD, REVEL, SpliceAI scoring
- **Audit**: Complete operation tracking and workflow history

**Current Status**:
- ✅ All 41 Phase 2 API endpoints functional (100% test pass rate)
- ✅ Core database models defined and aligned
- ✅ Repository patterns established
- ⚠️  Some field name inconsistencies fixed
- ⚠️  Analysis linkage to FilteredVariant incomplete
- ⚠️  Missing some repository methods for cleanup operations

---

## 2. Database Architecture

### 2.1 Core Tables and Relationships

```
File (parent)
├── SourceVariant (raw imported variants by source)
│   ├── Properties: chromosome, position, ref_allele, alt_allele, gene, transcript
│   ├── Metadata: source_database, import_timestamp, source_version
│   └── Indexes: file_id, coordinates, gene, import_time
│
├── MergedVariant (consolidated multi-source variants)
│   ├── Properties: chromosome, position, ref_allele, alt_allele, gene, transcript
│   ├── Metadata: source_databases (JSON), merge_timestamp, merge_strategy
│   ├── Source data: clinvar_data, lovd_data, gnomad_data (JSON)
│   └── Indexes: file_id, coordinates, gene
│
├── FilteredVariant (quality-checked variants)
│   ├── Properties: chromosome, position, ref_allele, alt_allele
│   ├── References: source_variant_id, merged_variant_id (optional)
│   ├── Validation: is_valid, is_complete, filter_results (JSON)
│   ├── Metadata: filter_timestamp, filter_version
│   └── Indexes: file_id, coordinates, validity
│
├── Annotation (analysis tool results)
│   ├── References: variant_id (generic Variant table)
│   ├── Properties: tool_name, annotation_type, score_value, score_label
│   ├── Metadata: metadata_json (tool-specific data)
│   └── Indexes: tool_name, score_value, tool_type
│
└── WorkflowAudit (operation tracking)
    ├── Properties: file_id, operation, operation_stage, status
    ├── Metrics: input_count, output_count, duration
    ├── Details: parameters (JSON), results (JSON), error_message
    ├── Metadata: started_at, completed_at
    └── Indexes: file_id, operation, status, timestamp
```

### 2.2 Key Design Decisions

**1. Canonical Variant Identifier (gen_pos)**
- Format: `"chr1-12345-A-T"` (chromosome-position-ref-alt)
- Used for deduplication and cross-table joins
- Indexed in SourceVariant, MergedVariant, FilteredVariant
- Advantages:
  - Immune to transcript/gene changes
  - Fast coordinate-based queries
  - Consistent across sources

**2. JSON Storage for Flexibility**
- `SourceVariant.source_data`: Source-specific fields
- `MergedVariant.{clinvar,lovd,gnomad}_data`: Per-source merge data
- `FilteredVariant.filter_results`: Individual filter pass/fail results
- `Annotation.metadata_json`: Tool-specific scoring details
- `WorkflowAudit.{parameters,results}`: Operation-specific metadata

**3. Audit Trail for Reproducibility**
- Every major operation creates WorkflowAudit entry
- Tracks: parameters, results, timing, errors, user_id
- Enables rollback and re-running operations

**4. Source Linkage Strategy**
- FilteredVariant can reference both SourceVariant AND MergedVariant
- Preserves traceability of data origin
- Allows analysis of filtering accuracy per source

---

## 3. API-to-Database Operation Mapping

### 3.1 Delta-Sync Operations

```
GET /workspace_phase2/delta-sync/status/<file_id>?source=clinvar

Operation Flow:
1. Query SourceVariant table for existing clinvar variants
2. Get last import_timestamp and source_version
3. Check freshness against source freshness window (clinvar: 24h)
4. Detect version mismatch (e.g., 2024.01 → 2024.02)
5. Return: SyncStatus with requires_full_sync flag
6. DB Operations: READ SourceVariant (indexed by file_id + source_database)

Output Example:
{
  "has_existing_data": true,
  "record_count": 15234,
  "last_import_timestamp": "2024-11-17T08:30:00Z",
  "requires_full_sync": false,
  "version_mismatch": false
}
```

### 3.2 Merge Operations

```
POST /workspace_phase2/merge/perform
{
  "file_id": 1,
  "sources": ["clinvar", "lovd"],
  "strategy": "consensus"
}

Operation Flow:
1. Create WorkflowAudit(operation="merge", status="pending")
2. Query SourceVariant for file_id with sources=[clinvar, lovd]
3. Group by gen_pos (canonical coordinate)
4. Apply strategy:
   - outer_union: Include all variants
   - inner_intersection: Only in all sources
   - consensus: In 2+ sources
5. Combine source-specific data into merged record
6. Bulk insert to MergedVariant table
7. Update WorkflowAudit(status="completed", output_count=N)
8. Emit socket notifications to user session

DB Operations:
- READ: SourceVariant (indexed query by file_id, source_database)
- WRITE: MergedVariant (bulk_save_objects)
- WRITE: WorkflowAudit (create & update)

Expected Output Example:
{
  "status": "success",
  "result": {
    "merged_count": 15234,
    "duplicate_count": 234,
    "source_breakdown": {
      "clinvar": 12000,
      "lovd": 8000
    },
    "merge_strategy": "consensus"
  }
}
```

### 3.3 Quality Filtering Operations

```
POST /workspace_phase2/filter/apply
{
  "file_id": 1
}

Operation Flow:
1. Create WorkflowAudit(operation="filter", status="pending")
2. Query MergedVariant table for file_id
3. For each variant, apply 6 QC filters:
   ✓ RequiredFieldsFilter (CRITICAL): chromosome, position, ref, alt
   ✓ GenomicCoordinateFilter (CRITICAL): valid chr + position
   ✓ AlleleValidityFilter (CRITICAL): DNA bases only
   ✓ CanonicalFormatFilter (CRITICAL): gen_pos format correct
   ✓ AnnotationPresenceFilter (SOFT): has gene or transcript
   ✓ SourceAttributionFilter (SOFT): has source database data
4. Determine is_valid (all critical pass) & is_complete (all pass)
5. Store filter_results JSON with per-filter status
6. Bulk insert to FilteredVariant table
7. Update WorkflowAudit(status="completed", output_count=N)

DB Operations:
- READ: MergedVariant (all for file_id)
- WRITE: FilteredVariant (bulk_save_objects)
- WRITE: WorkflowAudit (create & update)

Filter Results JSON Example:
{
  "required_fields": true,
  "genomic_coordinate": true,
  "allele_validity": true,
  "canonical_format": true,
  "annotation_presence": true,
  "source_attribution": true
}

Expected Output:
{
  "total_variants": 15234,
  "valid_variants": 14821,
  "invalid_variants": 413,
  "complete_variants": 15000
}
```

### 3.4 Analysis Operations

```
GET /workspace_phase2/analysis/statistics/<file_id>

Operation Flow:
1. Query Annotation table for all variants linked to FilteredVariant
2. Group by tool_name (CADD, REVEL, SpliceAI)
3. For each tool:
   - Count total annotations
   - Count pathogenic (score >= threshold)
   - Calculate avg, min, max scores
4. Return aggregated statistics

DB Operations:
- READ: Annotation (indexed query by tool_name)
- Filtering: Only variants in FilteredVariant for file_id

Expected Output:
{
  "by_tool": {
    "cadd": {
      "count": 14821,
      "pathogenic": 234,
      "avg_score": 15.23,
      "min_score": 0.0,
      "max_score": 35.0
    },
    "revel": {
      "count": 14821,
      "pathogenic": 189,
      "avg_score": 0.32,
      "min_score": 0.0,
      "max_score": 1.0
    },
    "spliceai": {
      "count": 14821,
      "pathogenic": 89,
      "avg_score": 0.08,
      "min_score": 0.0,
      "max_score": 1.0
    }
  },
  "total_analyses": 44463
}
```

### 3.5 Data Query Operations

```
GET /workspace_phase2/variants/filtered/<file_id>?valid_only=true&limit=100&offset=0

Operation Flow:
1. Query FilteredVariant table with filters:
   - file_id = <file_id>
   - is_valid = true (if valid_only specified)
2. Apply pagination (limit=100, offset=0)
3. Convert to dict representation
4. Return with count

DB Operations:
- READ: FilteredVariant (indexed query file_id + validity)

Response Format:
{
  "status": "success",
  "count": 100,
  "data": [
    {
      "id": 123456,
      "chromosome": "chr1",
      "position": 12345,
      "ref_allele": "A",
      "alt_allele": "T",
      "gene": "BRCA1",
      "is_valid": true,
      "is_complete": true,
      "created_at": "2025-11-17T08:30:00Z"
    },
    ...
  ]
}
```

---

## 4. Implementation Roadmap

### Phase 4.1: Validation & Fixes (COMPLETED ✅)

**Status**: Completed
**Commit**: `8d1e634`

Fixes applied:
1. ✅ Flask Blueprint routing (absolute → relative paths)
2. ✅ JSON error handling (catch 415 → return 400)
3. ✅ Annotation field names (tool → tool_name, score → score_value)
4. ✅ Test database initialization (create tables in fixture)

**Tests**: 41/41 Phase 2 API endpoints passing

---

### Phase 4.2: Repository Enhancement (NEXT)

**Objectives**:
- Add missing repository methods
- Implement cleanup/deletion operations
- Add transaction safety wrappers

**Missing Methods**:
1. `SourceVariantRepository.delete_by_file(file_id)`
2. `SourceVariantRepository.find_by_gene(file_id, gene)`
3. `MergedVariantRepository.delete_by_file(file_id)`
4. `MergedVariantRepository.count_by_file(file_id)`
5. `FilteredVariantRepository.delete_by_file(file_id)`
6. `FilteredVariantRepository.find_by_source_variant(source_variant_id)`
7. `WorkflowAuditRepository.delete_by_file(file_id)`
8. `WorkflowAuditRepository.get_all_by_status(status)`

**Time Estimate**: 2-3 hours

---

### Phase 4.3: Analysis-FilteredVariant Linkage

**Objective**: Complete the analysis workflow by linking annotations to filtered variants

**Current State**:
- Annotation model links to generic Variant table
- AnalysisIntegrationHandler works with annotations
- But Phase 2 pipeline uses FilteredVariant as final output
- Missing: Direct linkage between FilteredVariant and Annotation

**Solution Options**:

**Option A: Add FilteredVariant reference to Annotation** (Recommended)
```python
class Annotation(Base):
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    filtered_variant_id = Column(Integer, ForeignKey("filtered_variants.id"), nullable=True)
    # Rest of fields...
```
- Pros: Maintains backward compatibility, adds Phase 2 support
- Cons: Slight denormalization

**Option B: Create Phase2Annotation subclass**
```python
class Phase2Annotation(Annotation):
    filtered_variant_id = Column(Integer, ForeignKey("filtered_variants.id"))
```
- Pros: Clean separation of concerns
- Cons: Requires table inheritance

**Recommendation**: Option A - Add filtered_variant_id column to Annotation
- Minimal schema change
- Maintains backward compatibility
- Clear Phase 2 flow

**Tasks**:
1. Add migration to add filtered_variant_id column
2. Update AnalysisIntegrationHandler to populate filtered_variant_id
3. Update get_analysis_statistics() to filter by file_id properly
4. Update create_filtered_variant_from_analysis() with real implementation
5. Add tests for analysis-filtered variant linkage

**Time Estimate**: 4-5 hours

---

### Phase 4.4: Comprehensive Integration Testing

**Objective**: Create complete end-to-end test suite

**Test Scenarios**:

1. **Delta-Sync Tests**
   - Fresh data import (no existing data)
   - Update existing data (same version)
   - Version mismatch (new version available)
   - Freshness window expiration

2. **Merge Tests**
   - Two-source merge (clinvar + lovd)
   - Three-source merge (clinvar + lovd + gnomad)
   - Outer union strategy (expected: all variants)
   - Inner intersection (expected: only in all sources)
   - Consensus strategy (expected: in 2+ sources)
   - Duplicate handling

3. **Filter Tests**
   - All valid variants
   - Mixed valid/invalid
   - Variants with missing fields
   - Invalid coordinates
   - Complete filter audit trail

4. **Analysis Tests**
   - Single tool (CADD) analysis
   - Multi-tool (all three) analysis
   - Pathogenic classification
   - Score range filtering
   - Statistics aggregation

5. **Workflow Tests**
   - Complete pipeline: import → merge → filter → analyze
   - Error handling (failed import recovery)
   - Audit trail completeness
   - User session notifications
   - File cleanup

6. **Data Integrity Tests**
   - Transaction rollback on error
   - Duplicate prevention
   - Referential integrity
   - JSON field validation

**Files to Create**:
- `tests/integration/test_phase2_merge_operations.py`
- `tests/integration/test_phase2_filtering_operations.py`
- `tests/integration/test_phase2_analysis_operations.py`
- `tests/integration/test_phase2_end_to_end.py`

**Time Estimate**: 6-8 hours

---

### Phase 4.5: Performance Optimization

**Objective**: Optimize database queries for large datasets

**Optimizations**:
1. Index strategy validation
2. Query plan analysis
3. Bulk operation batching
4. Connection pooling
5. Query result caching (for stable data)

**Benchmarks to Target**:
- 100K variants merge: < 30 seconds
- 100K variants filter: < 20 seconds
- 100K variants analysis stats: < 5 seconds
- Query response time: < 1 second for paginated results

**Time Estimate**: 4-6 hours

---

### Phase 4.6: Documentation & Examples

**Objective**: Complete API documentation and usage examples

**Documentation**:
1. API endpoint specification (detailed)
2. Database schema documentation
3. Error codes and handling
4. Authentication/authorization
5. Rate limiting (if applicable)
6. Example requests/responses

**Code Examples**:
1. Basic workflow example
2. Error handling patterns
3. Bulk operation example
4. Custom merge strategy
5. Custom filter implementation

**Time Estimate**: 3-4 hours

---

## 5. Critical Integration Points

### 5.1 Data Consistency

**Transaction Requirements**:
```python
# Merge operation must be atomic
with session.begin_nested():
    merged = handler.perform_merge(...)  # Creates MergedVariant + WorkflowAudit
    if not merged:
        raise MergeFailedError()

# Cascading failures must rollback
try:
    merge_result = merge_handler.perform_merge(...)
    filter_result = filter_handler.apply_filters(...)
    analysis_result = analysis_handler.bulk_store_results(...)
except Exception:
    session.rollback()  # All changes reverted
```

### 5.2 Error Handling

**WorkflowAudit Logging**:
```python
audit = WorkflowAuditRepository.create(
    file_id=file_id,
    operation="merge",
    status="pending"
)

try:
    result = perform_merge(...)
    audit.status = "completed"
    audit.output_count = result.count
except Exception as e:
    audit.status = "failed"
    audit.error_message = str(e)
finally:
    session.commit()  # Always persist audit
```

### 5.3 Validation Rules

**Pre-Operation Validation**:
```python
# Before merge: Validate sources exist
sources_valid, error = validate_merge_inputs(file_id, sources)
if not sources_valid:
    return jsonify({"error": error}), 400

# Before filtering: Validate merged variants exist
merge_count = MergedVariantRepository.count_by_file(file_id)
if merge_count == 0:
    return jsonify({"error": "No merged variants to filter"}), 400
```

---

## 6. Quality Metrics

### 6.1 Test Coverage

**Target Coverage**:
- Unit tests: 85%+ for business logic
- Integration tests: 95%+ for Phase 2 operations
- End-to-end tests: 100% of critical workflows

**Current Coverage**:
- API endpoints: 100% (41/41 tests passing)
- Data layer: 60% (partial implementations)
- Repositories: 70% (core methods covered)

### 6.2 Performance Metrics

**Target SLAs**:
| Operation | Dataset Size | Target Time | Current |
|-----------|-------------|-------------|---------|
| Merge | 100K variants | < 30s | TBD |
| Filter | 100K variants | < 20s | TBD |
| Analysis Stats | 100K variants | < 5s | TBD |
| Query (paginated) | Any | < 1s | ✓ |

### 6.3 Reliability Metrics

**Target Goals**:
- Error recovery rate: > 95%
- Audit trail completeness: 100%
- Data consistency: 100%
- Transaction integrity: 100%

---

## 7. Risk Mitigation

### 7.1 Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Analysis-FilteredVariant linkage incomplete | High | Medium | Implement in Phase 4.3 |
| Large dataset performance degradation | Medium | High | Implement indexes, benchmark in Phase 4.5 |
| Transaction isolation issues | Low | High | Add locking, serializable isolation |
| Missing cleanup operations | Low | Medium | Implement Phase 4.2 |

### 7.2 Testing Strategy

1. **Unit Tests**: Business logic isolation
2. **Integration Tests**: Database operations
3. **End-to-End Tests**: Complete workflows
4. **Load Tests**: Performance with 100K+ variants
5. **Chaos Tests**: Error recovery scenarios

---

## 8. Timeline & Resource Allocation

```
Week 1 (Nov 18-24):
├─ Phase 4.1: Validation & Fixes ✅ (COMPLETED)
└─ Phase 4.2: Repository Enhancement (Start)

Week 2 (Nov 25-Dec 1):
├─ Phase 4.2: Repository Enhancement (Complete)
└─ Phase 4.3: Analysis-FilteredVariant Linkage (Start)

Week 3 (Dec 2-8):
├─ Phase 4.3: Analysis-FilteredVariant Linkage (Complete)
└─ Phase 4.4: Comprehensive Integration Testing (Start)

Week 4 (Dec 9-15):
├─ Phase 4.4: Integration Testing (Complete)
└─ Phase 4.5: Performance Optimization (Start)

Week 5 (Dec 16-22):
├─ Phase 4.5: Performance Optimization (Complete)
└─ Phase 4.6: Documentation (Start)

Week 6 (Dec 23-29):
└─ Phase 4.6: Documentation (Complete)
```

**Estimated Total**: 25-30 hours

---

## 9. Success Criteria

### Phase Completion Checklist

- [ ] All repository methods implemented
- [ ] Analysis-FilteredVariant linkage complete
- [ ] 95%+ test coverage for Phase 2 operations
- [ ] All 41 API endpoints with integration tests
- [ ] Performance benchmarks met (> 100K variant operations)
- [ ] Complete error handling and recovery
- [ ] Comprehensive audit trail for all operations
- [ ] Full API documentation
- [ ] Real-world data validation

### Definition of Done

A Phase 2 operation is "done" when:
1. ✅ API endpoint responds correctly
2. ✅ Database operations are atomic
3. ✅ WorkflowAudit entry created
4. ✅ Error handling with user-friendly messages
5. ✅ Integration tests (>80% coverage)
6. ✅ Documentation with examples
7. ✅ Performance acceptable (< target time)
8. ✅ Data integrity verified

---

## 10. Appendix: Key Thresholds & Constants

### Tool Configuration
```python
ANALYSIS_TOOLS = {
    "cadd": {
        "min": 0, "max": 100,
        "pathogenic_threshold": 20,
        "description": "CADD score (higher = more deleterious)"
    },
    "revel": {
        "min": 0, "max": 1,
        "pathogenic_threshold": 0.5,
        "description": "REVEL score (higher = more deleterious)"
    },
    "spliceai": {
        "min": 0, "max": 1,
        "pathogenic_threshold": 0.2,
        "description": "SpliceAI max score (higher = more impact)"
    }
}
```

### Quality Filters
```python
QUALITY_FILTERS = [
    # CRITICAL (all must pass for is_valid=True)
    "RequiredFieldsFilter",
    "GenomicCoordinateFilter",
    "AlleleValidityFilter",
    "CanonicalFormatFilter",
    # SOFT (informational, not blocking)
    "AnnotationPresenceFilter",
    "SourceAttributionFilter"
]
```

### Delta-Sync Configuration
```python
SOURCE_VERSIONS = {
    "clinvar": "2024.01",
    "lovd": "2024.01",
    "gnomad": "4.0",
    "custom": "1.0"
}

FRESHNESS_WINDOWS_HOURS = {
    "clinvar": 24,      # Daily updates
    "lovd": 168,        # Weekly
    "gnomad": 720,      # Monthly
    "custom": 8760      # Yearly
}
```

---

## References

- [Phase 2 Routes](./workspace_phase2_route.py)
- [Data Models](../models/)
- [Database Config](../database/)
- [API Test Suite](../../tests/integration/test_phase2_api_endpoints.py)

---

**Document History**:
- v1.0 (2025-11-18): Initial comprehensive plan based on code analysis

