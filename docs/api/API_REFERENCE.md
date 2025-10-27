# KATH API Reference

**Version:** 0.2-alpha
**Base URL:** `http://localhost:8080/api/v1`
**Last Updated:** 2025-10-27

## Table of Contents

- [Authentication](#authentication)
- [Common Headers](#common-headers)
- [Response Format](#response-format)
- [Error Codes](#error-codes)
- [Workspace Endpoints](#workspace-endpoints)
- [File Operations](#file-operations)
- [Data Processing](#data-processing)
- [Tool Applications](#tool-applications)
- [WebSocket Events](#websocket-events)

---

## Authentication

**Current Version:** No authentication required.

**Session Identification:**
- Clients generate a UUID (stored in localStorage)
- UUID sent in `uuid` header with every request
- Session ID (`sid`) sent after WebSocket connection

**Future:** JWT-based authentication (v0.3+)

---

## Common Headers

All API requests must include:

```
uuid: <client-generated-uuid>
sid: <socket-io-session-id>
Content-Type: application/json
```

Example:
```http
GET /api/v1/workspace HTTP/1.1
Host: localhost:8080
uuid: 8d8ac610-566d-4ef0-9c22-186b2a5ed793
sid: abc123xyz
Content-Type: application/json
```

---

## Response Format

### Success Response

```json
{
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response

```json
{
  "error": "Error message",
  "details": "Detailed error description"
}
```

### Pagination Response

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 150,
    "total_pages": 6
  }
}
```

---

## Error Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Missing headers, invalid parameters |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | File or resource not found |
| 500 | Internal Server Error | Server-side error |

---

## Workspace Endpoints

### Get Workspace Structure

Retrieves the file tree structure for the user's workspace.

**Endpoint:** `GET /workspace`

**Headers:**
```
uuid: <uuid>
sid: <sid>
```

**Response:**
```json
{
  "file_tree": [
    {
      "id": "file1.csv",
      "label": "file1.csv",
      "type": "csv",
      "children": null
    },
    {
      "id": "folder1",
      "label": "folder1",
      "type": "folder",
      "children": [
        {
          "id": "folder1/file2.csv",
          "label": "file2.csv",
          "type": "csv",
          "children": null
        }
      ]
    }
  ]
}
```

**Example:**
```javascript
const response = await axios.get('/workspace', {
  headers: { uuid, sid }
});
```

---

## File Operations

### Get File Content

Retrieves file content with pagination, filtering, and sorting support.

**Endpoint:** `GET /workspace/file/<path>`

**Path Parameters:**
- `path` - Relative file path (e.g., `folder1/file.csv`)

**Query Parameters:**
```
page: number (default: 1)
rows_per_page: number (default: 25)
sorts: string (optional, format: "column:asc|desc")
filters: string (optional, format: "column:operator:value")
aggregations: string (optional, format: "column:operation")
```

**Response:**
```json
{
  "columns": [
    { "field": "chromosome", "headerName": "Chromosome", "type": "string" },
    { "field": "position", "headerName": "Position", "type": "number" }
  ],
  "rows": [
    { "id": 0, "chromosome": "chr1", "position": 12345 },
    { "id": 1, "chromosome": "chr1", "position": 67890 }
  ],
  "file_pagination": {
    "page": 1,
    "rows_per_page": 25,
    "total_rows": 100,
    "total_pages": 4
  },
  "aggregations": {
    "position": { "sum": 1234567, "avg": 12345.67, "min": 100, "max": 99999 }
  }
}
```

**Example:**
```javascript
const response = await axios.get('/workspace/file/data.csv', {
  params: {
    page: 1,
    rows_per_page: 50,
    sorts: 'position:asc',
    filters: 'chromosome:equals:chr1',
    aggregations: 'position:sum,avg'
  },
  headers: { uuid, sid }
});
```

**Filter Operators:**
- `equals` - Exact match
- `contains` - Substring match
- `starts_with` - Prefix match
- `ends_with` - Suffix match
- `gt` - Greater than (numeric)
- `lt` - Less than (numeric)
- `gte` - Greater than or equal
- `lte` - Less than or equal

**Aggregation Operations:**
- `sum` - Sum of values
- `avg` - Average
- `min` - Minimum value
- `max` - Maximum value
- `cnt` - Count of values

---

### Save File Content

Saves modified file content.

**Endpoint:** `PUT /workspace/file/<path>`

**Request Body:**
```json
{
  "content": {
    "columns": [ ... ],
    "rows": [ ... ]
  }
}
```

**Response:**
```json
{
  "message": "File saved successfully"
}
```

**Example:**
```javascript
await axios.put('/workspace/file/data.csv', {
  content: {
    columns: fileContent.columns,
    rows: fileContent.rows
  }
}, {
  headers: { uuid, sid }
});
```

---

### Create File or Directory

Creates a new file or directory in the workspace.

**Endpoint:** `PUT /workspace/create[/<path>]`

**Query Parameters:**
```
type: "file" | "folder"
name: string (file/folder name)
```

**Response:**
```json
{
  "message": "File created successfully",
  "path": "folder1/newfile.csv"
}
```

**Example:**
```javascript
// Create folder
await axios.put('/workspace/create', null, {
  params: { type: 'folder', name: 'new_folder' },
  headers: { uuid, sid }
});

// Create file in folder
await axios.put('/workspace/create/new_folder', null, {
  params: { type: 'file', name: 'data.csv' },
  headers: { uuid, sid }
});
```

---

### Rename File or Directory

Renames a file or directory.

**Endpoint:** `PUT /workspace/rename/<path>`

**Query Parameters:**
```
new_name: string (new name)
```

**Response:**
```json
{
  "message": "File renamed successfully",
  "new_path": "folder1/renamed.csv"
}
```

**Example:**
```javascript
await axios.put('/workspace/rename/folder1/old.csv', null, {
  params: { new_name: 'new.csv' },
  headers: { uuid, sid }
});
```

---

### Delete File or Directory

Deletes a file or directory.

**Endpoint:** `PUT /workspace/delete/<path>`

**Response:**
```json
{
  "message": "File deleted successfully"
}
```

**Example:**
```javascript
await axios.put('/workspace/delete/folder1/file.csv', null, {
  headers: { uuid, sid }
});
```

---

## Data Processing

### Import Files

Imports CSV or TXT files into the workspace.

**Endpoint:** `POST /workspace/import[/<path>]`

**Request Body:** `multipart/form-data`

```
files: File[] (multiple files supported)
```

**Response:**
```json
{
  "message": "Files imported successfully",
  "imported": ["file1.csv", "file2.csv"]
}
```

**Example:**
```javascript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);

await axios.post('/workspace/import/target_folder', formData, {
  headers: {
    uuid,
    sid,
    'Content-Type': 'multipart/form-data'
  }
});
```

---

### Export File

Downloads a file from the workspace.

**Endpoint:** `GET /workspace/export/<path>`

**Response:** File download (binary)

**Example:**
```javascript
const response = await axios.get('/workspace/export/data.csv', {
  headers: { uuid, sid },
  responseType: 'blob'
});

const url = window.URL.createObjectURL(new Blob([response.data]));
const link = document.createElement('a');
link.href = url;
link.setAttribute('download', 'data.csv');
link.click();
```

---

### Merge Files

Merges multiple data files using various strategies.

**Endpoint:** `GET /workspace/merge/<type>/<path>`

**Merge Types:**
- `all` - Merge LOVD, ClinVar, and gnomAD data
- `lovd_clinvar` - Merge LOVD and ClinVar
- `gnomad_lovd` - Merge gnomAD and LOVD
- `custom` - Custom file merge

**Query Parameters (for custom merge):**
```
files: string[] (comma-separated file paths)
strategy: "inner" | "outer" | "left" | "right"
on: string (column to merge on)
```

**Response:**
```json
{
  "message": "Files merged successfully",
  "result_path": "merged_results.csv",
  "rows_merged": 1500
}
```

**Example:**
```javascript
// Merge all databases
await axios.get('/workspace/merge/all/results', {
  headers: { uuid, sid }
});

// Custom merge
await axios.get('/workspace/merge/custom/results', {
  params: {
    files: 'file1.csv,file2.csv',
    strategy: 'inner',
    on: 'variant_id'
  },
  headers: { uuid, sid }
});
```

---

### Aggregate Data

Calculates aggregate statistics for specified columns.

**Endpoint:** `GET /workspace/aggregate/<path>`

**Query Parameters:**
```
columns: string[] (comma-separated column names)
operations: string[] (comma-separated operations: sum, avg, min, max, cnt)
```

**Response:**
```json
{
  "aggregations": {
    "position": {
      "sum": 1234567890,
      "avg": 123456.78,
      "min": 1,
      "max": 999999,
      "cnt": 10000
    },
    "score": {
      "avg": 0.75,
      "min": 0.1,
      "max": 1.0
    }
  }
}
```

**Example:**
```javascript
const response = await axios.get('/workspace/aggregate/data.csv', {
  params: {
    columns: 'position,score',
    operations: 'sum,avg,min,max,cnt'
  },
  headers: { uuid, sid }
});
```

---

### Download from External Database

Downloads data from LOVD, ClinVar, or gnomAD databases.

**Endpoint:** `GET /workspace/download/<path>`

**Query Parameters:**
```
source: "lovd" | "clinvar" | "gnomad"
gene: string (gene name)
additional_params: object (source-specific parameters)
```

**Response:**
```json
{
  "message": "Download started",
  "task_id": "abc123",
  "estimated_time": "5 minutes"
}
```

**Example:**
```javascript
await axios.get('/workspace/download/downloads', {
  params: {
    source: 'clinvar',
    gene: 'BRCA1'
  },
  headers: { uuid, sid }
});
```

---

## Tool Applications

### Apply SpliceAI

Runs SpliceAI splice site prediction on variants.

**Endpoint:** `GET /workspace/apply/spliceai/<path>`

**Query Parameters:**
```
distance: number (default: 50, max distance from splice site)
mask: boolean (default: false, mask scores)
```

**Response:**
```json
{
  "message": "SpliceAI analysis started",
  "task_id": "spliceai_abc123",
  "variants_to_process": 1000
}
```

**SpliceAI Output Columns:**
- `DS_AG` - Delta score acceptor gain
- `DS_AL` - Delta score acceptor loss
- `DS_DG` - Delta score donor gain
- `DS_DL` - Delta score donor loss
- `DP_AG` - Delta position acceptor gain
- `DP_AL` - Delta position acceptor loss
- `DP_DG` - Delta position donor gain
- `DP_DL` - Delta position donor loss

**Example:**
```javascript
await axios.get('/workspace/apply/spliceai/data.csv', {
  params: { distance: 100 },
  headers: { uuid, sid }
});
```

---

### Apply CADD

Runs CADD pathogenicity scoring on variants.

**Endpoint:** `GET /workspace/apply/cadd/<path>`

**Query Parameters:**
```
genome_build: "GRCh37" | "GRCh38" (default: "GRCh38")
```

**Response:**
```json
{
  "message": "CADD analysis started",
  "task_id": "cadd_abc123",
  "variants_to_process": 1000
}
```

**CADD Output Columns:**
- `CADD_raw` - Raw CADD score
- `CADD_phred` - CADD Phred-scaled score (higher = more deleterious)

**Example:**
```javascript
await axios.get('/workspace/apply/cadd/data.csv', {
  params: { genome_build: 'GRCh38' },
  headers: { uuid, sid }
});
```

---

### Apply REVEL

Runs REVEL pathogenicity scoring on variants.

**Endpoint:** `GET /workspace/apply/revel/<path>`

**Response:**
```json
{
  "message": "REVEL analysis started",
  "task_id": "revel_abc123",
  "variants_to_process": 1000
}
```

**REVEL Output Columns:**
- `REVEL_score` - REVEL pathogenicity score (0-1, higher = more pathogenic)

**Example:**
```javascript
await axios.get('/workspace/apply/revel/data.csv', {
  headers: { uuid, sid }
});
```

---

## WebSocket Events

### Connection

**Event:** `connect`

**Client Action:**
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8080', {
  transports: ['websocket'],
  query: { uuid: localStorage.getItem('uuid') }
});

socket.on('connect', () => {
  console.log('Connected:', socket.id);
  // Save session ID for HTTP requests
  axios.defaults.headers.common['sid'] = socket.id;
});
```

---

### Console Feedback

Real-time feedback messages from backend operations.

**Event:** `console_feedback`

**Payload:**
```json
{
  "type": "info" | "success" | "warning" | "error",
  "message": "Operation message",
  "timestamp": "2025-10-27T12:34:56.789Z"
}
```

**Client Handler:**
```javascript
socket.on('console_feedback', (data) => {
  console.log(`[${data.type}] ${data.message}`);
  // Update console view in UI
  addConsoleMessage(data);
});
```

**Example Messages:**
- `{ type: "info", message: "Starting SpliceAI analysis..." }`
- `{ type: "success", message: "Analysis complete: 1000 variants processed" }`
- `{ type: "error", message: "Failed to read file: Permission denied" }`

---

### Workspace Update

Notification when file tree structure changes.

**Event:** `workspace_update_feedback`

**Payload:**
```json
{
  "action": "create" | "rename" | "delete",
  "path": "folder1/file.csv"
}
```

**Client Handler:**
```javascript
socket.on('workspace_update_feedback', (data) => {
  // Refresh file tree
  fetchWorkspaceStructure();
});
```

---

### File Save Feedback

Confirmation after file save operation.

**Event:** `workspace_file_save_feedback`

**Payload:**
```json
{
  "success": true,
  "path": "data.csv",
  "message": "File saved successfully"
}
```

**Client Handler:**
```javascript
socket.on('workspace_file_save_feedback', (data) => {
  if (data.success) {
    setUnsaved(false);
    showNotification('File saved');
  }
});
```

---

### Export Complete

Notification when file export completes.

**Event:** `workspace_export_feedback`

**Payload:**
```json
{
  "path": "results.csv",
  "download_url": "/workspace/export/results.csv"
}
```

**Client Handler:**
```javascript
socket.on('workspace_export_feedback', (data) => {
  // Trigger download
  window.location.href = data.download_url;
});
```

---

## Rate Limiting (Future)

Not implemented in v0.2-alpha. Planned for v0.3+:

- 100 requests per minute per user
- 10 concurrent tool executions per user
- Response header: `X-RateLimit-Remaining`

---

## Versioning

**Current Version:** v1 (`/api/v1`)

**Future Versions:**
- v2 will introduce RESTful resource endpoints
- v1 will be maintained for backward compatibility
- Deprecation notices will be given 6 months in advance

---

## Examples

### Complete Workflow: Import → Analyze → Export

```javascript
// 1. Import file
const formData = new FormData();
formData.append('files', csvFile);

await axios.post('/workspace/import', formData, {
  headers: { uuid, sid, 'Content-Type': 'multipart/form-data' }
});

// 2. Run SpliceAI analysis
await axios.get('/workspace/apply/spliceai/uploaded_file.csv', {
  params: { distance: 50 },
  headers: { uuid, sid }
});

// Wait for console_feedback event: "SpliceAI analysis complete"

// 3. Get results
const results = await axios.get('/workspace/file/uploaded_file.csv', {
  params: { page: 1, rows_per_page: 100 },
  headers: { uuid, sid }
});

// 4. Export results
const blob = await axios.get('/workspace/export/uploaded_file.csv', {
  headers: { uuid, sid },
  responseType: 'blob'
});

// Download file
const url = window.URL.createObjectURL(blob.data);
const link = document.createElement('a');
link.href = url;
link.download = 'results.csv';
link.click();
```

---

## Support

For issues or questions:
- GitHub Issues: [Repository Issues](https://github.com/your-repo/kath/issues)
- Documentation: [/docs](../)
- Developer Setup: [DEVELOPER_SETUP.md](../DEVELOPER_SETUP.md)

---

**API Reference Version:** 1.0
**Last Updated:** 2025-10-27
