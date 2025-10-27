# KATH Project Refactoring Plan
## Comprehensive Modernization & Enhancement Strategy

**Version:** 0.3-alpha Planning Document
**Date:** 2025-10-27
**Current Version:** 0.2-alpha

---

## Executive Summary

This document outlines a comprehensive refactoring plan for the KATH genetic analysis tool. The plan addresses critical technical debt, adds new features, and modernizes the architecture to support scalability, maintainability, and user experience improvements.

### Key Objectives
1. Replace CSV-based storage with SQLite database
2. Modernize frontend for responsive design and statistical analysis
3. Create robust backend API for DNA analysis tool integration
4. Improve code maintainability and testability
5. Add new DNA analysis tools and capabilities

### Prioritization Strategy
Improvements are ordered from **simplest to most complex**, allowing incremental delivery and reducing risk. Each phase builds upon the previous, enabling early wins while working toward comprehensive modernization.

---

## Current State Assessment

### Backend Architecture
- **Framework**: Flask 3.0.3 with Socket.IO for real-time communication
- **Data Storage**: CSV files with pagination/filtering via pandas
- **Tools Integrated**: SpliceAI, CADD, REVEL
- **Server**: Gunicorn with Gevent async runtime
- **Session Management**: Redis-based WebSocket tracking

### Frontend Architecture
- **Framework**: React 18.3.1 + TypeScript 5.6.3
- **Build Tool**: Vite 7.1.11
- **UI Library**: Material-UI (MUI) 5.16.7
- **State Management**: React Context API
- **Communication**: Axios (REST) + Socket.IO (WebSocket)

### Identified Issues
1. **Data Storage**: CSV files lack transaction support, difficult to query
2. **Frontend Responsiveness**: Fixed viewport units, no mobile support
3. **Backend Modularity**: Monolithic route files (1260+ lines)
4. **Tool Integration**: No standardized interface for adding new tools
5. **Statistical Analysis**: Limited data analysis capabilities in UI
6. **Testing**: No visible test infrastructure
7. **Documentation**: Limited API documentation

---

## Refactoring Phases

The plan is divided into **5 phases** with **30 tasks** total, organized from simplest to most complex.

---

# PHASE 1: Quick Wins & Foundation (Weeks 1-3)
**Complexity: Low | Impact: High | Risk: Low**

These tasks provide immediate value with minimal code disruption.

---

## Task 1.1: Add Comprehensive Documentation
**Complexity**:  (Very Simple)
**Estimated Time**: 2-3 days
**Dependencies**: None

### Description
Document existing API endpoints, data models, and setup procedures.

### Deliverables
- [ ] API endpoint documentation (OpenAPI/Swagger spec)
- [ ] Backend architecture diagram
- [ ] Frontend component hierarchy diagram
- [ ] Development setup guide
- [ ] Contribution guidelines

### Implementation Steps
1. Install Swagger/OpenAPI dependencies
2. Add decorators to existing Flask routes
3. Generate API documentation at `/api/docs`
4. Create architecture diagrams using Mermaid or draw.io
5. Write developer onboarding guide

### Success Criteria
- All API endpoints documented with request/response schemas
- New developers can set up environment in < 30 minutes
- Architecture diagrams available in `/docs/architecture/`

---

## Task 1.2: Implement Comprehensive Logging
**Complexity**:  (Very Simple)
**Estimated Time**: 2 days
**Dependencies**: None

### Description
Standardize logging across backend with structured logging format.

### Deliverables
- [ ] Centralized logger configuration
- [ ] Log rotation setup
- [ ] Request/response logging middleware
- [ ] Error tracking integration (optional: Sentry)

### Implementation Steps
1. Create `src/utils/logger.py` with Python's logging module
2. Configure JSON-formatted logs for production
3. Add request ID tracking for distributed tracing
4. Implement log rotation (size-based and time-based)
5. Add logging decorators for route handlers

### Success Criteria
- All routes log requests with timing information
- Errors logged with full stack traces
- Logs queryable by request ID
- Log files rotated automatically

---

## Task 1.3: Add Backend Unit Tests
**Complexity**:  (Simple)
**Estimated Time**: 5 days
**Dependencies**: None

### Description
Establish test framework and add tests for critical functions.

### Deliverables
- [ ] pytest configuration
- [ ] Test fixtures for common scenarios
- [ ] Unit tests for data processing functions
- [ ] Unit tests for tool integrations (SpliceAI, CADD, REVEL)
- [ ] CI/CD integration for test running

### Implementation Steps
1. Install pytest, pytest-flask, pytest-cov
2. Create `tests/` directory structure
3. Write fixtures for test data (CSV files, mock responses)
4. Test data processing utilities in `src/data/`
5. Test tool integrations with mocked external calls
6. Configure GitHub Actions for automated testing

### Success Criteria
- Test coverage > 60% for backend code
- All tool integrations have unit tests
- Tests run automatically on pull requests
- Test execution time < 5 minutes

---

## Task 1.4: Environment Configuration Refactor
**Complexity**:  (Simple)
**Estimated Time**: 2 days
**Dependencies**: None

### Description
Replace static Env class with proper configuration management.

### Deliverables
- [ ] pydantic-settings for configuration validation
- [ ] Type-safe configuration objects
- [ ] Environment-specific config files
- [ ] Configuration validation on startup

### Implementation Steps
1. Install `pydantic-settings`
2. Create `src/config.py` with `BaseSettings` classes
3. Define configuration schemas with types
4. Add validation rules (port ranges, URL formats)
5. Load configuration in `create_app()`
6. Update all usages of `Env` class

### Success Criteria
- Configuration errors detected on startup
- All environment variables documented
- Type hints for configuration values
- Invalid configuration prevents app start

---

## Task 1.5: Frontend Responsive Design - Phase 1
**Complexity**:  (Simple)
**Estimated Time**: 4 days
**Dependencies**: None

### Description
Add responsive breakpoints and mobile-friendly layouts.

### Deliverables
- [ ] MUI breakpoint system implemented
- [ ] Mobile navigation menu
- [ ] Responsive editor layout
- [ ] Touch-friendly interactions

### Implementation Steps
1. Define breakpoints (xs, sm, md, lg, xl)
2. Implement `useMediaQuery` hooks
3. Create mobile sidebar (drawer component)
4. Make file tree collapsible
5. Stack editor components vertically on mobile
6. Increase button sizes for touch (min 44x44px)
7. Test on real devices (iPhone, Android, iPad)

### Success Criteria
- App usable on screens  480px width
- File tree accessible via drawer on mobile
- Data grid scrollable horizontally
- No layout breaks at common resolutions

---

## Task 1.6: Code Quality Tools
**Complexity**:  (Very Simple)
**Estimated Time**: 1 day
**Dependencies**: None

### Description
Add linting, formatting, and pre-commit hooks.

