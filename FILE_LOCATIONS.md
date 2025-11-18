# KATH Codebase - File Locations with Line Numbers

## Critical Files for Variant API Implementation

### 1. Route Handlers
- **Main variant endpoint handler**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_route.py`
  - Line 316-621: GET endpoint for variant data retrieval
  - Line 119-184: _get_file_from_database() function
  - Line 187-313: GET workspace structure endpoint
  - Line 624-837: PUT endpoint for saving data

### 2. Service Layer
- **Variant retrieval business logic**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/services/workspace_service.py`
  - Line 46-109: get_file_data() - main service method
  - Line 161-214: _variants_to_rows() - conversion logic
  - Line 111-137: _build_filter_dict() - filter building
  - Line 139-159: _parse_sort() - sort parsing

### 3. Data Access Layer (Repositories)
- **Database queries and variant filtering**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/repositories.py`
  - Line 272-461: VariantRepository class
  - Line 365-461: filter_variants() - main query method with filters & pagination
  - Line 292-321: find_by_file() - simple file variant query
  - Line 323-340: find_by_position() - position-based lookup
  - Line 342-362: find_by_gene() - gene-based lookup

### 4. Data Models
- **Variant ORM model**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/variant.py`
  - Line 16-71: Variant class definition
  - Line 39-71: Database table schema and indexes
  - Line 94-119: to_dict() method
  - Line 76-92: data property for JSON handling

- **File ORM model**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/file.py`
  - Line 16-103: File class definition
  - Line 65-80: header property for JSON parsing
  - Line 82-102: to_dict() method

- **Workspace ORM model**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/workspace.py`
  - Line (check file for model definition)

### 5. Configuration & Setup
- **Application settings**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/settings.py`
  - Line 106-110: use_database_backend configuration flag
  - Line 98-100: database_path configuration

- **Database configuration**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/config.py`
  - Line 20-41: get_database_uri() function
  - Line 44-89: configure_database() function
  - Line 92-116: init_db() function
  - Line 60-70: Connection pool settings

- **Route constants**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/constants.py`
  - Line 28-40: All API route definitions

- **App initialization**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/__init__.py`
  - Line 39-110: create_app() function
  - Line 95-98: Database initialization

- **Route blueprint registration**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/setup/router.py`
  - Line 29-55: router() function

### 6. Entry Point
- **Application startup**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/run.py`
  - Line 22: create_app() call
  - Line 30: socketio.run() call

### 7. Supporting Services
- **File management routes**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_file_route.py`

- **Import/Export routes**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_import_route.py`
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_export_route.py`

- **Data operation routes**
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_merge_route.py`
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_apply_route.py`
  - `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_aggregate_route.py`

### 8. Database Models (All)
- `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/__init__.py`
- `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/base.py`
- `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/annotation.py`
- `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/aggregation.py`

### 9. Database Module (All)
- `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/__init__.py`

### 10. Frontend (React/Vue)
- `/home/tch/KATH/kath-v0.2-alpha/app/front_end/`

---

## Quick Navigation

### To understand variant retrieval:
1. Start: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_route.py` (Line 316-399)
2. Then: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/services/workspace_service.py` (Line 46-109)
3. Then: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/repositories.py` (Line 365-461)
4. Reference: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/variant.py` (Line 1-138)

### To understand configuration:
1. Start: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/settings.py` (Line 106-110)
2. Then: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/config.py` (Line 44-89)
3. Then: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/__init__.py` (Line 95-98)

### To understand filtering & pagination:
1. Reference: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/routes/workspace_route.py` (Line 381-399)
2. Implementation: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/database/repositories.py` (Line 395-459)

### To understand data models:
1. Variant: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/variant.py`
2. File: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/file.py`
3. Workspace: `/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/models/workspace.py`

