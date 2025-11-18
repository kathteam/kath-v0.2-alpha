# KATH Database Integration Plan

## Overview

This document outlines the strategic transition of the KATH system from a
CSV-file-based workflow to a comprehensive SQLite-backed architecture. The
plan is divided into two phases, with Phase 1 focusing on UI visualization
and pagination, and Phase 2 implementing deep integration to store the
entire analysis pipeline directly in the database.

**Current State:**
- Database: SQLite with 5-table schema (workspaces, files, variants,
  annotations, aggregations)
- Workflow: CSV files imported → analyzed → results displayed
- Storage: Test data in database (1.2M records), real genetic data to be
  imported
- Limitations: No pagination, full dataset loaded into memory, CSV files as
  single source of truth

**Target State (Phase 2):**
- Database as primary data store for all pipeline stages
- Intelligent delta-sync downloads (only new data if DB not empty)
- Complete analysis results stored in database
- Filtered/cleaned data stored separately with audit trail
- User-friendly UI with pagination and statistics

---

## Executive Summary

### Vision
Transform KATH from a CSV-dependent system to a modern, scalable database-first
architecture where SQLite serves as the single source of truth for all variant
data, analysis results, and workflow artifacts.

### Key Benefits
- **Scalability:** Handle millions of variants without memory constraints
- **Performance:** Indexed queries for fast filtering and sorting
- **Reproducibility:** Audit trail of all transformations via database records
- **Flexibility:** Modify analysis parameters and re-compute without re-importing
- **Intelligence:** Prevent duplicate downloads by detecting existing data
- **User Experience:** Pagination, sorting, real-time statistics
- **Data Integrity:** Transactional consistency across pipeline stages

### Timeline
- **Phase 1 (UI Visualization):** 2-3 weeks
- **Phase 2 (Complete Integration):** 6-8 weeks
- **Total:** 8-11 weeks for full implementation

---

## Phase 1: UI Visualization Layer (Initial Integration)

### 1.1 Objective

Enable the KATH UI to display variant data directly from the SQLite database
with pagination controls, allowing users to:
- View total number of variant entries
- Configure entries per page (10, 25, 50, 100)
- Navigate between pages (previous, next, go-to-page)
- See real-time statistics (total count, current page range)

### 1.2 User Experience Goals

**Current Experience (CSV-based):**
```
1. User imports CSV file (100,000+ rows)
2. System loads entire file into memory
3. UI freezes during processing
4. All rows displayed (or pagination via client-side array)
5. Filtering/sorting done in-memory
```

**Target Phase 1 Experience:**
```
1. User selects workspace with imported data
2. UI loads first page (e.g., 25 rows)
3. Statistics display: "Showing 1-25 of 1,206,222 entries"
4. User can:
   - Navigate with Previous/Next buttons
   - Jump to specific page
   - Change entries-per-page dynamically
   - Sort by any column (delegated to database)
5. Performance: <100ms per page load (database-driven)
```

### 1.3 Technical Scope

#### What's Included
- API endpoints modified to support pagination (LIMIT/OFFSET)
- Database queries optimized with proper indexing
- Frontend pagination UI components
- Entry count aggregation cached in annotations table
- Real-time statistics display
- CSV files retained as secondary reference

#### What's NOT Included
- CSV replacement (files still primary import source)
- Analysis pipeline storage (Phase 2 only)
- Download optimization (Phase 2 only)
- Source-level data transformations (Phase 2 only)

### 1.4 Detailed Implementation Tasks

#### Task 1.4.1: Backend API Pagination Endpoint

**File:** `app/back_end/src/routes/variants_route.py`

**Current Endpoint (Approximate):**
```python
@app.route('/api/v1/files/<file_id>/variants', methods=['GET'])
def get_variants(file_id):
    # Returns all variants for a file
    variants = session.query(Variant).filter_by(file_id=file_id).all()
    return jsonify([v.to_dict() for v in variants])
```

**New Paginated Endpoint:**
```python
@app.route('/api/v1/files/<file_id>/variants', methods=['GET'])
def get_variants(file_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 25, type=int)
    sort_by = request.args.get('sort_by', 'id', type=str)
    sort_order = request.args.get('sort_order', 'asc', type=str)

    # Validate inputs
    if page < 1:
        page = 1
    if page_size not in [10, 25, 50, 100]:
        page_size = 25

    # Get total count (cached if possible)
    total_count = variant_repository.count_by_file(file_id)

    # Get paginated results
    offset = (page - 1) * page_size
    variants = variant_repository.find_paginated(
        file_id=file_id,
        offset=offset,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size

    return jsonify({
        'data': [v.to_dict() for v in variants],
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total_entries': total_count,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'showing_from': offset + 1 if total_count > 0 else 0,
            'showing_to': min(offset + page_size, total_count)
        }
    })
```

**Duration:** 3-4 hours

---

#### Task 1.4.2: Repository Layer Pagination Support

**File:** `app/back_end/src/database/repositories.py`

**Add to VariantRepository:**
```python
def find_paginated(self, file_id, offset=0, limit=25,
                   sort_by='id', sort_order='asc'):
    """Retrieve paginated variants with sorting support."""
    query = self.session.query(Variant).filter_by(file_id=file_id)

    # Apply sorting
    sort_column = getattr(Variant, sort_by, Variant.id)
    if sort_order.lower() == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    return query.all()

def count_by_file(self, file_id):
    """Count total variants in a file (with caching)."""
    cache_key = f"variant_count_{file_id}"

    # Check cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    count = self.session.query(Variant).filter_by(file_id=file_id).count()

    # Cache for 1 hour
    cache.set(cache_key, count, timeout=3600)
    return count

def invalidate_count_cache(self, file_id):
    """Clear count cache when data changes."""
    cache_key = f"variant_count_{file_id}"
    cache.delete(cache_key)
```

**Duration:** 2-3 hours

---

#### Task 1.4.3: Frontend Pagination Component

**File:** `app/front_end/src/components/VariantPagination.vue` (NEW)