### Deliverables
- [ ] Backend: Black, isort, flake8, mypy
- [ ] Frontend: ESLint, Prettier (already present)
- [ ] Pre-commit hooks for both
- [ ] CI/CD checks for code quality

### Implementation Steps
1. Install pre-commit framework
2. Configure `.pre-commit-config.yaml`
3. Add black, isort, flake8, mypy checks
4. Run on all existing code (fix violations)
5. Add to CI/CD pipeline

### Success Criteria
- All Python code formatted with Black
- Type hints checked with mypy
- Pre-commit hooks prevent bad commits
- CI fails on linting errors

---

# PHASE 2: Database Migration (Weeks 4-7)
**Complexity: Medium | Impact: Very High | Risk: Medium**

Replace CSV storage with SQLite database for better performance and querying.

---

## Task 2.1: Database Schema Design
**Complexity**:  (Simple)
**Estimated Time**: 3 days
**Dependencies**: Task 1.1 (Documentation)

### Description
Design normalized database schema for genetic data.

### Deliverables
- [ ] ER diagram for database schema
- [ ] SQLAlchemy models
- [ ] Migration strategy from CSV to SQLite
- [ ] Data validation rules

### Implementation Steps
1. Analyze current CSV file structures
2. Design normalized schema:
   - `workspaces` table (user workspaces)
   - `files` table (file metadata)
   - `variants` table (genetic variants)
   - `annotations` table (tool annotations)
   - `aggregations` table (cached aggregations)
3. Create SQLAlchemy models in `src/models/`
4. Define indexes for common queries
5. Document schema in ER diagram

### Proposed Schema
```sql
-- Workspaces
CREATE TABLE workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    UNIQUE (workspace_id, path)
);

-- Variants
CREATE TABLE variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    chromosome TEXT NOT NULL,
    position INTEGER NOT NULL,
    ref_allele TEXT NOT NULL,
    alt_allele TEXT NOT NULL,
    variant_id TEXT,
    gene TEXT,
    transcript TEXT,
    consequence TEXT,
    -- Additional columns from CSV files
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    INDEX idx_variant_lookup (chromosome, position, ref_allele, alt_allele)
);

-- Annotations
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    annotation_type TEXT NOT NULL,
    value REAL,
    metadata TEXT, -- JSON field for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE,
    INDEX idx_tool_name (tool_name)
);

-- Aggregations (cached)
CREATE TABLE aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    operation TEXT NOT NULL, -- SUM, AVG, MIN, MAX, COUNT
    value REAL NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE (file_id, column_name, operation)
);
```

### Success Criteria
- Schema supports all current CSV data types
- Indexes defined for common queries
- SQLAlchemy models map to schema
- Migration path documented

---

## Task 2.2: Database Layer Implementation
**Complexity**:  (Medium)
**Estimated Time**: 5 days
**Dependencies**: Task 2.1

### Description
Implement database access layer with SQLAlchemy ORM.

### Deliverables
- [ ] SQLAlchemy setup with Flask-SQLAlchemy
- [ ] Repository pattern for data access
- [ ] Database migration tools (Alembic)
- [ ] Connection pooling configuration

### Implementation Steps
1. Install Flask-SQLAlchemy, Alembic
2. Create `src/database/` module
3. Implement repository classes:
   - `WorkspaceRepository`
   - `FileRepository`
   - `VariantRepository`
   - `AnnotationRepository`
4. Add connection pooling configuration
5. Create Alembic migration scripts
6. Implement database initialization script

### Repository Pattern Example
```python
class VariantRepository:
    def __init__(self, session):
        self.session = session

    def create(self, variant_data: dict) -> Variant:
        variant = Variant(**variant_data)
        self.session.add(variant)
        self.session.commit()
        return variant

    def find_by_id(self, variant_id: int) -> Optional[Variant]:
        return self.session.query(Variant).filter_by(id=variant_id).first()

    def find_by_file(self, file_id: int, page: int = 1, per_page: int = 25) -> List[Variant]:
        return self.session.query(Variant)\
            .filter_by(file_id=file_id)\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()

    def count_by_file(self, file_id: int) -> int:
        return self.session.query(Variant).filter_by(file_id=file_id).count()
```

### Success Criteria
- All database operations use repositories
- Transactions properly managed
- Connection pooling configured
- Alembic migrations working

---

## Task 2.3: CSV to SQLite Migration Tool
**Complexity**:  (Medium)
**Estimated Time**: 5 days
**Dependencies**: Task 2.2

### Description
Create command-line tool to migrate existing CSV data to SQLite.

### Deliverables
- [ ] Migration script with progress tracking
- [ ] Data validation during migration
- [ ] Rollback capability
- [ ] Migration documentation

### Implementation Steps
1. Create `src/scripts/migrate_csv_to_db.py`
2. Implement CSV parsing with pandas
3. Batch insert variants (1000 rows at a time)
4. Validate data integrity after migration
5. Generate migration report (rows migrated, errors)
6. Test on template workspace
7. Create backup strategy

### Migration Script Structure
```python
def migrate_workspace(workspace_path: str, db_session):
    # 1. Create workspace record
    workspace = create_workspace_from_path(workspace_path)

    # 2. Iterate through CSV files
    for csv_file in find_csv_files(workspace_path):
        # 3. Create file record
        file_record = create_file_record(csv_file, workspace.id)

        # 4. Read CSV in chunks
        for chunk in pd.read_csv(csv_file, chunksize=1000):
            # 5. Transform to variant records
            variants = transform_chunk_to_variants(chunk, file_record.id)

            # 6. Bulk insert
            db_session.bulk_insert_mappings(Variant, variants)
            db_session.commit()

        # 7. Update file row count
        update_file_row_count(file_record.id, db_session)

    # 8. Generate migration report
    return MigrationReport(workspace_id=workspace.id, ...)
```

### Success Criteria
- All CSV data migrated to database
- No data loss during migration
- Migration completes in reasonable time (<10 min for template)
- Validation confirms data integrity

---

## Task 2.4: Update Backend Routes for Database
**Complexity**:  (Complex)
**Estimated Time**: 10 days
**Dependencies**: Task 2.3

### Description
Refactor all route handlers to use database instead of CSV files.

### Deliverables
- [ ] Updated workspace routes
- [ ] Updated file routes
- [ ] Updated data processing routes
- [ ] Backward compatibility layer (optional)

### Implementation Steps
1. Update `workspace_route.py`:
   - Replace file tree generation with DB queries
   - Update pagination to use SQL LIMIT/OFFSET
   - Replace filtering with SQL WHERE clauses
2. Update `workspace_apply_route.py`:
   - Store tool results in `annotations` table
   - Update progress tracking
3. Update `workspace_merge_route.py`:
   - Implement SQL JOIN operations
