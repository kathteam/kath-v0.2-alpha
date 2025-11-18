# KATH API Endpoints Structure Analysis

## Overview
The KATH application uses a Flask-based REST API with SQLAlchemy ORM for database operations. Variant data is managed through a service layer that abstracts database operations and provides filtering, sorting, and pagination capabilities.

---

## 1. BACKEND ROUTES DIRECTORY STRUCTURE

### Location
`/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/`

### Route Files
- `workspace_route.py` - Main variant data retrieval endpoints (1,171 lines)
- `workspace_file_route.py` - File management operations
- `workspace_import_route.py` - Import functionality
- `workspace_export_route.py` - Export functionality
- `workspace_download_route.py` - Download operations
- `workspace_merge_route.py` - Data merging operations
- `workspace_apply_route.py` - Tool application routes
- `workspace_align_route.py` - Sequence alignment
- `workspace_aggregate_route.py` - Data aggregation
- `workspace_mgmt_route.py` - Workspace management
- `monitoring_route.py` - System monitoring

---

## 2. CURRENT ENDPOINT STRUCTURE

### Base Route Configuration
**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/constants.py` (Lines 28-40)

```python
BASE_ROUTE = "/api/v1"
WORKSPACE_ROUTE = "/workspace"
WORKSPACE_FILE_ROUTE = "/workspace/file"
```

### Active API Endpoints

#### 2.1 Get Workspace Structure
**Endpoint**: `GET /api/v1/workspace`

**File**: `workspace_route.py` Lines 187-313

**Headers Required**:
- `uuid` - Workspace UUID
- `sid` - Session ID

**Returns**:
```json
{
  "file_type": "folder|file",
  "name": "filename",
  "path": "relative/path",
  "children": [...],
  "row_count": 1000,
  "column_count": 10
}
```

**Status Codes**:
- `200 OK` - Workspace structure retrieved
- `400 Bad Request` - Missing uuid/sid headers
- `403 Forbidden` - Permission denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Unexpected error

---

#### 2.2 Get File Data (Variants)
**Endpoint**: `GET /api/v1/workspace/file/<path:relative_path>`

**File**: `workspace_route.py` Lines 316-621

**Headers Required**:
- `uuid` - Workspace UUID
- `sid` - Session ID

**Query Parameters**:
```
page=0                      # Page number (0-indexed)
rowsPerPage=100             # Rows per page (default: 100)
filters={"column_name": {"operator": "contains", "value": "search_term"}}
sorts={"column_name": "asc"}  # asc or desc
```

**Supported Filter Operators** (Lines 413-497):
- `contains` - Case-insensitive substring match
- `does-not-contain` - Exclude substring match
- `equals` - Case-insensitive exact match
- `does-not-equal` - Exclude exact match
- `starts-with` - String starts with value
- `ends-with` - String ends with value
- `is-empty` - Empty or null value
- `is-not-empty` - Non-empty value
- `gt` - Greater than (numeric)
- `gte` - Greater than or equal (numeric)
- `lt` - Less than (numeric)
- `lte` - Less than or equal (numeric)

**Response Format** (Lines 562-567):
```json
{
  "page": 0,
  "totalRows": 5000,
  "header": ["chromosome", "position", "ref_allele", "alt_allele", "variant_id", "gen_pos", "gene", "transcript", "consequence", ...],
  "rows": [
    ["chr1", "100001", "A", "T", "rs123456", "chr1-100001-A-T", "GENE1", "ENST0000001", "missense_variant", ...],
    ...
  ]
}
```

**Data Source**:
- **If `USE_DATABASE_BACKEND=True`** (Line 397): Routes to database backend via `_get_file_from_database()`
- **If `USE_DATABASE_BACKEND=False`**: Reads from CSV files

---

#### 2.3 Save/Update File Data
**Endpoint**: `PUT /api/v1/workspace/file/<path:relative_path>`

**File**: `workspace_route.py` Lines 624-837

**Headers Required**:
- `uuid` - Workspace UUID
- `sid` - Session ID

**Request Body**:
```json
{
  "page": 0,
  "rowsPerPage": 100,
  "header": ["col1", "col2", ...],
  "rows": [["val1", "val2", ...], ...]
}
```

**Returns**: Success/error JSON response

---

#### 2.4 Create File/Folder
**Endpoint**: `PUT /api/v1/workspace/create/` or `PUT /api/v1/workspace/create/<path:relative_path>`

**File**: `workspace_route.py` Lines 839-999

---

#### 2.5 Rename File
**Endpoint**: `PUT /api/v1/workspace/rename/<path:relative_path>`

**File**: `workspace_route.py` Lines 1001-1169

---

#### 2.6 Delete File
**Endpoint**: `PUT /api/v1/workspace/delete/<path:relative_path>`

**File**: `workspace_route.py` Lines 1171-1350

---

## 3. VARIANT DATA MODEL

### Variant Model Structure
**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/variant.py` (Lines 1-138)