**Component Features:**
```vue
<template>
  <div class="pagination-container">
    <!-- Statistics Row -->
    <div class="stats-row">
      <span class="entry-count">
        Showing {{ pagination.showing_from }} to
        {{ pagination.showing_to }} of
        {{ pagination.total_entries }} entries
      </span>

      <!-- Page Size Selector -->
      <select v-model="pageSize" @change="onPageSizeChange">
        <option value="10">10 per page</option>
        <option value="25">25 per page</option>
        <option value="50">50 per page</option>
        <option value="100">100 per page</option>
      </select>
    </div>

    <!-- Navigation Row -->
    <div class="navigation-row">
      <button
        @click="previousPage"
        :disabled="!pagination.has_previous"
        class="btn btn-sm"
      >
        ← Previous
      </button>

      <div class="page-indicator">
        Page {{ pagination.current_page }} of
        {{ pagination.total_pages }}
      </div>

      <div class="goto-page">
        <input
          type="number"
          v-model.number="goToPageInput"
          min="1"
          :max="pagination.total_pages"
          @keyup.enter="goToPage"
          placeholder="Go to page"
          class="page-input"
        />
        <button @click="goToPage" class="btn btn-sm">Go</button>
      </div>

      <button
        @click="nextPage"
        :disabled="!pagination.has_next"
        class="btn btn-sm"
      >
        Next →
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VariantPagination',
  props: {
    fileId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      variants: [],
      pagination: {
        current_page: 1,
        page_size: 25,
        total_entries: 0,
        total_pages: 0,
        has_previous: false,
        has_next: false,
        showing_from: 0,
        showing_to: 0
      },
      pageSize: 25,
      goToPageInput: null,
      loading: false,
      error: null
    }
  },
  mounted() {
    this.loadPage(1);
  },
  methods: {
    async loadPage(pageNumber) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch(
          `/api/v1/files/${this.fileId}/variants?` +
          `page=${pageNumber}&page_size=${this.pageSize}`
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        this.variants = result.data;
        this.pagination = result.pagination;
      } catch (err) {
        this.error = `Failed to load variants: ${err.message}`;
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    previousPage() {
      if (this.pagination.has_previous) {
        this.loadPage(this.pagination.current_page - 1);
      }
    },

    nextPage() {
      if (this.pagination.has_next) {
        this.loadPage(this.pagination.current_page + 1);
      }
    },

    goToPage() {
      const pageNum = parseInt(this.goToPageInput);
      if (pageNum >= 1 && pageNum <= this.pagination.total_pages) {
        this.loadPage(pageNum);
        this.goToPageInput = null;
      }
    },

    onPageSizeChange() {
      this.pageSize = parseInt(this.pageSize);
      this.loadPage(1);  // Reset to first page
    }
  }
}
</script>

<style scoped>
.pagination-container {
  padding: 20px;
  border-top: 1px solid #ddd;
  background-color: #f9f9f9;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.entry-count {
  font-weight: 500;
  color: #333;
}

select {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.navigation-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.page-indicator {
  flex: 1;
  text-align: center;
  font-weight: 500;
}

.goto-page {
  display: flex;
  gap: 5px;
}

.page-input {
  width: 60px;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn {
  padding: 8px 12px;
  border: 1px solid #007bff;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  border-color: #999;
}
</style>
```

**Duration:** 4-5 hours

---

#### Task 1.4.4: Database Query Optimization

**File:** `app/back_end/src/database/config.py`

**Add Indexes:**
```python
# In Variant model (if not already indexed)
__table_args__ = (
    Index('ix_variant_file_id', 'file_id'),
    Index('ix_variant_chromosome', 'chromosome'),
    Index('ix_variant_position', 'position'),
    Index('ix_variant_gen_pos', 'gen_pos'),
    Index('ix_variant_gene', 'gene'),
    Index('ix_variant_file_id_chromosome_position',
          'file_id', 'chromosome', 'position'),
)
```

**Verify Indexes Created:**
```sql
-- Run after migration
PRAGMA index_list(variants);
-- Should show all indices including file_id, chromosome, position
```

**Duration:** 1-2 hours

---

#### Task 1.4.5: Frontend Integration

**File:** `app/front_end/src/views/WorkspaceVariants.vue` (MODIFY)

**Current Structure (Approximate):**
```vue
<template>
  <div class="variants-view">
    <h1>{{ workspace }} - Variants</h1>
    <table>
      <tr v-for="variant in allVariants" :key="variant.id">
        <td>{{ variant.chromosome }}</td>
        <td>{{ variant.position }}</td>
        ...
      </tr>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      allVariants: []  // Loaded all at once from CSV
    }
  },
  methods: {
    async loadVariants() {
      const response = await fetch(`/api/v1/files/${fileId}/variants`);
      this.allVariants = await response.json();
    }
  }
}
</script>
```

**Modified Structure:**
```vue
<template>
  <div class="variants-view">
    <h1>{{ workspace }} - Variants</h1>

    <!-- Add pagination component -->
    <VariantPagination :fileId="fileId" />

    <!-- Variant table still present but receives paginated data -->
    <table v-if="!loading">
      <thead>
        <tr>
          <th>Chromosome</th>
          <th>Position</th>
          <th>Ref</th>
          <th>Alt</th>
          <th>Gene</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="variant in variants" :key="variant.id">
          <td>{{ variant.chromosome }}</td>
          <td>{{ variant.position }}</td>
          <td>{{ variant.ref_allele }}</td>
          <td>{{ variant.alt_allele }}</td>
          <td>{{ variant.gene }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
import VariantPagination from '@/components/VariantPagination.vue';

export default {
  components: { VariantPagination },
  data() {
    return {
      fileId: null,
      workspace: null,
      variants: [],  // Current page only
      loading: false,
      error: null
    }
  },
  mounted() {
    this.loadInitialData();
  },
  methods: {
    async loadInitialData() {
      // Get file_id from route params
      this.fileId = this.$route.params.fileId;
      this.workspace = this.$route.params.workspace;
    }
  }
}
</script>
```

**Duration:** 3-4 hours

---

#### Task 1.4.6: Caching Strategy

**File:** `app/back_end/src/cache.py` (NEW)

**Implementation:**
```python
from flask_caching import Cache
from flask import Flask

cache = Cache(config={
    'CACHE_TYPE': 'simple',  # or redis for production
    'CACHE_DEFAULT_TIMEOUT': 300
})

def init_cache(app: Flask):
    """Initialize caching system."""
    cache.init_app(app)
    return cache

def cache_variant_count(file_id: int, timeout: int = 3600):
    """Decorator for caching variant counts."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            cache_key = f"variant_count_{file_id}"
            result = cache.get(cache_key)
            if result is not None:
                return result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator
```

**Duration:** 2 hours

---

### 1.5 Phase 1 Success Criteria

- [V] API endpoint returns paginated results with metadata
- [V] Pagination component displays on frontend
- [V] Page navigation works (previous, next, go-to)
- [V] Page size selector works (10, 25, 50, 100)
- [V] Statistics display correct (total count, showing X-Y of Z)
- [V] Database queries execute in <100ms for typical page sizes
- [V] Count cache working (verified via query timing)
- [V] No memory spikes when loading large datasets
- [V] CSV files still accessible as backup
- [V] All existing functionality maintained