4. Update `workspace_aggregate_route.py`:
   - Use SQL aggregate functions (SUM, AVG, etc.)
   - Cache results in `aggregations` table
5. Update `workspace_import_route.py`:
   - Parse CSV and insert into database
6. Update `workspace_export_route.py`:
   - Generate CSV from database queries
7. Add database session management to routes
8. Update error handling for database exceptions

### Route Refactoring Example
```python
# Before (CSV-based)
@workspace_route_bp.route('/workspace/file/<path:relative_path>', methods=['GET'])
def get_file(relative_path):
    df = pd.read_csv(get_file_path(relative_path))
    # Pagination, filtering, sorting logic
    return jsonify(df.to_dict())

# After (Database-based)
@workspace_route_bp.route('/workspace/file/<path:relative_path>', methods=['GET'])
def get_file(relative_path):
    file_id = get_file_id_from_path(relative_path)
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 25)

    variant_repo = VariantRepository(db.session)
    variants = variant_repo.find_by_file(file_id, page, per_page)
    total = variant_repo.count_by_file(file_id)

    return jsonify({
        'data': [v.to_dict() for v in variants],
        'pagination': {'page': page, 'per_page': per_page, 'total': total}
    })
```

### Success Criteria
- All routes using database queries
- Performance equal or better than CSV
- API contracts unchanged (frontend compatibility)
- Tests passing for all routes

---

## Task 2.5: Frontend Updates for Database Backend
**Complexity**:  (Simple)
**Estimated Time**: 3 days
**Dependencies**: Task 2.4

### Description
Update frontend to handle database-backed API responses.

### Deliverables
- [ ] Updated API response types
- [ ] Updated data grid pagination
- [ ] Updated filtering/sorting logic
- [ ] Error handling for database errors

### Implementation Steps
1. Review API response changes from Task 2.4
2. Update TypeScript interfaces in `types/`
3. Modify DataGrid pagination handlers
4. Update filtering/sorting request parameters
5. Test with new backend

### Success Criteria
- Frontend works with database backend
- No regression in UI functionality
- Pagination, filtering, sorting functional
- Error messages displayed correctly

---

# PHASE 3: Statistical Analysis Features (Weeks 8-10)
**Complexity: Medium | Impact: High | Risk: Low**

Add statistical analysis capabilities to frontend and backend.

---

## Task 3.1: Backend Statistical Analysis API
**Complexity**:  (Medium)
**Estimated Time**: 5 days
**Dependencies**: Task 2.4 (Database routes)

### Description
Create API endpoints for statistical analysis operations.

### Deliverables
- [ ] Descriptive statistics endpoint
- [ ] Correlation analysis endpoint
- [ ] Distribution analysis endpoint
- [ ] Data quality report endpoint

### Implementation Steps
1. Install scipy, scikit-learn for statistical functions
2. Create `src/routes/workspace_stats_route.py`
3. Implement endpoints:
   - `GET /api/v1/workspace/stats/descriptive/<file_id>`
   - `GET /api/v1/workspace/stats/correlation/<file_id>`
   - `GET /api/v1/workspace/stats/distribution/<file_id>/<column>`
   - `GET /api/v1/workspace/stats/quality/<file_id>`
4. Implement statistical functions in `src/data/statistics.py`
5. Add caching for expensive calculations

### Statistical Functions
```python
def calculate_descriptive_stats(file_id: int, column: str) -> dict:
    """Calculate mean, median, std, min, max, quartiles"""
    variants = query_numeric_column(file_id, column)
    return {
        'mean': np.mean(variants),
        'median': np.median(variants),
        'std': np.std(variants),
        'min': np.min(variants),
        'max': np.max(variants),
        'q1': np.percentile(variants, 25),
        'q3': np.percentile(variants, 75),
    }

def calculate_correlation_matrix(file_id: int, columns: List[str]) -> dict:
    """Calculate Pearson correlation between numeric columns"""
    df = query_multiple_columns(file_id, columns)
    corr_matrix = df.corr()
    return corr_matrix.to_dict()

def calculate_distribution(file_id: int, column: str, bins: int = 20) -> dict:
    """Calculate histogram for column"""
    values = query_numeric_column(file_id, column)
    hist, bin_edges = np.histogram(values, bins=bins)
    return {'counts': hist.tolist(), 'bin_edges': bin_edges.tolist()}
```

### Success Criteria
- All statistical endpoints functional
- Results cached for repeated queries
- API responses include metadata
- Tests for statistical functions

---

## Task 3.2: Frontend Statistical Visualization Components
**Complexity**:  (Medium)
**Estimated Time**: 7 days
**Dependencies**: Task 3.1

### Description
Create React components for visualizing statistical analysis.

### Deliverables
- [ ] Chart library integration (Recharts or Chart.js)
- [ ] Histogram component
- [ ] Box plot component
- [ ] Scatter plot component
- [ ] Correlation heatmap component
- [ ] Statistics dashboard

### Implementation Steps
1. Install `recharts` for React
2. Create `features/editor/components/statisticsView/`
3. Implement chart components:
   - `HistogramChart.tsx` - Distribution visualization
   - `BoxPlotChart.tsx` - Quartile visualization
   - `ScatterPlot.tsx` - Correlation visualization
   - `HeatmapChart.tsx` - Correlation matrix
4. Create statistics toolbar group
5. Add "View Statistics" button to DataGrid toolbar
6. Implement statistics modal dialog
7. Fetch statistics from API endpoints
8. Cache statistics in WorkspaceContext

### Component Structure
```typescript
interface HistogramChartProps {
  data: { counts: number[]; bin_edges: number[] };
  title: string;
  xLabel: string;
  yLabel: string;
}

const HistogramChart: React.FC<HistogramChartProps> = ({ data, title, xLabel, yLabel }) => {
  const chartData = data.counts.map((count, i) => ({
    binStart: data.bin_edges[i],
    count: count,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="binStart" label={{ value: xLabel, position: 'insideBottom', offset: -5 }} />
        <YAxis label={{ value: yLabel, angle: -90, position: 'insideLeft' }} />
        <Tooltip />
        <Bar dataKey="count" fill="#8884d8" />
      </BarChart>
    </ResponsiveContainer>
  );
};
```

### Success Criteria
- Statistics dialog displays charts
- Charts update when column selection changes
- Responsive design for charts
- Loading states during API calls

---

## Task 3.3: Data Export Enhancements
**Complexity**:  (Simple)
**Estimated Time**: 3 days
**Dependencies**: Task 3.1

### Description
Add export options for statistical analysis results.

### Deliverables
- [ ] Export statistics to JSON
- [ ] Export statistics to CSV
- [ ] Export charts as PNG/SVG
- [ ] Batch export functionality