#### Database Schema (Table: `variants`)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | Integer (PK) | NO | Auto-incrementing variant ID |
| `file_id` | Integer (FK) | NO | Parent file ID |
| `row_index` | Integer | NO | Original CSV row number |
| `chromosome` | String(10) | YES | Chromosome identifier (indexed) |
| `position` | Integer | YES | Genomic position |
| `ref_allele` | String(255) | YES | Reference allele |
| `alt_allele` | String(255) | YES | Alternative allele |
| `variant_id` | String(255) | YES | External variant ID (rs#, indexed) |
| `gen_pos` | String(255) | YES | Format: "chr-pos-ref-alt" (indexed) |
| `gene` | String(255) | YES | Gene symbol (indexed) |
| `transcript` | String(255) | YES | Transcript ID |
| `consequence` | String(255) | YES | Variant consequence/effect |
| `data_json` | Text | YES | JSON for additional columns |
| `created_at` | DateTime | NO | Timestamp |

#### Key Methods

**`to_dict(include_annotations=False)`** (Lines 94-119):
Converts variant to dictionary representation, optionally including annotations.

**`to_csv_row(columns=None)`** (Lines 121-137):
Converts variant to CSV row format.

**Data JSON Property** (Lines 76-92):
Flexible storage for additional CSV columns beyond core variant fields.

---

### File Model Structure
**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/file.py` (Lines 1-103)

#### Database Schema (Table: `files`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-incrementing file ID |
| `workspace_id` | String(255) (FK) | Parent workspace UUID |
| `name` | String(255) | File name |
| `path` | String(512) | Relative path within workspace (unique with workspace_id) |
| `file_type` | String(10) | "file" or "folder" |
| `parent_id` | Integer (FK) | Parent directory ID |
| `row_count` | Integer | Number of variant rows |
| `column_count` | Integer | Number of columns |
| `data_source` | String(50) | "gnomAD", "ClinVar", "LOVD", "Custom" |
| `header_json` | Text | JSON array of column names |
| `created_at` | DateTime | Timestamp |
| `updated_at` | DateTime | Update timestamp |

#### Relationships
- `variants` - One-to-many relationship with Variant model
- `aggregations` - Cached aggregations for file
- `children` - Hierarchical folder structure

---

## 4. HOW VARIANTS ARE RETRIEVED FROM DATABASE

### Database Retrieval Flow

#### Step 1: Route Handler
**File**: `workspace_route.py:316-399`

```python
@workspace_route_bp.route(f"{WORKSPACE_FILE_ROUTE}/<path:relative_path>", methods=["GET"])
def get_workspace_file(relative_path):
    # Extract headers and parameters
    uuid = request.headers.get("uuid")
    sid = request.headers.get("sid")
    
    # Get pagination and filtering parameters
    page = int(request.args.get("page", 0))
    rows_per_page = int(request.args.get("rowsPerPage", 100))
    
    # Check if database backend is enabled
    settings = get_settings()
    if settings.use_database_backend:
        return _get_file_from_database(uuid, sid, relative_path, page, rows_per_page, filter, sort)
```

#### Step 2: Service Layer
**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/services/workspace_service.py` (Lines 46-109)

```python
def get_file_data(
    self,
    workspace_id: str,
    file_path: str,
    page: int = 0,
    rows_per_page: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    sorts: Optional[Dict[str, str]] = None,
) -> Tuple[List[str], List[List[Any]], int]:
    """
    1. Validate workspace exists
    2. Get file record from FileRepository
    3. Parse header from file.header_json
    4. Build filter dictionary
    5. Query variants with VariantRepository.filter_variants()
    6. Convert variants to rows
    7. Return (header, rows, total_count)
    """
```

#### Step 3: Repository Layer
**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/repositories.py` (Lines 365-461)

```python
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
    1. Query Variant table filtered by file_id
    2. Apply filter conditions based on operator
    3. Apply sorting
    4. Count total matching records
    5. Apply pagination (offset/limit)
    6. Return variants and total count
    """
```

#### Step 4: Data Conversion
**File**: `workspace_service.py:161-214`

Converts Variant ORM objects to row format:
- Maps core columns: chromosome, position, ref_allele, alt_allele, etc.
- Extracts additional columns from data_json
- Returns rows as list of lists

### Configuration Control

**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/settings.py` (Lines 106-110)

```python
use_database_backend: bool = Field(
    default=True,
    description="Use database for variant data instead of CSV files",
    validation_alias="USE_DATABASE_BACKEND",
)
```

---

## 5. DATA FORMAT RETURNED TO FRONTEND

### Standard Response Format

**Success Response (HTTP 200)**:
```json
{
  "page": 0,
  "totalRows": 5000,
  "header": [
    "chromosome",
    "position",
    "ref_allele",
    "alt_allele",
    "variant_id",
    "gen_pos",
    "gene",
    "transcript",
    "consequence",
    "custom_col1",
    "custom_col2"
  ],
  "rows": [
    [
      "chr1",
      "100001",
      "A",
      "T",
      "rs123456",
      "chr1-100001-A-T",
      "BRCA1",
      "ENST00000007392",
      "missense_variant",
      "value1",
      "value2"
    ],
    [
      "chr2",
      "200002",
      "G",
      "C",
      "rs789012",
      "chr2-200002-G-C",
      "TP53",
      "ENST00000269305",
      "frameshift_variant",
      "value3",
      "value4"
    ]
  ]
}
```

### Column Mapping

#### Core Variant Columns (from Variant model)
- `chromosome` - chromosome attribute
- `position` - position attribute
- `ref_allele` - ref_allele attribute
- `alt_allele` - alt_allele attribute
- `variant_id` - variant_id attribute
- `gen_pos` - gen_pos attribute
- `gene` - gene attribute
- `transcript` - transcript attribute
- `consequence` - consequence attribute

#### Additional Columns
- Stored in `data_json` field as JSON
- Dynamically extracted based on file header

### WebSocket Events

**File**: `constants.py:42-46`

Feedback events emitted to frontend:
```python
CONSOLE_FEEDBACK_EVENT = "console_feedback"
WORKSPACE_FILE_SAVE_FEEDBACK_EVENT = "workspace_file_save_feedback"
WORKSPACE_UPDATE_FEEDBACK_EVENT = "workspace_update_feedback"
```

---

## 6. FILTERING & PAGINATION LOGIC

### Pagination Implementation

**Request Parameters**:
```
page=0              # Zero-indexed page number
rowsPerPage=100     # Records per page
```

**Calculation**:
```python
start_row = page * rows_per_page
end_row = start_row + rows_per_page
offset = page * rows_per_page
```

**Repository Query** (repositories.py:456-459):
```python
if offset:
    query = query.offset(offset)
if limit:
    query = query.limit(limit)
```

### Filtering Logic

**Filter Dictionary Format**:
```json
{
  "column_name": {
    "operator": "contains|equals|starts-with|...",
    "value": "search_term"
  }
}
```

**Supported Operators** (repositories.py:413-436):

| Operator | Implementation | Data Type |
|----------|-----------------|-----------|
| `contains` | `ILIKE %value%` | String |
| `does-not-contain` | `NOT ILIKE %value%` | String |
| `equals` | `ILIKE value` (case-insensitive) | String |
| `does-not-equal` | `NOT ILIKE value` | String |
| `starts-with` | `ILIKE value%` | String |
| `ends-with` | `ILIKE %value` | String |
| `is-empty` | `= '' OR IS NULL` | Any |
| `is-not-empty` | `!= '' AND IS NOT NULL` | Any |
| `gt` | `>` | Numeric |
| `gte` | `>=` | Numeric |
| `lt` | `<` | Numeric |
| `lte` | `<=` | Numeric |

**Filter Application** (repositories.py:438-439):
```python
if conditions:
    query = query.filter(and_(*conditions))
```

### Sorting Implementation

**Sort Dictionary Format**:
```json
{
  "column_name": "asc|desc"
}
```

**Sort Application** (repositories.py:441-450):
```python
if sort_column and hasattr(Variant, sort_column):
    col_attr = getattr(Variant, sort_column)
    if sort_order == "desc":
        query = query.order_by(desc(col_attr))
    else:
        query = query.order_by(col_attr)
else:
    # Default sort by row_index
    query = query.order_by(Variant.row_index)
```

**Default Sort**: `row_index` (preserves original CSV order)

---

## 7. KEY IMPLEMENTATION FILES & LOCATIONS

### Route Handlers
| File | Purpose | Key Lines |
|------|---------|-----------|
| `workspace_route.py` | Main variant data endpoints | 119-621 (database retrieval), 316-621 (GET file) |
| `workspace_file_route.py` | File operation helpers | - |
| `workspace_import_route.py` | Import variants | - |
| `workspace_export_route.py` | Export variants | - |

### Service Layer
| File | Purpose | Key Lines |
|------|---------|-----------|
| `workspace_service.py` | Business logic, filtering, sorting | 46-109 (get_file_data), 365-461 (filter_variants) |

### Data Access Layer
| File | Purpose | Key Lines |
|------|---------|-----------|
| `repositories.py` | Database queries | 272-461 (VariantRepository) |
| `config.py` | SQLAlchemy configuration | All |

### Models
| File | Purpose | Key Lines |
|------|---------|-----------|
| `variant.py` | Variant ORM model | All |
| `file.py` | File/folder ORM model | All |
| `workspace.py` | Workspace ORM model | - |

### Configuration
| File | Purpose | Key Lines |
|------|---------|-----------|
| `settings.py` | App configuration | 106-110 (use_database_backend) |
| `constants.py` | Route definitions | 28-40 |

---

## 8. APPLICATION INITIALIZATION

**Entry Point**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/run.py`

**App Creation Flow** (src/__init__.py:39-110):

1. **Gevent Monkey Patching** (Line 60)
2. **Flask App Creation** (Line 63)
3. **Logging Setup** (Lines 65-68)
4. **App Configuration** (Lines 70-74)
   - Compression enabled for CSV
   - CORS configuration from environment
5. **Request Logging Middleware** (Line 77)
6. **Flask Extensions** (Lines 80-92)
   - Compression
   - Socket.IO
   - CORS
7. **Database Initialization** (Lines 95-98)
8. **Event Handlers** (Lines 101-102)
9. **Route Registration** (Lines 105-106)
   - Routes registered at `/api/v1` prefix

---

## 9. DATABASE CONFIGURATION

**Database URI**: SQLite at `instance/kath.db` (configurable via settings)

**File**: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/config.py`

**Connection Pool Settings** (Lines 60-70):
```python
pool_size = 20
max_overflow = 10
pool_recycle = 3600
pool_pre_ping = True
pool_timeout = 30
SQLite timeout = 30
check_same_thread = False
isolation_level = None (autocommit)
```

---

## 10. SUMMARY TABLE: VARIANT DATA FLOW

```
Frontend Request
    ↓
GET /api/v1/workspace/file/<path>?page=0&rowsPerPage=100&filters={}&sorts={}
    ↓
workspace_route.py: get_workspace_file() [Line 318]
    ↓
Check: settings.use_database_backend [Line 397]
    ↓
workspace_service.py: get_file_data() [Line 46]
    ├→ WorkspaceRepository.find_by_uuid()
    ├→ FileRepository.find_by_path() [Get file metadata & header]
    ├→ VariantRepository.filter_variants() [Line 97]
    │   ├→ Query variants by file_id
    │   ├→ Apply filters [Lines 395-439]
    │   ├→ Apply sorting [Lines 441-450]
    │   ├→ Count total [Line 453]
    │   ├→ Apply pagination [Lines 456-459]
    │   └→ Return variants + count
    └→ Convert variants to rows [Line 107]
    ↓
Response JSON: {page, totalRows, header, rows}
    ↓
Frontend receives and renders data
```

---

## 11. NOTES FOR ENHANCEMENT

### Current Capabilities
- Flexible filtering with 12+ operators
- Sorting support (single column)
- Pagination with configurable page size
- Extensible JSON column storage
- Composite indexes for performance
- Database profiling and caching decorators

### Potential Areas for Enhancement
1. **Multi-column sorting** - Currently single column only
2. **Advanced filtering** - OR conditions between filters (currently AND only)
3. **Search API** - Dedicated text search endpoint
4. **Variant-specific queries** - By gene, position, annotation scores
5. **Annotation filtering** - Filter by tool scores (SpliceAI, CADD, etc.)
6. **Export with filters** - Export filtered results directly
7. **Query caching** - Cache filtered result sets for frequent queries