### 1.6 Phase 1 Testing Plan

**Unit Tests:**
```python
def test_variant_pagination():
    """Test paginated variant retrieval."""
    variants = variant_repo.find_paginated(
        file_id=1, offset=0, limit=25
    )
    assert len(variants) == 25

    # Test offset
    variants_page2 = variant_repo.find_paginated(
        file_id=1, offset=25, limit=25
    )
    assert variants[0].id != variants_page2[0].id

def test_variant_count_caching():
    """Test count caching."""
    count1 = variant_repo.count_by_file(file_id=1)
    count2 = variant_repo.count_by_file(file_id=1)
    assert count1 == count2  # Should be cached
```

**Integration Tests:**
```python
def test_pagination_api_endpoint():
    """Test full pagination API."""
    response = client.get('/api/v1/files/1/variants?page=1&page_size=25')
    assert response.status_code == 200

    data = response.get_json()
    assert 'data' in data
    assert 'pagination' in data
    assert data['pagination']['current_page'] == 1
    assert len(data['data']) == 25
```

**Duration:** 8-10 hours

---

### 1.7 Phase 1 Resource Estimate

| Task | Hours | Days |
|------|-------|------|
| 1.4.1 API Endpoint | 4 | 0.5 |
| 1.4.2 Repository | 3 | 0.4 |
| 1.4.3 Component | 5 | 0.6 |
| 1.4.4 Optimization | 2 | 0.25 |
| 1.4.5 Integration | 4 | 0.5 |
| 1.4.6 Caching | 2 | 0.25 |
| Testing | 10 | 1.25 |
| **Total Phase 1** | **30** | **3.75 days** |

**Timeline:** 2-3 weeks with 50% development time allocation

---

## Phase 2: Complete SQLite Integration & Pipeline Storage

### 2.1 Objective

Implement comprehensive database-first architecture where SQLite stores:
- Pre-merge data (source-specific variants as imported)
- Merged results (combined data from multiple sources)
- Filtered data (cleaned/validated entries after quality control)
- Analysis results (CADD, REVEL, SpliceAI scores)
- Workflow metadata (audit trail of transformations)

Replace CSV files as primary data source with intelligent download optimization.

### 2.2 User Experience Goals

**Phase 2 Complete Flow:**

```
1. User initiates import from ClinVar/LOVD/gnomAD
   ↓
2. System queries database for existing data
   - If empty: Download all data
   - If exists: Download only new/updated records
   ↓
3. Data imported and stored in "source_variants" table
   - Linked to original source (clinvar, lovd, gnomad)
   - Timestamp for delta-sync optimization
   ↓
4. User initiates merge (e.g., ClinVar + LOVD)
   - Merged results stored in "merged_variants" table
   - Composition tracked (which sources, which rows)
   - Searchable and filterable
   ↓
5. User runs quality filtering
   - Removes corrupt/incomplete entries
   - Results stored in "filtered_variants" table
   - Original data preserved (audit trail)
   ↓
6. User runs analysis tools (CADD, REVEL, SpliceAI)
   - Reads from filtered_variants
   - Results stored in annotations table
   - Can recompute without re-filtering
   ↓
7. User visualizes results
   - All data from database with pagination
   - Can explore any stage of pipeline
   - Export from database (not CSV)
```

### 2.3 Data Model Extensions

#### 2.3.1 New Tables

**`source_variants` Table:**
Purpose: Store imported data before any merging/filtering operations

```python
class SourceVariant(Base):
    """Variants as imported from data source (ClinVar/LOVD/gnomAD)."""
    __tablename__ = 'source_variants'

    id = Column(Integer, primary_key=True)
    source_database = Column(String(50), nullable=False)  # clinvar, lovd, gnomad
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)

    # Genomic coordinates (as imported)
    chromosome = Column(String(10), nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    ref_allele = Column(String(255), nullable=False)
    alt_allele = Column(String(255), nullable=False)
    gen_pos = Column(String(255), nullable=False, index=True)

    # Source-specific fields
    variant_id = Column(String(255), index=True)  # rs numbers, etc.
    gene = Column(String(255), index=True)
    transcript = Column(String(255))
    consequence = Column(String(255))

    # Source data (as JSON)
    source_data = Column(Text)  # Original columns from source

    # Import metadata
    import_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_version = Column(String(50))  # Version of source DB at import

    # Relationships
    file = relationship('File', backref='source_variants')

    # Indexes
    __table_args__ = (
        Index('ix_sv_file_source', 'file_id', 'source_database'),
        Index('ix_sv_chr_pos', 'chromosome', 'position'),
        Index('ix_sv_gen_pos', 'gen_pos'),
    )
```

**`merged_variants` Table:**
Purpose: Store results after merging multiple sources

```python
class MergedVariant(Base):
    """Variants after merging multiple sources."""
    __tablename__ = 'merged_variants'

    id = Column(Integer, primary_key=True)
    merged_file_id = Column(Integer, ForeignKey('files.id'), nullable=False)

    # Canonical coordinates (merged position)
    chromosome = Column(String(10), nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    ref_allele = Column(String(255), nullable=False)
    alt_allele = Column(String(255), nullable=False)
    gen_pos = Column(String(255), nullable=False, index=True)

    # Merged fields
    gene = Column(String(255), index=True)
    transcript = Column(String(255))
    consequence = Column(String(255))

    # Source information
    source_databases = Column(Text)  # JSON: ["clinvar", "lovd"]
    clinvar_data = Column(Text)  # Data from ClinVar
    lovd_data = Column(Text)  # Data from LOVD
    gnomad_data = Column(Text)  # Data from gnomAD

    # Merge metadata
    merge_timestamp = Column(DateTime, default=datetime.utcnow)
    merge_strategy = Column(String(50))  # outer_join, inner_join, etc.

    # Relationships
    merged_file = relationship('File', backref='merged_variants')

    __table_args__ = (
        Index('ix_mv_file_id', 'merged_file_id'),
        Index('ix_mv_chr_pos', 'chromosome', 'position'),
    )
```

**`filtered_variants` Table:**
Purpose: Store cleaned/validated variants after quality control