### Implementation Steps
1. Add export buttons to statistics dialog
2. Implement JSON export (direct download)
3. Implement CSV export for tabular stats
4. Use html2canvas for chart image export
5. Create ZIP archive for batch exports

### Success Criteria
- Statistics exportable in multiple formats
- Charts downloadable as images
- Export preserves data precision
- Batch export creates organized ZIP file

---

# PHASE 4: Advanced Tool Integration (Weeks 11-15)
**Complexity: High | Impact: High | Risk: Medium**

Modernize backend API and add new DNA analysis tools.

---

## Task 4.1: Tool Integration Framework
**Complexity**:  (Complex)
**Estimated Time**: 7 days
**Dependencies**: Task 2.4 (Database routes)

### Description
Create standardized framework for integrating DNA analysis tools.

### Deliverables
- [ ] Abstract base class for tools
- [ ] Tool registry system
- [ ] Async task queue (Celery)
- [ ] Tool result caching
- [ ] Tool versioning support

### Implementation Steps
1. Install Celery, Redis (task queue)
2. Create `src/tools/base.py` with abstract base class
3. Implement tool registry in `src/tools/registry.py`
4. Configure Celery for background tasks
5. Refactor existing tools (SpliceAI, CADD, REVEL) to use framework
6. Add tool metadata (version, parameters, description)

