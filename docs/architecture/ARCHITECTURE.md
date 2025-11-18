# KATH Architecture Overview

**Version:** 0.2-alpha
**Last Updated:** 2025-10-27

## Table of Contents

- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Data Flow](#data-flow)
- [Security Model](#security-model)
- [Deployment Architecture](#deployment-architecture)
- [Future Architecture (v0.3+)](#future-architecture)

---

## System Overview

KATH is a web-based genetic analysis platform designed for analyzing gene variation data from LOVD, GNOMAD, and CLINVAR databases. The system provides:

- **File-based data management** (CSV/TXT files)
- **DNA analysis tool integration** (SpliceAI, CADD, REVEL)
- **Real-time feedback** via WebSocket
- **Interactive data grid** with filtering and sorting
- **Data merging and aggregation** capabilities

### High-Level Architecture

```

                         User Browser                        
    
    React Frontend (Port 5173)                             
    - Material-UI Components                               
    - Context-based State Management                       
    - Axios (HTTP) + Socket.IO (WebSocket)                
    

                              
                               HTTP/WebSocket
                              

                   Flask Backend (Port 8080)                 
    
    Flask Application                                       
    - REST API Endpoints (/api/v1)                         
    - Socket.IO Event Handlers                             
    - Gunicorn + Gevent Workers                            
    
                                                            
                  
                                                          
                                                          
                  
     Tools              Data             Redis        
    SpliceAI          Processor         Session       
     CADD             pandas            Manager       
     REVEL             CSV I/O                        
                  

                              
                              

                    Filesystem Storage                       
  - User workspaces (UUID-based directories)                 
  - CSV data files with pagination support                   
  - Reference files (FASTA, REVEL database)                  

```

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Flask | 3.0.3 | HTTP server and routing |
| **Real-time** | Flask-SocketIO | 5.3.6 | WebSocket communication |
| **Async Runtime** | Gevent | 24.2.1 | Asynchronous I/O |
| **Server** | Gunicorn | 23.0.0 | WSGI HTTP server |
| **Data Processing** | Pandas | 2.2.3 | CSV manipulation |
| **Deep Learning** | TensorFlow | 2.19.0 | SpliceAI predictions |
| **Web Automation** | Selenium | 4.25.0 | CADD integration |
| **Session Store** | Redis | 5.0.8 | WebSocket session tracking |
| **Database** | SQLite | 3.x | REVEL scores (local) |
| **Language** | Python | 3.12+ | Backend runtime |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18.3.1 | UI components |
| **Language** | TypeScript | 5.6.3 | Type safety |
| **Build Tool** | Vite | 7.1.11 | Dev server & bundler |
| **UI Library** | Material-UI | 5.16.7 | Component library |
| **Data Grid** | MUI X DataGrid | 7.12.1 | Tabular data display |
| **Tree View** | MUI X TreeView | 7.19.0 | File browser |
| **HTTP Client** | Axios | 1.7.7 | REST API calls |
| **WebSocket** | Socket.IO Client | 4.8.0 | Real-time updates |
| **Router** | React Router | 6.26.2 | Client-side routing |
| **Animation** | React Spring | 9.7.5 | UI transitions |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker | Application packaging |
| **Base Image** | Ubuntu 24.04 (CUDA) | Container OS |
| **Redis** | Redis 7.x | Session management |
| **Web Server** | Nginx (future) | Reverse proxy |

---

## Backend Architecture

### Directory Structure

```
app/back_end/
 src/
    __init__.py              # App factory (create_app)
    config.py                # Environment configuration
    constants.py             # API routes and constants
   
    routes/                  # API endpoint blueprints
       workspace_route.py           # File CRUD operations
       workspace_apply_route.py     # Tool applications
       workspace_merge_route.py     # Data merging
       workspace_aggregate_route.py # Aggregations
       workspace_download_route.py  # External data downloads
       workspace_import_route.py    # File imports
       workspace_export_route.py    # File exports
   
    tools/                   # DNA analysis integrations
       spliceai.py         # SpliceAI wrapper
       cadd.py             # CADD API client
       revel.py            # REVEL database queries
   
    data/                    # Data processing modules
       downloading.py      # External data fetching
       refactoring.py      # Data transformation
       helpers.py          # Data utilities
   
    utils/                   # Shared utilities
       exceptions.py       # Custom exceptions
       helpers.py          # General helpers
       logger.py           # Logging configuration
       socket_manager.py   # WebSocket session tracking
   
    setup/                   # App initialization
       extensions.py       # Flask extensions setup
       router.py           # Blueprint registration
       eventer.py          # Socket.IO event handlers
   
    workspace/               # User workspaces
        template/            # Template workspace files

 run.py                       # Application entry point
 gunicorn_config.py          # Gunicorn configuration
 requirements.txt            # Python dependencies
 .env.development            # Environment variables
```

### Request Flow

```
1. HTTP Request (Client)
   
    Flask Router
      
       Blueprint Route Handler
         
          Validate Headers (UUID, SID)
         
          Emit Socket.IO "console_feedback" (start)
         
          Business Logic
             File I/O (pandas)
             Tool Execution (SpliceAI, CADD, REVEL)
             Data Processing
         
          Emit Socket.IO "console_feedback" (success/error)
         
          Return JSON Response
      
       Error Handler
           Return Error JSON + HTTP Status
   
    Response (Client)
```

### API Endpoints

All endpoints are prefixed with `/api/v1`:

#### Workspace Management

- `GET /workspace` - Get file tree structure
- `GET /workspace/file/<path>` - Get file content with pagination
- `PUT /workspace/file/<path>` - Save file content
- `PUT /workspace/create[/<path>]` - Create file/directory
- `PUT /workspace/rename/<path>` - Rename file/directory
- `PUT /workspace/delete/<path>` - Delete file/directory

#### Data Operations

- `POST /workspace/import[/<path>]` - Import CSV/TXT files
- `GET /workspace/export/<path>` - Export/download files
- `GET /workspace/merge/{type}/<path>` - Merge datasets
- `GET /workspace/aggregate/<path>` - Calculate aggregations
- `GET /workspace/download/<path>` - Download from external DBs

#### Tool Applications

- `GET /workspace/apply/spliceai/<path>` - Run SpliceAI
- `GET /workspace/apply/cadd/<path>` - Run CADD
- `GET /workspace/apply/revel/<path>` - Run REVEL

### Session Management

```python
# Redis-based WebSocket session tracking
socket_id_map:{uuid}  Set of session IDs

# On connect:
redis.sadd(f"socket_id_map:{uuid}", socket.id)

# On disconnect:
redis.srem(f"socket_id_map:{uuid}", socket.id)

# Emit to user:
sids = redis.smembers(f"socket_id_map:{uuid}")
for sid in sids:
    socketio.emit('event', data, room=sid)
```

### Data Storage (Current)

**Workspace Structure:**

```
workspace/{uuid}/
 file1.csv
 folder1/
    file2.csv
    file3.txt
 results/
     analysis.csv
```

**CSV File Format:**

- First row: column headers
- Subsequent rows: data
- Pagination: read chunks with pandas
- Filtering: temporary `.index` files

**Reference Data:**

- `workspace/fasta/hg38.fa` - Genome reference (SpliceAI)
- `workspace/revel/revel_with_transcript_ids.db` - REVEL SQLite database

---

## Frontend Architecture

### Directory Structure

```
app/front_end/src/
 app/
    index.tsx               # App root component
    provider.tsx            # Context providers wrapper
    router.tsx              # Route configuration
    routes/                 # Page components
        home.tsx
        notFound.tsx

 features/
    editor/                 # Main editor feature
        index.tsx           # Editor layout
        components/         # Feature components
           fileTreeView/   # File browser
           editorView/     # Data grid
           toolbarView/    # Toolbar with tools
           consoleView/    # Real-time console
           filebarView/    # File tabs
        stores/             # Feature contexts
           workspaceContextProvider.tsx
           toolbarContextProvider.tsx
        hooks/              # Feature hooks
        types/              # Feature types
        utils/              # Feature utilities

 components/                 # Shared components
    dialogs/               # Modal dialogs
       settingsDialog/
       feedbackDialog/
       shortcutsDialog/
    layouts/               # Layout components
       baseLayout.tsx
    sidebar/               # Navigation sidebar

 stores/                     # Global contexts
    sessionContextProvider.tsx    # WebSocket state
    statusContextProvider.tsx     # UI state
    themeContextProvider.tsx      # Theme state

 lib/                        # External library configs
    axios.ts               # HTTP client
    socket.ts              # WebSocket client

 types/                      # Global TypeScript types
    constants/             # API endpoints, events
    enums/                 # Color enums

 utils/                      # Utility functions
```

### Component Hierarchy

```
<App>
 <AppProvider>  (wraps all contexts)
     <SessionContextProvider>  (WebSocket)
     <StatusContextProvider>   (UI state)
     <ThemeContextProvider>    (Theme)
         <AppRouter>
             <BaseLayout>
                 <Header>
                 <Sidebar>
                 <Editor>  (main feature)
                     <WorkspaceContextProvider>
                        <ToolbarContextProvider>
                            <FileTreeView>
                               RichTreeView (MUI)
                            <EditorContent>
                                <ToolbarView>
                                   AutomaticGroup
                                   DownloadGroup
                                   MergeGroup
                                   ApplyGroup
                                <EditorView>
                                   DataGrid (MUI)
                                <FilebarView>
                                <ConsoleView>
```

### State Management

KATH uses **React Context API** for state management (no Redux):

#### Global Contexts

**SessionContext** - WebSocket connection state

```typescript
interface SessionContextProps {
  connected: boolean;  // WebSocket connection status
}
```

**StatusContext** - UI state

```typescript
interface StatusContextProps {
  blocked: boolean;              // UI disabled during operations
  blockedStateUpdate: (b: boolean) => void;
  unsaved: boolean;              // Unsaved changes warning
  unsavedStateUpdate: (b: boolean) => void;
}
```

**ThemeContext** - Light/dark theme

```typescript
interface ThemeContextProps {
  mode: string;         // 'light' | 'dark'
  update: () => void;   // Toggle theme
  values: string[];     // Available modes
}
```

#### Feature Contexts

**WorkspaceContext** - Editor workspace state

```typescript
interface WorkspaceContextProps {
  // Current file
  file: FileModel;
  fileContent: FileContentModel;
  filePagination: FilePaginationModel;
  fileStateUpdate: (file?, content?, pagination?) => void;

  // File history
  filesHistory: FileModel[];
  filesHistoryStateUpdate: (add?, remove?) => void;

  // File tree
  fileTree: TreeViewBaseItem<FileModel>[];
  fileTreeArray: FileModel[];
  fileTreeIsLoading: boolean;

  // Console feedback
  consoleFeedback: ConsoleFeedback[];
  consoleFeedbackStateUpdate: (add) => void;

  // Utilities
  openFileByPath: (path: string) => void;
}
```

### Data Flow Example

**Opening a File:**

```
1. User clicks file in tree
   
2. FileTreeItem.onClick()
   
3. workspaceContext.openFileByPath(filePath)
   
4. workspaceContext.fileStateUpdate({ id, label, type })
   
5. EditorView detects file.id change (useEffect)
   
6. axios.get('/workspace/file/{id}', { page, rowsPerPage })
   
7. Backend processes request
   
8. Response: { columns, rows, pagination }
   
9. fileStateUpdate({ fileContent, filePagination })
   
10. DataGrid re-renders with new data
```

**Real-time Updates:**

```
1. Backend performs operation
   
2. socketio.emit('console_feedback', { message, type })
   
3. Frontend Socket.IO listener receives event
   
4. workspaceContext.consoleFeedbackStateUpdate(message)
   
5. ConsoleView re-renders with new message
```

---

## Data Flow

### Complete Request/Response Cycle

```

  User Action 

       
       

  Frontend Component                      
  - Button click / Form submit            
  - State update (StatusContext.blocked)  

       
       

  Axios HTTP Request                      
  - Headers: { uuid, sid }                
  - Method: GET/POST/PUT/DELETE           
  - Body: JSON payload                    

       
       

  Flask Route Handler                     
  1. Validate headers                     
  2. Emit "console_feedback" (start)      
  3. Execute business logic               
     - Read CSV with pandas               
     - Run DNA analysis tool              
     - Write results                      
  4. Emit "console_feedback" (complete)   
  5. Return JSON response                 

       
       

  Socket.IO Events (parallel)             
  - "console_feedback" events             
  - Received by all client sessions       

       
       

  Frontend Event Handlers                 
  - ConsoleView updates                   
  - WorkspaceContext state updates        

       
       

  UI Updates                              
  - DataGrid refreshes                    
  - Console shows messages                
  - StatusContext.blocked = false         

```

---

## Security Model

### Current Security (v0.2-alpha)

[!] **Note:** Current version is designed for single-user local deployment.

**Authentication:** None (UUID-based session identification)
**Authorization:** None (all users have full access)
**Data Isolation:** UUID-based workspace directories

### Session Identification

```
Client generates UUID (localStorage)
   
UUID sent in HTTP headers
   
Backend tracks sessions in Redis
   
Socket.IO room per UUID
```

### Planned Security (v0.3+)

See [REFACTORING_PLAN.md](../../REFACTORING_PLAN.md#task-56-user-management--permissions) for details:

- **Authentication:** JWT tokens
- **Authorization:** Role-based access control (Admin, Analyst, Viewer)
- **Data Isolation:** Workspace ownership and sharing
- **Audit Logging:** User action tracking
- **Rate Limiting:** API request throttling

---

## Deployment Architecture

### Current Docker Deployment

```

  Docker Container (cpu64/kath:final-amd64-fixed)        
    
    Frontend (Vite dev server) - Port 5173             
    
    
    Backend (Gunicorn + Flask) - Port 8080             
    
    
    Redis Server - Port 6379 (internal)                
    
    
    Workspace Volume Mount                             
    ./data  /kath/app/back_end/src/workspace/...      
    

                    
                    
            Host Machine Ports
            - 5173  Frontend
            - 8080  Backend API
```

### Container Entrypoint

```bash
#!/bin/bash
redis-server --daemonize yes
cd ./back_end && gunicorn -c gunicorn_config.py run:app &
cd ./front_end && npm run dev
```

### Production Architecture (Planned)

```
                    Internet
                       
                       
                  
                    Nginx    (Reverse Proxy, SSL)
                  
                       
       
                                     
                                     
        
 Frontend      Backend        Redis   
 (Static)      (Gunicorn     (Session)
     + Flask)     
                
                       
                       
                
                  Celery    (Background tasks)
                  Workers 
                
                       
                       
                
                 SQLite     (Database)
                 Database 
                
```

---

## Future Architecture (v0.3+)

### Database Layer

Replace CSV storage with SQLite database:

```

  Application Layer                      
  - Routes                               
  - Business Logic                       

               
               

  Repository Layer                       
  - WorkspaceRepository                  
  - FileRepository                       
  - VariantRepository                    
  - AnnotationRepository                 

               
               

  ORM Layer (SQLAlchemy)                 
  - Models                               
  - Relationships                        

               
               

  Database (SQLite)                      
  - workspaces                           
  - files                                
  - variants                             
  - annotations                          
  - aggregations (cached)                

```

### Tool Integration Framework

Standardized tool integration with async execution:

```

  Tool Registry                          
  - SpliceAI                             
  - CADD                                 
  - REVEL                                
  - VEP                                  
  - PolyPhen-2                           
  - AlphaMissense                        

               
               

  BaseTool Interface                     
  - validate_input()                     
  - run()                                
  - parse_output()                       

               
               

  Celery Task Queue                      
  - Background execution                 
  - Progress tracking                    
  - Result caching                       

```

### API Versioning

```
/api/v1  (Current - Maintained for backward compatibility)
   
    /workspace
    /workspace/file
    ...

/api/v2  (Future - RESTful design)
   
    /workspaces
       GET    /workspaces
       POST   /workspaces
       GET    /workspaces/{id}
       PATCH  /workspaces/{id}
       DELETE /workspaces/{id}
   
    /files
       GET    /files/{id}
       PATCH  /files/{id}
       DELETE /files/{id}
   
    /tools
        GET    /tools (list available)
        POST   /files/{id}/analyze
        GET    /files/{id}/annotations
```

---

## Performance Considerations

### Current Bottlenecks

1. **CSV File I/O:** Reading large files with pandas is memory-intensive
2. **No Caching:** Repeated queries reload entire CSV files
3. **Synchronous Tool Execution:** Tools block HTTP request/response
4. **No Query Optimization:** Full table scans for filtering

### Future Optimizations

1. **Database Indexes:** Fast lookups by chromosome, position, gene
2. **Redis Caching:** Cache frequently accessed data
3. **Async Task Queue:** Long-running analyses in background
4. **Query Optimization:** SQL queries with proper indexes
5. **Result Streaming:** Large datasets streamed, not loaded entirely

### Target Performance Metrics (v0.3+)

- API response time: < 200ms (95th percentile)
- Database query time: < 100ms (95th percentile)
- Frontend initial load: < 3 seconds
- Concurrent users: 100+
- File size limit: 1GB+

---

## Monitoring & Observability (Planned)

### Metrics Collection

- **Prometheus:** Application metrics
- **Grafana:** Visualization dashboards
- **Application Metrics:**
  - Request rate
  - Response times
  - Error rates
  - Tool execution times
  - Database query times

### Logging

- **Structured Logging:** JSON-formatted logs
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Aggregation:** Centralized log storage
- **Request IDs:** Distributed tracing

### Health Checks

```python
@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'redis': redis_client.ping(),
        'database': check_database_connection(),
        'version': '0.3.0'
    }
```

---

## Technology Decisions

### Why Flask?

- Lightweight and flexible
- Excellent WebSocket support (Flask-SocketIO)
- Easy integration with scientific libraries (pandas, TensorFlow)
- Rich ecosystem of extensions

### Why React + TypeScript?

- Component-based architecture
- Strong type safety with TypeScript
- Excellent developer experience
- Large ecosystem (MUI, Vite, etc.)

### Why SQLite? (Future)

- Embedded database (no separate server)
- Full SQL support with good performance
- FTS5 for full-text search
- Easy backup (single file)
- Suitable for single-user deployments

### Why Not PostgreSQL?

- Additional infrastructure complexity
- Overkill for single-user local deployment
- May consider for multi-user cloud deployment

### Why Celery? (Future)

- Battle-tested task queue
- Excellent monitoring and debugging tools
- Supports result caching
- Easy integration with Flask

---

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Material-UI](https://mui.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Celery](https://docs.celeryq.dev/)

---

**Next Steps:**

- Review [Refactoring Plan](../../REFACTORING_PLAN.md)
- Set up [Development Environment](../DEVELOPER_SETUP.md)
- Explore [API Reference](../api/API_REFERENCE.md)
