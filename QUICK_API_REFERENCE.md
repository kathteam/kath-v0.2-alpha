# KATH API Quick Reference Guide

## Main Variant Data Endpoint

### Get Variants (with Filtering & Pagination)
```
GET /api/v1/workspace/file/<relative_path>
```

**Headers:**
```
uuid: <workspace-uuid>
sid: <session-id>
```

**Query Parameters:**
```
page=0
rowsPerPage=100
filters={"gene": {"operator": "contains", "value": "BRCA1"}}
sorts={"position": "asc"}
```

**Response:**
```json
{
  "page": 0,
  "totalRows": 5000,
  "header": ["chromosome", "position", "ref_allele", ...],
  "rows": [["chr1", "100001", "A", ...], ...]
}
```

---

## Core File Locations

| Layer | File | Key Classes/Functions |
|-------|------|----------------------|
| **Routes** | `back_end/src/routes/workspace_route.py` | `get_workspace_file()`, `_get_file_from_database()` |
| **Service** | `back_end/src/services/workspace_service.py` | `WorkspaceService.get_file_data()` |
| **Repository** | `back_end/src/database/repositories.py` | `VariantRepository.filter_variants()` |
| **Models** | `back_end/src/models/variant.py` | `Variant` ORM model |
| **Settings** | `back_end/src/settings.py` | `use_database_backend` config |
| **Config** | `back_end/src/database/config.py` | Database initialization |

---

## Variant Database Schema

**Table: variants**
- Core fields: chromosome, position, ref_allele, alt_allele, gene, transcript, consequence
- Flexible storage: data_json (for custom columns)
- Indexes: file_id+row_index, chromosome+position+ref+alt, variant_id, gen_pos, gene

---

## Filter Operators

String: `contains`, `does-not-contain`, `equals`, `does-not-equal`, `starts-with`, `ends-with`, `is-empty`, `is-not-empty`
Numeric: `gt`, `gte`, `lt`, `lte`

---

## Data Flow

```
Request → Route Handler → Service Layer → Repository → Database
         (workspace_route.py)  (WorkspaceService)  (VariantRepository)
                ↓
         [Filter & Sort Applied in Repository Layer]
                ↓
         Variants → Convert to Rows → Return JSON Response
```

---

## Configuration

**Enable/Disable Database Backend:**
```
USE_DATABASE_BACKEND=true  (or .env file in back_end/)
```

**Database Location:**
```
instance/kath.db (configurable via DATABASE_PATH setting)
```

---

## Key Implementation Details

**Pagination Calculation:**
- offset = page * rowsPerPage
- Returns: page, totalRows, header, rows

**Sorting:**
- Single column sort supported
- Default: row_index (original CSV order)

**Filtering:**
- Multiple filter conditions combined with AND logic
- Case-insensitive string matching
- Dynamic column mapping for custom columns

**Response Format:**
- All variants converted to row format (list of lists)
- Maintains column order from file.header_json
- Custom columns extracted from variant.data_json