```python
class FilteredVariant(Base):
    """Variants after filtering and validation."""
    __tablename__ = 'filtered_variants'

    id = Column(Integer, primary_key=True)
    filtered_file_id = Column(Integer, ForeignKey('files.id'),
                             nullable=False)
    source_variant_id = Column(Integer, ForeignKey('source_variants.id'))
    merged_variant_id = Column(Integer, ForeignKey('merged_variants.id'))

    # Genomic data
    chromosome = Column(String(10), nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    ref_allele = Column(String(255), nullable=False)
    alt_allele = Column(String(255), nullable=False)
    gen_pos = Column(String(255), nullable=False, index=True)

    # Quality flags
    is_complete = Column(Boolean, default=True)  # Has all required fields
    is_valid = Column(Boolean, default=True)  # Passes validation rules
    filter_results = Column(Text)  # JSON: {rule_name: passed}

    # Filtering metadata
    filter_timestamp = Column(DateTime, default=datetime.utcnow)
    filter_version = Column(String(50))  # Version of filter rules

    # Relationships
    filtered_file = relationship('File', backref='filtered_variants')
    source_variant = relationship('SourceVariant')
    merged_variant = relationship('MergedVariant')

    __table_args__ = (
        Index('ix_fv_file_id', 'filtered_file_id'),
        Index('ix_fv_chr_pos', 'chromosome', 'position'),
    )
```

**`workflow_audit` Table:**
Purpose: Track all transformations for reproducibility

```python
class WorkflowAudit(Base):
    """Audit trail of pipeline operations."""
    __tablename__ = 'workflow_audit'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)

    operation = Column(String(50), nullable=False)  # import, merge, filter, analyze
    operation_stage = Column(String(50))  # source_import, merge, filtering, etc.

    input_count = Column(Integer)  # Rows before operation
    output_count = Column(Integer)  # Rows after operation

    parameters = Column(Text)  # JSON of operation parameters
    results = Column(Text)  # JSON of operation results

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    status = Column(String(20), default='pending')  # pending, completed, failed
    error_message = Column(Text)

    user_id = Column(String(255))  # Who triggered the operation

    file = relationship('File', backref='workflow_audits')

    __table_args__ = (
        Index('ix_wa_file_id', 'file_id'),
        Index('ix_wa_operation', 'operation'),
    )
```

**Duration:** 4-5 hours design and creation

---

#### 2.3.2 Enhanced File Model

**Modifications to `app/back_end/src/models/file.py`:**

```python
class File(Base):
    """Enhanced File model with pipeline tracking."""

    # ... existing fields ...

    # Pipeline stage tracking
    import_status = Column(String(20), default='pending')  # pending, completed, failed
    import_source = Column(String(50))  # clinvar, lovd, gnomad, csv
    import_timestamp = Column(DateTime)

    merge_status = Column(String(20))  # pending, not_applicable, completed, failed
    merge_timestamp = Column(DateTime)
    merge_sources = Column(Text)  # JSON: ["clinvar", "lovd"]

    filter_status = Column(String(20))  # pending, not_applicable, completed, failed
    filter_timestamp = Column(DateTime)
    filter_rules_version = Column(String(50))

    analysis_status = Column(String(20))  # pending, completed, failed
    analysis_timestamp = Column(DateTime)
    analysis_tools = Column(Text)  # JSON: ["cadd", "revel", "spliceai"]

    # Counts at each stage
    source_variant_count = Column(Integer, default=0)
    merged_variant_count = Column(Integer, default=0)
    filtered_variant_count = Column(Integer, default=0)
    analyzed_variant_count = Column(Integer, default=0)

    # Last download info (for delta-sync)
    last_download_timestamp = Column(DateTime)
    last_download_count = Column(Integer)

    # Relationships
    source_variants = relationship('SourceVariant', backref='file')
    merged_variants = relationship('MergedVariant', backref='file')
    filtered_variants = relationship('FilteredVariant', backref='file')
    workflow_audits = relationship('WorkflowAudit', backref='file')
```

**Duration:** 2-3 hours

---

### 2.4 Download Optimization Implementation

#### 2.4.1 Delta-Sync Algorithm

**File:** `app/back_end/src/data/delta_sync.py` (NEW)

```python
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from models import File, SourceVariant

class DeltaSyncManager:
    """Intelligent download optimization for external databases."""

    def __init__(self, session: Session):
        self.session = session

    def should_download(self, file_id: int, source: str) -> bool:
        """Determine if we need to download data for source."""
        file = self.session.query(File).filter_by(id=file_id).first()
        if not file:
            return True  # New file, always download

        # Get last successful import
        last_import = self.session.query(SourceVariant)\
            .filter_by(file_id=file_id, source_database=source)\
            .order_by(SourceVariant.import_timestamp.desc())\
            .first()

        if not last_import:
            return True  # Never imported this source

        # Check if source DB has been updated since last import
        # This requires checking external DB version/timestamp
        if self._is_source_updated(source, last_import.source_version):
            return True

        return False

    def get_delta_query(self, file_id: int, source: str,
                        source_version: str) -> str:
        """Generate database-specific query for delta download."""
        file = self.session.query(File).filter_by(id=file_id).first()

        if not file:
            # Full download
            return self._get_full_query(source)

        # Get last import timestamp
        last_import = self.session.query(SourceVariant)\
            .filter_by(file_id=file_id, source_database=source)\
            .order_by(SourceVariant.import_timestamp.desc())\
            .first()

        if not last_import:
            return self._get_full_query(source)

        # Delta query (only new/updated records)
        return self._get_delta_query(source,
                                    last_import.import_timestamp,
                                    source_version)

    def _is_source_updated(self, source: str,
                          last_known_version: str) -> bool:
        """Check if source DB has newer version."""
        if source == 'clinvar':
            return self._check_clinvar_version(last_known_version)
        elif source == 'lovd':
            return self._check_lovd_version(last_known_version)
        elif source == 'gnomad':
            return self._check_gnomad_version(last_known_version)
        return True  # Conservative: assume updated if unknown

    def _get_full_query(self, source: str) -> str:
        """Get full download query for source."""
        if source == 'clinvar':
            return "SELECT * FROM clinvar_variants"
        elif source == 'lovd':
            return "SELECT * FROM lovd_variants"
        elif source == 'gnomad':
            return "SELECT * FROM gnomad_variants"

    def _get_delta_query(self, source: str, since: datetime,
                        version: str) -> str:
        """Get delta query (only new records)."""
        timestamp_str = since.isoformat()

        if source == 'clinvar':
            return f"SELECT * FROM clinvar_variants WHERE last_updated > '{timestamp_str}'"
        elif source == 'lovd':
            return f"SELECT * FROM lovd_variants WHERE last_updated > '{timestamp_str}'"
        elif source == 'gnomad':
            return f"SELECT * FROM gnomad_variants WHERE release_date > '{timestamp_str}'"

    def _check_clinvar_version(self, last_version: str) -> bool:
        """Check if ClinVar has newer version."""
        # Implementation would query ClinVar API
        pass

    def _check_lovd_version(self, last_version: str) -> bool:
        """Check if LOVD has newer version."""
        # Implementation would query LOVD API
        pass

    def _check_gnomad_version(self, last_version: str) -> bool:
        """Check if gnomAD has newer version."""
        # Implementation would check gnomAD release notes
        pass
```