### Tool Framework Design
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseTool(ABC):
    """Abstract base class for all DNA analysis tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Tool version"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass

    @abstractmethod
    def validate_input(self, variants: List[Dict]) -> bool:
        """Validate input variants"""
        pass

    @abstractmethod
    async def run(self, variants: List[Dict], params: Dict[str, Any]) -> List[Dict]:
        """Execute tool analysis"""
        pass

    @abstractmethod
    def parse_output(self, raw_output: Any) -> List[Dict]:
        """Parse tool output to standard format"""
        pass

class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {'name': tool.name, 'version': tool.version, 'description': tool.description}
            for tool in self._tools.values()
        ]

# Global registry
tool_registry = ToolRegistry()

# Example refactored SpliceAI
class SpliceAITool(BaseTool):
    name = "SpliceAI"
    version = "1.3.1"
    description = "Predicts splice site effects of genetic variants"

    def validate_input(self, variants: List[Dict]) -> bool:
        # Check required fields
        required_fields = ['chromosome', 'position', 'ref', 'alt']
        return all(field in variants[0] for field in required_fields)

    async def run(self, variants: List[Dict], params: Dict[str, Any]) -> List[Dict]:
        # Generate VCF, run SpliceAI, parse results
        vcf_file = self._generate_vcf(variants)
        output = await self._execute_spliceai(vcf_file, params)
        return self.parse_output(output)

    def parse_output(self, raw_output: Any) -> List[Dict]:
        # Parse SpliceAI VCF output
        return parse_spliceai_vcf(raw_output)

# Register tool
tool_registry.register(SpliceAITool())
```

### Celery Task Example
```python
from celery import Celery

celery = Celery('kath', broker='redis://localhost:6379/0')

@celery.task
def run_tool_analysis(tool_name: str, file_id: int, params: Dict[str, Any]):
    """Background task for tool analysis"""
    tool = tool_registry.get(tool_name)

    # Fetch variants from database
    variants = fetch_variants_for_file(file_id)

    # Run tool
    results = await tool.run(variants, params)

    # Store results in database
    store_annotations(file_id, tool_name, results)

    # Emit WebSocket event
    emit_tool_complete_event(file_id, tool_name)
```

### Success Criteria
- All existing tools refactored to use framework
- New tools can be added with minimal code
- Tool execution runs asynchronously
- Tool metadata accessible via API

---

## Task 4.2: Add New DNA Analysis Tools
**Complexity**:  (Medium)
**Estimated Time**: 10 days
**Dependencies**: Task 4.1

### Description
Integrate additional DNA analysis tools using the new framework.

### Deliverables
- [ ] VEP (Variant Effect Predictor) integration
- [ ] PolyPhen-2 integration
- [ ] SIFT integration
- [ ] AlphaMissense integration
- [ ] gnomAD frequency lookup
- [ ] Tool comparison view

### Recommended Tools

**1. VEP (Variant Effect Predictor)**
- Source: Ensembl
- Function: Comprehensive variant annotation
- Integration: REST API or local installation
- Output: Transcript consequences, SIFT, PolyPhen scores

**2. PolyPhen-2**
- Source: Harvard
- Function: Pathogenicity prediction
- Integration: REST API
- Output: Benign/Possibly damaging/Probably damaging

**3. SIFT (Sorting Intolerant From Tolerant)**
- Source: J. Craig Venter Institute
- Function: Amino acid substitution prediction
- Integration: REST API or local database
- Output: Tolerated/Deleterious score

**4. AlphaMissense**
- Source: DeepMind/Google
- Function: Missense variant pathogenicity prediction
- Integration: Pre-computed database lookup
- Output: Pathogenicity score (0-1)

**5. gnomAD Frequency**
- Source: Broad Institute
- Function: Population allele frequency
- Integration: REST API
- Output: Allele frequency, population-specific frequencies

### Implementation Steps
1. Create tool classes for each:
   - `src/tools/vep.py`
   - `src/tools/polyphen.py`
   - `src/tools/sift.py`
   - `src/tools/alphamissense.py`
   - `src/tools/gnomad.py`
2. Implement BaseTool interface
3. Register tools in registry
4. Add API endpoints for each tool
5. Update frontend toolbar with tool buttons
6. Create tool result comparison view

### Tool Comparison View
```python
@workspace_route_bp.route('/workspace/tools/compare/<int:file_id>', methods=['GET'])
def compare_tools(file_id):
    """Compare results from multiple tools"""
    tools = request.args.getlist('tools')  # ['SpliceAI', 'CADD', 'REVEL']

    results = {}
    for tool_name in tools:
        annotations = fetch_annotations(file_id, tool_name)
        results[tool_name] = annotations

    # Merge results by variant
    comparison = merge_tool_results(results)

    return jsonify(comparison)
```

### Success Criteria
- At least 3 new tools integrated
- All tools accessible via API
- Tool results stored in database
- Frontend displays tool comparison

---

## Task 4.3: RESTful API Modernization
**Complexity**:  (Complex)
**Estimated Time**: 8 days
**Dependencies**: Task 4.1

### Description
Modernize API to follow REST best practices and add versioning.

### Deliverables
- [ ] RESTful resource endpoints
- [ ] API versioning (v1, v2)
- [ ] JSON:API or HAL standard
- [ ] Rate limiting
- [ ] API authentication (JWT)
- [ ] Pagination headers (Link, X-Total-Count)

### Implementation Steps
1. Install Flask-RESTX or Flask-RESTful
2. Design RESTful resource endpoints:
   ```
   GET    /api/v2/workspaces
   POST   /api/v2/workspaces
   GET    /api/v2/workspaces/{id}
   PATCH  /api/v2/workspaces/{id}
   DELETE /api/v2/workspaces/{id}

   GET    /api/v2/workspaces/{id}/files
   POST   /api/v2/workspaces/{id}/files
   GET    /api/v2/files/{id}
   PATCH  /api/v2/files/{id}
   DELETE /api/v2/files/{id}

   GET    /api/v2/files/{id}/variants
   GET    /api/v2/variants/{id}

   POST   /api/v2/files/{id}/analyze
   GET    /api/v2/files/{id}/annotations
   ```
3. Implement resource classes with proper HTTP verbs
4. Add pagination with Link headers
5. Implement JWT authentication
6. Add rate limiting with Flask-Limiter
7. Keep v1 API for backward compatibility

### RESTful Resource Example
```python
from flask_restx import Resource, Namespace, fields

api = Namespace('files', description='File operations')

file_model = api.model('File', {
    'id': fields.Integer(readonly=True),
    'workspace_id': fields.String(required=True),
    'name': fields.String(required=True),
    'path': fields.String(required=True),
    'file_type': fields.String(required=True),
    'row_count': fields.Integer(readonly=True),
})

@api.route('/<int:file_id>')
class FileResource(Resource):
    @api.doc('get_file')
    @api.marshal_with(file_model)
    def get(self, file_id):
        """Fetch a file by ID"""
        file = FileRepository.find_by_id(file_id)
        if not file:
            api.abort(404, f"File {file_id} not found")
        return file

    @api.doc('update_file')
    @api.expect(file_model)
    @api.marshal_with(file_model)
    def patch(self, file_id):
        """Update a file"""
        file = FileRepository.find_by_id(file_id)
        if not file:
            api.abort(404, f"File {file_id} not found")

        data = request.json
        FileRepository.update(file_id, data)
        return FileRepository.find_by_id(file_id)

    @api.doc('delete_file')
    @api.response(204, 'File deleted')
    def delete(self, file_id):
        """Delete a file"""
        FileRepository.delete(file_id)
        return '', 204
```

### Success Criteria
- API follows REST conventions
- Proper HTTP status codes
- Versioned endpoints (v1, v2)
- API documentation auto-generated
- JWT authentication working

---

## Task 4.4: Asynchronous Task Processing
**Complexity**:  (Complex)
**Estimated Time**: 6 days
**Dependencies**: Task 4.1 (Tool framework with Celery)

### Description
Implement background task processing for long-running analyses.

### Deliverables
- [ ] Celery worker configuration
- [ ] Task progress tracking
- [ ] Task result storage
- [ ] Task cancellation support
- [ ] Frontend task monitor

### Implementation Steps
1. Configure Celery with Redis backend
2. Create task definitions in `src/tasks/`
3. Implement progress tracking with Celery signals
4. Store task results in database
5. Add WebSocket events for task updates
6. Create frontend task monitor component
7. Add task cancellation endpoint

### Task Progress Tracking
```python
from celery import Task
from celery.signals import task_prerun, task_postrun

class ProgressTask(Task):
    """Base task with progress tracking"""

    def __call__(self, *args, **kwargs):
        # Emit start event
        emit_task_start(self.request.id)

        try:
            result = super().__call__(*args, **kwargs)
            emit_task_success(self.request.id, result)
            return result
        except Exception as e:
            emit_task_failure(self.request.id, str(e))
            raise

@celery.task(base=ProgressTask, bind=True)
def analyze_file_with_tool(self, file_id: int, tool_name: str, params: dict):
    """Long-running analysis task"""
    tool = tool_registry.get(tool_name)
    variants = fetch_variants(file_id)

    total_variants = len(variants)
    results = []

    for i, variant in enumerate(variants):
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': total_variants}
        )

        # Run tool on variant
        result = tool.analyze_variant(variant, params)
        results.append(result)

    # Store results
    store_annotations(file_id, tool_name, results)

    return {'file_id': file_id, 'tool': tool_name, 'variants_analyzed': total_variants}
```

### Frontend Task Monitor
```typescript
interface TaskStatus {
  task_id: string;
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  current?: number;
  total?: number;
  result?: any;
  error?: string;
}

const TaskMonitor: React.FC = () => {
  const [tasks, setTasks] = useState<TaskStatus[]>([]);

  useEffect(() => {
    socket.on('task_update', (taskStatus: TaskStatus) => {
      setTasks(prev => {
        const index = prev.findIndex(t => t.task_id === taskStatus.task_id);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = taskStatus;
          return updated;
        }
        return [...prev, taskStatus];
      });
    });
  }, []);

  return (
    <Box>
      {tasks.map(task => (
        <TaskProgressBar key={task.task_id} task={task} />
      ))}
    </Box>
  );
};
```

### Success Criteria
- Long-running tasks execute in background
- Progress updates visible in UI
- Tasks can be cancelled
- Task history stored in database
- No UI blocking during analysis

---

# PHASE 5: Advanced Features & Optimization (Weeks 16-20)
**Complexity: Very High | Impact: Medium-High | Risk: Low**

Polish application with advanced features and performance optimizations.

---

## Task 5.1: Data Caching Layer
**Complexity**:  (Medium)
**Estimated Time**: 5 days
**Dependencies**: Task 2.4 (Database routes)

### Description
Implement caching for frequently accessed data.

### Deliverables
- [ ] Redis caching for API responses
- [ ] Database query result caching
- [ ] Cache invalidation strategies
- [ ] Cache hit rate monitoring

### Implementation Steps
1. Install Flask-Caching
2. Configure Redis cache backend
3. Add caching decorators to routes
4. Implement cache invalidation on data updates
5. Add cache statistics endpoint
6. Monitor cache performance

### Caching Strategy
```python
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/1'})

@workspace_route_bp.route('/workspace/file/<int:file_id>', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes
def get_file(file_id):
    # Expensive database query
    variants = VariantRepository.find_by_file(file_id)
    return jsonify(variants)

def invalidate_file_cache(file_id: int):
    """Invalidate cache when file is updated"""
    cache.delete(f'/workspace/file/{file_id}*')
```

### Success Criteria
- Cache hit rate > 70% for common queries
- API response times reduced by 50%
- Cache invalidation prevents stale data
- Cache statistics visible in logs

---

## Task 5.2: Batch Operations & Bulk Processing
**Complexity**:  (Complex)
**Estimated Time**: 7 days
**Dependencies**: Task 4.4 (Async tasks)

### Description
Add support for batch operations on multiple files.

### Deliverables
- [ ] Batch file import
- [ ] Batch tool analysis
- [ ] Batch export
- [ ] Batch delete with confirmation

### Implementation Steps
1. Add batch endpoints:
   - `POST /api/v2/files/batch/import`
   - `POST /api/v2/files/batch/analyze`
   - `POST /api/v2/files/batch/export`
   - `DELETE /api/v2/files/batch/delete`
2. Implement Celery task chains for batch operations
3. Add progress tracking for batch jobs
4. Create frontend batch selection UI
5. Implement batch confirmation dialog

### Batch Analysis Example
```python
from celery import group, chord

@celery.task
def batch_analyze_files(file_ids: List[int], tool_name: str, params: dict):
    """Batch analyze multiple files"""

    # Create task group
    job = group([
        analyze_file_with_tool.s(file_id, tool_name, params)
        for file_id in file_ids
    ])

    # Execute with callback
    callback = batch_analysis_complete.s()
    result = chord(job)(callback)

    return {'batch_id': result.id, 'files': file_ids}

@celery.task
def batch_analysis_complete(results):
    """Called when batch completes"""
    emit_batch_complete_event(results)
```

### Success Criteria
- Users can select multiple files for operations
- Batch operations execute efficiently
- Progress visible for each file
- Batch operations can be cancelled

---

## Task 5.3: Advanced Filtering & Search
**Complexity**:  (Medium)
**Estimated Time**: 6 days
**Dependencies**: Task 2.4 (Database routes)

### Description
Implement advanced search and filtering capabilities.

### Deliverables
- [ ] Full-text search with SQLite FTS5
- [ ] Multi-column filtering
- [ ] Saved filter presets
- [ ] Filter builder UI component

### Implementation Steps
1. Enable SQLite FTS5 extension
2. Create full-text search indexes on variant columns
3. Implement search endpoint with ranking
4. Add filter persistence to database
5. Create filter builder React component
6. Add quick filters (pathogenic, benign, etc.)

### Full-Text Search
```sql
-- Create FTS5 virtual table
CREATE VIRTUAL TABLE variants_fts USING fts5(
    gene, transcript, consequence, variant_id, content=variants
);

-- Populate FTS table
INSERT INTO variants_fts(rowid, gene, transcript, consequence, variant_id)
SELECT id, gene, transcript, consequence, variant_id FROM variants;

-- Search query
SELECT v.* FROM variants v
JOIN variants_fts fts ON v.id = fts.rowid
WHERE variants_fts MATCH 'BRCA1 OR BRCA2'
ORDER BY rank;
```

### Filter Builder UI
```typescript
interface Filter {
  column: string;
  operator: 'equals' | 'contains' | 'gt' | 'lt' | 'in';
  value: any;
}

const FilterBuilder: React.FC = () => {
  const [filters, setFilters] = useState<Filter[]>([]);

  const addFilter = () => {
    setFilters([...filters, { column: '', operator: 'equals', value: '' }]);
  };

  const applyFilters = () => {
    // Send filters to API
    fetchFilteredVariants(filters);
  };

  return (
    <Box>
      {filters.map((filter, i) => (
        <FilterRow key={i} filter={filter} onChange={(updated) => updateFilter(i, updated)} />
      ))}
      <Button onClick={addFilter}>Add Filter</Button>
      <Button onClick={applyFilters}>Apply</Button>
    </Box>
  );
};
```

### Success Criteria
- Full-text search returns ranked results
- Multi-column filters work together (AND/OR)
- Filter presets can be saved/loaded
- Search response time < 1 second

---

## Task 5.4: Data Visualization Dashboard
**Complexity**:  (Complex)
**Estimated Time**: 10 days
**Dependencies**: Task 3.2 (Statistical visualization)

### Description
Create comprehensive dashboard for data visualization.

### Deliverables
- [ ] Dashboard page with multiple chart types
- [ ] Customizable widget layout
- [ ] Export dashboard as PDF/PNG
- [ ] Dashboard templates
- [ ] Real-time data updates

### Implementation Steps
1. Install react-grid-layout for widget positioning
2. Create dashboard route in frontend
3. Implement chart widgets:
   - Variant distribution by chromosome
   - Pathogenicity score distribution
   - Tool result comparison
   - Gene frequency chart
   - Quality metrics over time
4. Add widget configuration panel
5. Implement dashboard save/load
6. Add PDF export with jsPDF

### Dashboard Layout
```typescript
import GridLayout from 'react-grid-layout';

interface DashboardWidget {
  id: string;
  type: 'histogram' | 'scatter' | 'heatmap' | 'pie';
  config: any;
  layout: { x: number; y: number; w: number; h: number };
}

const Dashboard: React.FC = () => {
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);

  const layout = widgets.map(w => ({ i: w.id, ...w.layout }));

  return (
    <GridLayout
      className="layout"
      layout={layout}
      cols={12}
      rowHeight={30}
      width={1200}
      onLayoutChange={(newLayout) => updateWidgetLayout(newLayout)}
    >
      {widgets.map(widget => (
        <div key={widget.id}>
          <WidgetRenderer widget={widget} />
        </div>
      ))}
    </GridLayout>
  );
};
```

### Success Criteria
- Dashboard displays multiple charts
- Widgets can be repositioned
- Dashboard saves to database
- PDF export includes all widgets
- Real-time updates via WebSocket

---

## Task 5.5: Performance Optimization
**Complexity**:  (Medium)
**Estimated Time**: 5 days
**Dependencies**: All previous tasks

### Description
Optimize application performance and scalability.

### Deliverables
- [ ] Database query optimization
- [ ] Frontend bundle size reduction
- [ ] API response compression
- [ ] Database indexing improvements
- [ ] Load testing results

### Implementation Steps
1. Profile slow database queries
2. Add missing database indexes
3. Implement database query result streaming
4. Enable gzip compression for API responses
5. Optimize React component rendering (React.memo, useMemo)
6. Code-split frontend bundles
7. Lazy load chart libraries
8. Run load tests with Locust
9. Monitor performance with New Relic or DataDog

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_variants_file_chromosome ON variants(file_id, chromosome);
CREATE INDEX idx_variants_gene ON variants(gene);
CREATE INDEX idx_annotations_variant_tool ON annotations(variant_id, tool_name);

-- Analyze query performance
EXPLAIN QUERY PLAN
SELECT * FROM variants
WHERE file_id = 1 AND chromosome = 'chr1'
ORDER BY position
LIMIT 25;
```

### Frontend Optimization
```typescript
// Code splitting
const StatisticsView = lazy(() => import('./components/statisticsView'));
const DashboardView = lazy(() => import('./components/dashboardView'));

// Memoization
const VariantRow = React.memo(({ variant }) => {
  return <TableRow>...</TableRow>;
});

// useMemo for expensive calculations
const sortedVariants = useMemo(() => {
  return variants.sort((a, b) => a.position - b.position);
}, [variants]);
```

### Load Testing
```python
from locust import HttpUser, task, between

class KathUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_file(self):
        self.client.get("/api/v2/files/1/variants?page=1&per_page=25")

    @task(1)
    def analyze_file(self):
        self.client.post("/api/v2/files/1/analyze", json={"tool": "SpliceAI"})

# Run: locust -f load_test.py --host=http://localhost:8080
```

### Success Criteria
- Database queries < 100ms (95th percentile)
- Frontend initial load < 3 seconds
- API response times < 200ms (95th percentile)
- Application handles 100 concurrent users
- Frontend bundle size < 1MB (main chunk)

---

## Task 5.6: User Management & Permissions
**Complexity**:  (Complex)
**Estimated Time**: 8 days
**Dependencies**: Task 4.3 (JWT authentication)

### Description
Add multi-user support with role-based access control.

### Deliverables
- [ ] User registration/login
- [ ] Role-based permissions (Admin, Analyst, Viewer)
- [ ] Workspace sharing
- [ ] Audit logging
- [ ] User settings

### Implementation Steps
1. Create users table and authentication system
2. Implement JWT token issuance and refresh
3. Add role-based access control (RBAC)
4. Implement workspace ownership and sharing
5. Add audit log for user actions
6. Create user management UI
7. Implement password reset flow

### User Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst', -- admin, analyst, viewer
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workspace_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    permission TEXT NOT NULL, -- owner, editor, viewer
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE (workspace_id, user_id)
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### RBAC Implementation
```python
from functools import wraps
from flask import request, jsonify
import jwt

def require_role(required_role: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No token provided'}), 401

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                user_role = payload.get('role')

                if user_role != required_role and user_role != 'admin':
                    return jsonify({'error': 'Insufficient permissions'}), 403

                request.current_user = payload
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

        return decorated_function
    return decorator

@workspace_route_bp.route('/workspaces', methods=['POST'])
@require_role('analyst')
def create_workspace():
    # Only analysts and admins can create workspaces
    user_id = request.current_user['id']
    workspace = create_new_workspace(user_id)
    return jsonify(workspace), 201
```

### Success Criteria
- Users can register and login
- JWT tokens issued and validated
- Permissions enforced on all endpoints
- Workspace sharing functional
- Audit log tracks all user actions

---

## Task 5.7: Documentation & Knowledge Base
**Complexity**:  (Simple)
**Estimated Time**: 4 days
**Dependencies**: All previous tasks

### Description
Create comprehensive documentation for users and developers.

### Deliverables
- [ ] User guide with screenshots
- [ ] API reference documentation
- [ ] Developer setup guide
- [ ] Tutorial videos
- [ ] FAQ section
- [ ] Tool comparison guide

### Implementation Steps
1. Create `/docs` directory with Markdown files
2. Set up MkDocs or Docusaurus for documentation site
3. Write user guide with step-by-step tutorials
4. Document all API endpoints with examples
5. Create architecture diagrams
6. Record tutorial videos with screen capture
7. Build FAQ from common issues
8. Deploy documentation to GitHub Pages

### Documentation Structure
```
/docs
 index.md                    # Documentation home
 user-guide/
    getting-started.md
    importing-data.md
    running-analyses.md
    viewing-results.md
    statistical-analysis.md
    exporting-data.md
 api-reference/
    authentication.md
    workspaces.md
    files.md
    variants.md
    tools.md
    statistics.md
 developer-guide/
    setup.md
    architecture.md
    adding-tools.md
    testing.md
    deployment.md
 tutorials/
    analyzing-brca-variants.md
    comparing-tool-results.md
    creating-dashboards.md
 faq.md
```

### Success Criteria
- Documentation site deployed
- All features documented with examples
- Tutorial videos recorded (5-10 minutes each)
- FAQ covers 80% of common questions
- API examples tested and working

---

## Task 5.8: Deployment & DevOps
**Complexity**:  (Complex)
**Estimated Time**: 7 days
**Dependencies**: Task 5.5 (Performance optimization)

### Description
Set up production deployment infrastructure.

### Deliverables
- [ ] Docker Compose for production
- [ ] Nginx reverse proxy configuration
- [ ] SSL/TLS certificates (Let's Encrypt)
- [ ] Database backup automation
- [ ] Monitoring and alerting (Prometheus/Grafana)
- [ ] CI/CD pipeline

### Implementation Steps
1. Create production `docker-compose.yml`
2. Configure Nginx as reverse proxy
3. Set up SSL with certbot
4. Implement database backup script (daily)
5. Configure Prometheus for metrics
6. Set up Grafana dashboards
7. Create GitHub Actions workflow for deployment
8. Write deployment documentation

### Production Docker Compose
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  backend:
    build:
      context: ./app/back_end
      dockerfile: Dockerfile.production
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///data/kath.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
      - celery

  celery:
    build:
      context: ./app/back_end
      dockerfile: Dockerfile.production
    command: celery -A src.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///data/kath.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
    depends_on:
      - redis

  frontend:
    build:
      context: ./app/front_end
      dockerfile: Dockerfile.production
    environment:
      - VITE_API_URL=https://yourdomain.com/api/v2
      - VITE_SOCKET_URL=https://yourdomain.com

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

### GitHub Actions CI/CD
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          cd app/back_end
          pip install -r requirements_dev.txt
          pytest
      - name: Run frontend tests
        run: |
          cd app/front_end
          npm install
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/kath
            git pull origin main
            docker-compose down
            docker-compose up -d --build
```

### Success Criteria
- Production deployment automated
- SSL certificates auto-renew
- Database backups run daily
- Monitoring dashboards functional
- Zero-downtime deployments possible

---

# Implementation Timeline

## Gantt Chart Overview

| Phase | Week | Tasks | Status |
|-------|------|-------|--------|
| **Phase 1** | 1-3 | Tasks 1.1-1.6 | Not Started |
| **Phase 2** | 4-7 | Tasks 2.1-2.5 | Not Started |
| **Phase 3** | 8-10 | Tasks 3.1-3.3 | Not Started |
| **Phase 4** | 11-15 | Tasks 4.1-4.4 | Not Started |
| **Phase 5** | 16-20 | Tasks 5.1-5.8 | Not Started |

## Detailed Timeline

### Weeks 1-3: Foundation (Phase 1)
- Week 1: Documentation, logging, configuration
- Week 2: Testing infrastructure, code quality tools
- Week 3: Frontend responsive design

### Weeks 4-7: Database Migration (Phase 2)
- Week 4: Schema design and database layer
- Week 5: Migration tool development
- Week 6-7: Route refactoring and frontend updates

### Weeks 8-10: Statistical Analysis (Phase 3)
- Week 8: Backend statistics API
- Week 9: Frontend visualization components
- Week 10: Export enhancements

### Weeks 11-15: Tool Integration (Phase 4)
- Week 11-12: Tool framework and new tools
- Week 13: RESTful API modernization
- Week 14-15: Async task processing

### Weeks 16-20: Advanced Features (Phase 5)
- Week 16: Caching and batch operations
- Week 17: Advanced filtering and search
- Week 18-19: Dashboard and optimization
- Week 20: User management and deployment

---

# Risk Assessment & Mitigation

## High-Risk Items

### 1. Database Migration (Task 2.3, 2.4)
**Risk**: Data loss or corruption during CSV to SQLite migration
**Probability**: Medium
**Impact**: Critical
**Mitigation**:
- Create comprehensive backups before migration
- Test migration on template workspace first
- Implement rollback capability
- Validate data integrity post-migration
- Keep CSV files as backup for 30 days

### 2. Backend Route Refactoring (Task 2.4)
**Risk**: API contract changes break frontend
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Maintain API version 1 for backward compatibility
- Implement comprehensive integration tests
- Use feature flags to toggle between CSV and DB backends
- Gradual rollout with monitoring

### 3. Tool Integration Framework (Task 4.1)
**Risk**: Framework complexity slows down development
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Start with simple abstract base class
- Refactor one existing tool first (SpliceAI)
- Gather feedback before refactoring all tools
- Keep legacy tool implementations as fallback

## Medium-Risk Items

### 4. Async Task Processing (Task 4.4)
**Risk**: Celery adds operational complexity
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Thorough Celery documentation review
- Start with simple tasks
- Monitor task queue health
- Implement automatic worker restart

### 5. User Management (Task 5.6)
**Risk**: Security vulnerabilities in authentication
**Probability**: Low
**Impact**: Critical
**Mitigation**:
- Use battle-tested libraries (Flask-JWT-Extended)
- Security audit before release
- Implement rate limiting
- Add 2FA support

---

# Success Metrics

## Key Performance Indicators (KPIs)

### Performance
- [ ] API response time < 200ms (95th percentile)
- [ ] Database query time < 100ms (95th percentile)
- [ ] Frontend initial load < 3 seconds
- [ ] Support 100+ concurrent users

### Code Quality
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] Code review approval for all PRs
- [ ] Documentation coverage 100%

### User Experience
- [ ] Mobile responsive (480px+)
- [ ] < 5 clicks to run analysis
- [ ] Real-time feedback on all operations
- [ ] Dashboard customizable

### Features
- [ ] 5+ DNA analysis tools integrated
- [ ] Statistical analysis functional
- [ ] Batch operations working
- [ ] User management complete

---

# Maintenance & Long-Term Roadmap

## Post-Launch Maintenance (v0.3-alpha+)

### Monthly Tasks
- Security updates for dependencies
- Database backup verification
- Performance monitoring review
- User feedback analysis

### Quarterly Tasks
- Load testing
- Security audit
- Documentation updates
- Feature prioritization

## Future Enhancements (v0.4-alpha and beyond)

### Advanced Analytics
- Machine learning model integration
- Variant classification algorithms
- Population genetics analysis
- Pathway enrichment analysis

### Collaboration Features
- Real-time collaboration (multiple users editing)
- Commenting system for variants
- Annotation sharing across workspaces
- Team workspaces

### Enterprise Features
- LDAP/SSO integration
- Advanced audit logging
- Data governance policies
- Custom branding

### Performance Enhancements
- PostgreSQL migration for larger datasets
- ElasticSearch for advanced search
- GraphQL API option
- Serverless function support

---

# Appendix

## A. Technology Stack Summary

### Current Stack
| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | Flask | 3.0.3 |
| Frontend Framework | React | 18.3.1 |
| Language | Python / TypeScript | 3.12 / 5.6.3 |
| Database | SQLite (post-migration) | 3.x |
| Cache | Redis | 5.0.8 |
| Task Queue | Celery | TBD |
| Build Tool | Vite | 7.1.11 |
| UI Library | Material-UI | 5.16.7 |

### Proposed Additions
| Component | Technology | Purpose |
|-----------|-----------|---------|
| ORM | SQLAlchemy | Database abstraction |
| Migrations | Alembic | Schema versioning |
| Testing | pytest | Unit/integration tests |
| API Docs | Swagger/OpenAPI | API documentation |
| Monitoring | Prometheus + Grafana | Observability |
| Task Queue | Celery + Redis | Background jobs |
| Charts | Recharts | Data visualization |

## B. Glossary

- **VCF**: Variant Call Format - standard format for genetic variants
- **SpliceAI**: Deep learning tool for splice site prediction
- **CADD**: Combined Annotation Dependent Depletion - variant pathogenicity scoring
- **REVEL**: Rare Exome Variant Ensemble Learner - pathogenicity predictor
- **gnomAD**: Genome Aggregation Database - population frequency database
- **CRUD**: Create, Read, Update, Delete operations
- **ORM**: Object-Relational Mapping
- **JWT**: JSON Web Token for authentication
- **RBAC**: Role-Based Access Control

## C. References

### Documentation
- Flask: https://flask.palletsprojects.com/
- React: https://react.dev/
- Material-UI: https://mui.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Celery: https://docs.celeryq.dev/

### Tools
- SpliceAI: https://github.com/Illumina/SpliceAI
- CADD: https://cadd.gs.washington.edu/
- REVEL: https://sites.google.com/site/revelgenomics/
- VEP: https://www.ensembl.org/vep
- gnomAD: https://gnomad.broadinstitute.org/

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Next Review**: Start of each phase

---

# Task Checklist Summary

Use this checklist to track progress:

## Phase 1: Quick Wins (6 tasks)
- [ ] 1.1: Documentation
- [ ] 1.2: Logging
- [ ] 1.3: Unit Tests
- [ ] 1.4: Configuration Refactor
- [ ] 1.5: Responsive Design Phase 1
- [ ] 1.6: Code Quality Tools

## Phase 2: Database Migration (5 tasks)
- [ ] 2.1: Schema Design
- [ ] 2.2: Database Layer
- [ ] 2.3: Migration Tool
- [ ] 2.4: Backend Routes Update
- [ ] 2.5: Frontend Updates

## Phase 3: Statistical Analysis (3 tasks)
- [ ] 3.1: Statistics API
- [ ] 3.2: Visualization Components
- [ ] 3.3: Export Enhancements

## Phase 4: Tool Integration (4 tasks)
- [ ] 4.1: Tool Framework
- [ ] 4.2: New Tools
- [ ] 4.3: RESTful API
- [ ] 4.4: Async Tasks

## Phase 5: Advanced Features (8 tasks)
- [ ] 5.1: Caching
- [ ] 5.2: Batch Operations
- [ ] 5.3: Advanced Filtering
- [ ] 5.4: Dashboard
- [ ] 5.5: Performance Optimization
- [ ] 5.6: User Management
- [ ] 5.7: Documentation
- [ ] 5.8: Deployment

**Total: 26 Tasks over 20 weeks**