**Duration:** 6-8 hours

---

#### 2.4.2 Intelligent Import Flow

**File:** `app/back_end/src/routes/import_route.py` (MODIFY)

**Current Flow (Approximate):**
```python
@app.route('/api/v1/import', methods=['POST'])
def import_data():
    source = request.json['source']  # clinvar, lovd, gnomad
    file_data = request.files['file']

    # Load CSV and import
    df = pd.read_csv(file_data)
    variants = dataframe_to_variants(df, source)
    db_session.bulk_save_objects(variants)
    db_session.commit()

    return {'status': 'success'}
```

**Enhanced Flow:**
```python
@app.route('/api/v1/import', methods=['POST'])
def import_data():
    file_id = request.json.get('file_id')
    source = request.json['source']  # clinvar, lovd, gnomad

    # Start workflow audit
    audit = WorkflowAudit(
        file_id=file_id,
        operation='import',
        operation_stage='source_import',
        status='pending',
        parameters=json.dumps({
            'source': source,
            'timestamp': datetime.utcnow().isoformat()
        })
    )
    db_session.add(audit)
    db_session.commit()

    try:
        # Check if we need to download
        delta_mgr = DeltaSyncManager(db_session)
        should_download = delta_mgr.should_download(file_id, source)

        if not should_download:
            return {
                'status': 'skipped',
                'reason': 'Database already up-to-date',
                'audit_id': audit.id
            }

        # Get download query
        query = delta_mgr.get_delta_query(file_id, source,
                                         get_source_version(source))

        # Download data (full or delta)
        if request.files.get('file'):
            # CSV upload
            file_data = request.files['file']
            df = pd.read_csv(file_data)
            download_count = len(df)
        else:
            # Download from external source
            df = download_from_source(source, query)
            download_count = len(df)

        # Store as source variants
        source_variants = dataframe_to_source_variants(df, source)
        db_session.bulk_save_objects(source_variants)
        db_session.flush()

        # Update file tracking
        file = db_session.query(File).filter_by(id=file_id).first()
        file.source_variant_count += download_count
        file.import_timestamp = datetime.utcnow()
        file.import_status = 'completed'
        file.last_download_timestamp = datetime.utcnow()
        file.last_download_count = download_count

        # Update audit
        audit.input_count = 0
        audit.output_count = download_count
        audit.completed_at = datetime.utcnow()
        audit.status = 'completed'
        audit.results = json.dumps({
            'downloaded_count': download_count,
            'is_delta_sync': not should_download,
            'source_version': get_source_version(source)
        })

        db_session.commit()

        return {
            'status': 'success',
            'downloaded_count': download_count,
            'is_delta': not should_download,
            'audit_id': audit.id
        }

    except Exception as e:
        audit.status = 'failed'
        audit.error_message = str(e)
        db_session.commit()
        raise
```

**Duration:** 5-6 hours

---

### 2.5 Merge Operation Refactoring

**File:** `app/back_end/src/routes/merge_route.py` (MODIFY)

**Enhanced Merge with Database Storage:**

```python
@app.route('/api/v1/merge', methods=['POST'])
def merge_variants():
    workspace_id = request.json['workspace_id']
    file_id_1 = request.json['file_id_1']
    file_id_2 = request.json['file_id_2']
    merge_type = request.json.get('merge_type', 'outer')  # outer, inner

    # Get source variants
    sources_1 = db_session.query(SourceVariant)\
        .filter_by(file_id=file_id_1).all()
    sources_2 = db_session.query(SourceVariant)\
        .filter_by(file_id=file_id_2).all()

    # Convert to DataFrames
    df1 = pd.DataFrame([v.to_dict() for v in sources_1])
    df2 = pd.DataFrame([v.to_dict() for v in sources_2])

    # Merge
    if merge_type == 'outer':
        merged_df = pd.merge(df1, df2, on='gen_pos', how='outer')
    else:
        merged_df = pd.merge(df1, df2, on='gen_pos', how='inner')

    # Create merged file
    merged_file = File(
        workspace_id=workspace_id,
        name=f"Merged: {sources_1[0].source_database} + {sources_2[0].source_database}",
        file_type='merged',
        data_source='merged'
    )
    db_session.add(merged_file)
    db_session.flush()

    # Store merged variants
    merged_variants = []
    for idx, row in merged_df.iterrows():
        mv = MergedVariant(
            merged_file_id=merged_file.id,
            chromosome=row.get('chromosome'),
            position=row.get('position'),
            ref_allele=row.get('ref_allele'),
            alt_allele=row.get('alt_allele'),
            gen_pos=row.get('gen_pos'),
            gene=row.get('gene'),
            transcript=row.get('transcript'),
            consequence=row.get('consequence'),
            source_databases=json.dumps([
                sources_1[0].source_database,
                sources_2[0].source_database
            ]),
            merge_strategy=merge_type
        )

        # Store source-specific data with column suffixes
        source_1_cols = {k: v for k, v in row.items()
                        if k.endswith('_x')}
        source_2_cols = {k: v for k, v in row.items()
                        if k.endswith('_y')}

        mv.clinvar_data = json.dumps(source_1_cols)
        mv.lovd_data = json.dumps(source_2_cols)

        merged_variants.append(mv)

    db_session.bulk_save_objects(merged_variants)

    # Update file tracking
    merged_file.merged_variant_count = len(merged_variants)
    merged_file.merge_status = 'completed'

    db_session.commit()

    return {
        'status': 'success',
        'merged_file_id': merged_file.id,
        'merged_count': len(merged_variants)
    }
```

**Duration:** 4-5 hours

---

### 2.6 Filtering Implementation

**File:** `app/back_end/src/data/filtering.py` (NEW/ENHANCE)

```python
from typing import List, Dict
from models import FilteredVariant, MergedVariant, SourceVariant

class VariantFilter:
    """Quality filtering for variant data."""

    def __init__(self, session):
        self.session = session
        self.rules = []

    def add_completeness_check(self):
        """Require all genomic fields present."""
        def check(variant: MergedVariant) -> bool:
            return all([
                variant.chromosome,
                variant.position,
                variant.ref_allele,
                variant.alt_allele
            ])
        self.rules.append(('completeness', check))

    def add_coordinate_validation(self):
        """Validate genomic coordinates."""
        def check(variant: MergedVariant) -> bool:
            try:
                pos = int(variant.position)
                return pos > 0 and len(variant.chromosome) > 0
            except:
                return False
        self.rules.append(('coordinate_validation', check))

    def add_allele_validation(self):
        """Validate allele strings (ACGT only)."""
        def check(variant: MergedVariant) -> bool:
            valid_bases = set('ACGTN')
            ref_valid = all(b in valid_bases for b in variant.ref_allele)
            alt_valid = all(b in valid_bases for b in variant.alt_allele)
            return ref_valid and alt_valid
        self.rules.append(('allele_validation', check))

    def filter_variants(self, source_variant_id: int = None,
                       merged_variant_id: int = None) -> List[Dict]:
        """Apply all filters to variants."""

        results = []

        if merged_variant_id:
            variants = [self.session.query(MergedVariant)\
                       .filter_by(id=merged_variant_id).first()]
        else:
            variants = self.session.query(MergedVariant).all()

        for variant in variants:
            filter_results = {}

            for rule_name, rule_func in self.rules:
                try:
                    passed = rule_func(variant)
                    filter_results[rule_name] = passed
                except Exception as e:
                    filter_results[rule_name] = False

            results.append({
                'variant': variant,
                'filter_results': filter_results,
                'passed_all': all(filter_results.values())
            })

        return results

    def store_filtered(self, file_id: int,
                      filter_results: List[Dict]) -> int:
        """Store filtered variants in database."""

        filtered_variants = []
        passed_count = 0

        for result in filter_results:
            if result['passed_all']:
                fv = FilteredVariant(
                    filtered_file_id=file_id,
                    merged_variant_id=result['variant'].id,
                    chromosome=result['variant'].chromosome,
                    position=result['variant'].position,
                    ref_allele=result['variant'].ref_allele,
                    alt_allele=result['variant'].alt_allele,
                    gen_pos=result['variant'].gen_pos,
                    is_complete=True,
                    is_valid=True,
                    filter_results=json.dumps(result['filter_results'])
                )
                filtered_variants.append(fv)
                passed_count += 1

        self.session.bulk_save_objects(filtered_variants)
        self.session.commit()

        return passed_count
```

**Duration:** 5-6 hours

---

### 2.7 Analysis Tools Database Integration

**File:** `app/back_end/src/tools/analysis_base.py` (NEW)

```python
from abc import ABC, abstractmethod
from models import FilteredVariant, Annotation

class DatabaseDrivenAnalyzer(ABC):
    """Base class for database-driven analysis tools."""

    def __init__(self, session, tool_name: str):
        self.session = session
        self.tool_name = tool_name

    def analyze_file(self, file_id: int) -> Dict[str, any]:
        """Analyze all variants in a file from database."""

        # Get filtered variants
        variants = self.session.query(FilteredVariant)\
            .filter_by(filtered_file_id=file_id).all()

        results = {
            'total_variants': len(variants),
            'analyzed': 0,
            'failed': 0,
            'tool': self.tool_name
        }

        for variant in variants:
            try:
                # Tool-specific analysis
                annotation_data = self._analyze_variant(variant)

                # Store in database
                annotation = Annotation(
                    variant_id=variant.id,
                    tool_name=self.tool_name,
                    score_value=annotation_data.get('score'),
                    score_label=annotation_data.get('label'),
                    metadata_json=json.dumps(annotation_data)
                )
                self.session.add(annotation)
                results['analyzed'] += 1

            except Exception as e:
                results['failed'] += 1
                results.setdefault('errors', []).append({
                    'variant_id': variant.id,
                    'error': str(e)
                })

        self.session.commit()
        return results

    @abstractmethod
    def _analyze_variant(self, variant: FilteredVariant) -> Dict:
        """Tool-specific analysis. Return dict with 'score' and 'label'."""
        pass
```

**Duration:** 3-4 hours

---

### 2.8 API Endpoints for Phase 2 Features

**File:** `app/back_end/src/routes/pipeline_route.py` (NEW)

```python
from flask import Blueprint, request, jsonify
from models import File, SourceVariant, MergedVariant, FilteredVariant
from data.delta_sync import DeltaSyncManager
from data.filtering import VariantFilter

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/v1/pipeline')

@pipeline_bp.route('/status/<file_id>', methods=['GET'])
def get_pipeline_status(file_id):
    """Get current pipeline status for a file."""
    file = db_session.query(File).filter_by(id=file_id).first()
    return jsonify({
        'file_id': file.id,
        'import_status': file.import_status,
        'import_count': file.source_variant_count,
        'merge_status': file.merge_status,
        'merge_count': file.merged_variant_count,
        'filter_status': file.filter_status,
        'filter_count': file.filtered_variant_count,
        'analysis_status': file.analysis_status,
        'analysis_count': file.analyzed_variant_count,
        'last_import': file.import_timestamp,
        'last_download_count': file.last_download_count
    })

@pipeline_bp.route('/source-variants/<file_id>', methods=['GET'])
def get_source_variants(file_id):
    """Get source variants with pagination."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 25, type=int)

    query = db_session.query(SourceVariant).filter_by(file_id=file_id)
    total = query.count()

    variants = query.limit(page_size).offset((page-1)*page_size).all()

    return jsonify({
        'data': [v.to_dict() for v in variants],
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size
        }
    })

@pipeline_bp.route('/merged-variants/<file_id>', methods=['GET'])
def get_merged_variants(file_id):
    """Get merged variants with pagination."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 25, type=int)

    query = db_session.query(MergedVariant).filter_by(merged_file_id=file_id)
    total = query.count()

    variants = query.limit(page_size).offset((page-1)*page_size).all()

    return jsonify({
        'data': [v.to_dict() for v in variants],
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size
        }
    })

@pipeline_bp.route('/filter', methods=['POST'])
def filter_variants():
    """Filter variants from database."""
    file_id = request.json['file_id']
    rules = request.json.get('rules', ['completeness', 'coordinate_validation'])

    # Create filtered file
    filtered_file = File(
        workspace_id=None,  # Set from request
        name=f"Filtered: {file_id}",
        file_type='filtered',
        data_source='filtered'
    )
    db_session.add(filtered_file)
    db_session.flush()

    # Apply filters
    vf = VariantFilter(db_session)
    if 'completeness' in rules:
        vf.add_completeness_check()
    if 'coordinate_validation' in rules:
        vf.add_coordinate_validation()
    if 'allele_validation' in rules:
        vf.add_allele_validation()

    # Filter and store
    filter_results = vf.filter_variants(merged_variant_id=file_id)
    passed_count = vf.store_filtered(filtered_file.id, filter_results)

    return jsonify({
        'status': 'success',
        'filtered_file_id': filtered_file.id,
        'passed': passed_count,
        'failed': len(filter_results) - passed_count
    })
```

**Duration:** 4-5 hours

---

### 2.9 Phase 2 Success Criteria

- [V] SourceVariant table populated with imported data
- [V] MergedVariant table stores merge results with source tracking
- [V] FilteredVariant table contains cleaned data with audit trail
- [V] WorkflowAudit table tracks all operations
- [V] Delta-sync detects existing data and only downloads new records
- [V] Import flow checks database before downloading
- [V] Merge operations store results in database
- [V] Filtering produces separate table with passed/failed flags
- [V] Analysis tools read from database and store results
- [V] All API endpoints return database-driven results
- [V] Pagination works at each pipeline stage
- [V] Download count optimized (delta-sync reduces data transfer)
- [V] CSV files completely optional (can export from DB)

### 2.10 Phase 2 Testing Plan

**Unit Tests:**
```python
def test_delta_sync_detection():
    """Test detection of existing data."""
    manager = DeltaSyncManager(session)

    # No data yet
    assert manager.should_download(file_id=1, source='clinvar')

    # After import
    create_source_variant(file_id=1, source='clinvar')
    assert not manager.should_download(file_id=1, source='clinvar')

def test_merge_variant_storage():
    """Test merged variant storage."""
    sv1 = create_source_variant(chromosome='1', position=1000)
    sv2 = create_source_variant(chromosome='1', position=1000)

    merge_result = merge_variants([sv1, sv2])
    mv = session.query(MergedVariant).first()

    assert mv.chromosome == '1'
    assert mv.position == 1000
    assert 'clinvar' in mv.source_databases

def test_filtering_rules():
    """Test variant filtering."""
    vf = VariantFilter(session)
    vf.add_completeness_check()

    complete_variant = create_variant(chromosome='1', position=1000)
    incomplete_variant = create_variant(chromosome=None, position=1000)

    results = vf.filter_variants()

    assert any(r['variant'].id == complete_variant.id and r['passed_all'])
    assert any(r['variant'].id == incomplete_variant.id and not r['passed_all'])
```

**Integration Tests:**
```python
def test_full_pipeline():
    """Test complete import→merge→filter→analyze flow."""

    # Import from ClinVar
    import_result = import_clinvar_data(file_id=1)
    assert import_result['status'] == 'success'
    assert session.query(SourceVariant).count() > 0

    # Merge with LOVD
    merge_result = merge_variants(file_id_1=1, file_id_2=2)
    assert merge_result['status'] == 'success'
    assert session.query(MergedVariant).count() > 0

    # Filter
    filter_result = filter_variants(file_id=1)
    assert filter_result['status'] == 'success'
    assert session.query(FilteredVariant).count() > 0

    # Analyze
    analysis_result = analyze_with_cadd(file_id=1)
    assert analysis_result['status'] == 'success'
    assert session.query(Annotation).count() > 0
```

**Duration:** 12-15 hours

---

### 2.11 Phase 2 Resource Estimate

| Component | Hours | Days |
|-----------|-------|------|
| 2.3 Data Models | 6 | 0.75 |
| 2.4 Delta-Sync | 8 | 1 |
| 2.5 Merge Refactor | 5 | 0.6 |
| 2.6 Filtering | 6 | 0.75 |
| 2.7 Analysis Tools | 4 | 0.5 |
| 2.8 API Endpoints | 5 | 0.6 |
| Testing | 15 | 1.9 |
| Integration | 10 | 1.25 |
| Documentation | 6 | 0.75 |
| **Total Phase 2** | **65** | **8.1 days** |

**Timeline:** 6-8 weeks with 50% development time allocation

---

## Phase 3: Migration Strategy & Deployment

### 3.1 Data Migration Plan

**Step 1: Backup Existing Data**
```bash
cp app/back_end/instance/kath.db app/back_end/instance/kath.db.backup
```

**Step 2: Run Alembic Migrations**
```bash
.venv/bin/alembic upgrade head
```

**Step 3: Validate New Tables**
```python
from models import SourceVariant, MergedVariant, FilteredVariant, WorkflowAudit
session.query(SourceVariant).count()  # Should be 0 initially
```

**Step 4: Import Existing Variants (if applicable)**
```python
# Convert existing Variant records to SourceVariant
for variant in session.query(Variant).all():
    sv = SourceVariant(
        source_database='legacy',
        file_id=variant.file_id,
        chromosome=variant.chromosome,
        position=variant.position,
        # ... copy other fields
    )
    session.add(sv)
session.commit()
```

**Duration:** 4-6 hours testing and validation

---

### 3.2 Rollback Procedure

If issues arise, rollback is straightforward:

```bash
# 1. Stop application
docker-compose down

# 2. Restore backup
cp app/back_end/instance/kath.db.backup app/back_end/instance/kath.db

# 3. Revert Alembic migrations
.venv/bin/alembic downgrade -1

# 4. Restart application
docker-compose up -d
```

**Duration:** 10-15 minutes

---

## Phase Comparison & Timeline

### Recommended Rollout Schedule

```
Week 1-3:   Phase 1 Implementation & Testing
            - Pagination UI
            - Database query optimization
            - Frontend integration

Week 4-5:   Phase 1 Production Deployment
            - Staged rollout
            - Performance monitoring
            - User feedback collection

Week 6-13:  Phase 2 Implementation & Testing
            - Data model extensions
            - Delta-sync optimization
            - Pipeline stages (merge, filter, analyze)
            - Comprehensive testing

Week 14-15: Phase 2 Production Deployment
            - Data migration
            - CSV deprecation planning
            - Training and documentation

Week 16+:   Optimization & Maintenance
            - Performance tuning
            - User support
            - Continuous improvement
```

### Resource Requirements

**Development Team:**
- 2-3 full-time developers for 4 months
- 1 QA engineer for testing phases
- 1 DevOps engineer for deployment

**Infrastructure:**
- Temporary staging database (for migration testing)
- Monitoring tools (query performance, disk usage)
- Backup storage (database backups)

**Timeline Summary:**
- **Phase 1:** 2-3 weeks
- **Phase 2:** 6-8 weeks
- **Deployment:** 2-3 weeks
- **Total:** 10-14 weeks

---

## Technical Considerations & Challenges

### Challenge 1: Query Performance at Scale

**Problem:** Database queries may slow with millions of records

**Mitigation:**
- Pre-computed indexes on frequently-filtered columns
- Query result caching (Redis)
- Pagination to limit result sets
- Monitoring and alerting for slow queries

**Solution:**
```python
# Add query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Monitor slow queries
from sqlalchemy.event import listens_for
from sqlalchemy.pool import Pool
import time

@listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    dbapi_conn.isolation_level = None

def log_slow_queries(conn, cursor, statement, parameters, context, executemany):
    start = time.time()
    if executemany:
        cursor.executemany(statement, parameters)
    else:
        cursor.execute(statement, parameters)
    duration = time.time() - start
    if duration > 1.0:  # Log queries > 1 second
        logging.warning(f"Slow query ({duration:.2f}s): {statement[:100]}")
```

---

### Challenge 2: Memory Usage During Merges

**Problem:** Merging large datasets may use excessive memory

**Mitigation:**
- Process in chunks instead of loading entire dataset
- Stream results to database incrementally
- Limit maximum merge size per operation

**Solution:**
```python
def merge_variants_chunked(file_id_1, file_id_2, chunk_size=10000):
    """Merge variants in chunks to manage memory."""
    offset = 0
    total_merged = 0

    while True:
        # Load chunk
        df1_chunk = load_variants_chunk(file_id_1, offset, chunk_size)
        df2_chunk = load_variants_chunk(file_id_2, offset, chunk_size)

        if df1_chunk.empty and df2_chunk.empty:
            break

        # Merge chunk
        merged_chunk = pd.merge(df1_chunk, df2_chunk, on='gen_pos', how='outer')

        # Store immediately
        store_merged_chunk(merged_chunk)
        total_merged += len(merged_chunk)

        offset += chunk_size

    return total_merged
```

---

### Challenge 3: Download Optimization Complexity

**Problem:** Different sources have different update patterns and APIs

**Mitigation:**
- Implement source-specific strategies
- Fallback to full download if delta detection fails
- Manual override for forced full sync

**Solution:**
```python
class SourceStrategy(ABC):
    @abstractmethod
    def get_latest_version(self) -> str:
        pass

    @abstractmethod
    def get_delta_query(self, since: datetime) -> str:
        pass

class ClinVarStrategy(SourceStrategy):
    def get_latest_version(self):
        # Query ClinVar FTP for version file
        # Example: clinvar_20240101.vcf.gz
        pass

    def get_delta_query(self, since):
        # ClinVar updates daily
        pass

class LovdStrategy(SourceStrategy):
    def get_latest_version(self):
        # Query LOVD API for version
        pass

    def get_delta_query(self, since):
        # LOVD supports timestamp-based queries
        pass
```

---

### Challenge 4: Coordinate System Consistency

**Problem:** Different sources may use different genome builds (hg19, hg38)

**Mitigation:**
- Standardize on hg38 throughout
- Store source coordinates with source-specific format
- Implement coordinate conversion on import

**Solution:**
```python
class GenomeCoordinateConverter:
    def __init__(self):
        self.liftover = pysam.CrossMap()

    def to_hg38(self, chrom, pos, source_build):
        if source_build == 'hg38':
            return chrom, pos
        elif source_build == 'hg19':
            # Use LiftOver
            converted = self.liftover.convert(chrom, pos)
            return converted
        else:
            raise ValueError(f"Unknown build: {source_build}")
```

---

### Challenge 5: Audit Trail Complexity

**Problem:** Tracking all transformations creates large audit tables

**Mitigation:**
- Archive old audit records
- Summarize operations periodically
- Implement retention policies

**Solution:**
```python
def archive_old_audits(days_threshold=90):
    """Archive audit records older than threshold."""
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)

    old_audits = session.query(WorkflowAudit)\
        .filter(WorkflowAudit.completed_at < cutoff).all()

    # Export to archive table or file
    for audit in old_audits:
        archive_record(audit)
        session.delete(audit)

    session.commit()
```

---

## Success Metrics & Validation

### Phase 1 Validation Checklist

- [ ] Pagination component displays without errors
- [ ] Page navigation buttons work correctly
- [ ] Page size selector changes results appropriately
- [ ] Statistics (showing X-Y of Z) display correct values
- [ ] Database queries execute in < 100ms
- [ ] Memory usage constant regardless of total dataset size
- [ ] Count cache working (verify via query timing)
- [ ] All variant data fields visible and accessible
- [ ] CSV files still accessible as backup
- [ ] No regressions in existing functionality

### Phase 2 Validation Checklist

- [ ] SourceVariant table populated on import
- [ ] MergedVariant table shows source attribution
- [ ] FilteredVariant table contains only passing variants
- [ ] WorkflowAudit table tracks all operations
- [ ] Delta-sync reduces download size by > 50% on second import
- [ ] Merge operations complete without memory spikes
- [ ] Filtering produces correct pass/fail counts
- [ ] Analysis tools read from database and store results
- [ ] All pipeline stages accessible via API with pagination
- [ ] Can re-run analysis without re-importing data
- [ ] Export from database matches manual computation

### Performance Benchmarks

**Phase 1 Targets:**
- Page load: < 100ms
- Pagination navigation: < 200ms
- Count query: < 50ms (cached)
- Memory per-page: < 50MB

**Phase 2 Targets:**
- Delta-sync detection: < 500ms
- Import 100K records: < 30 seconds
- Merge operation: < 1 minute
- Filter operation: < 2 minutes
- Analysis tool per-variant: < 100ms

---

## Conclusion

This comprehensive plan provides a phased approach to transforming KATH from a
CSV-dependent system to a modern, scalable SQLite-backed architecture. Phase 1
focuses on providing users with a better visualization experience through
pagination and statistics, while Phase 2 implements the complete pipeline
storage infrastructure for true database-first operations.

The estimated timeline of 10-14 weeks allows for proper testing and validation
at each stage, with rollback procedures in place for safety.

By completing this plan, KATH will be positioned to handle:
- Datasets with millions of variants
- Complex multi-source analyses
- Reproducible, auditable workflows
- Intelligent data synchronization
- Superior user experience with pagination and statistics

---

**Plan Version:** 1.0
**Last Updated:** November 17, 2025
**Status:** Ready for Implementation
