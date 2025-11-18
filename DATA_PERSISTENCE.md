# KATH Data Persistence Guide

## Overview

KATH uses persistent Docker volume mounts to ensure all data generated during genetic analysis is preserved between container runs. This guide explains how data persistence works, how to verify it, and how to manage persistent storage.

## Data Persistence Architecture

KATH maintains data persistence through two primary volume mounts:

### 1. **Workspace Volume** - Genetic Data Analysis Files
```
Host Path:      ./data/
Container Path: /kath/app/back_end/src/workspace/default/
Purpose:        Stores all CSV files, analysis results, and workspace data
```

### 2. **Database Volume** - Application Database
```
Host Path:      ./database/
Container Path: /kath/app/back_end/instance/
Purpose:        Stores SQLite database (kath.db) with metadata and analysis history
```

## Data Directory Structure

When you run KATH, the following directory structure is created:

```
data/                              # Workspace data (persistent)
├── *.csv                          # Analysis result files
├── cadd/                          # CADD analysis working files
│   ├── [timestamp]/
│   │   ├── input/                # CADD input files
│   │   └── output/               # CADD output files
├── spliceai/                      # SpliceAI analysis files
├── lovd_[timestamp]/              # LOVD database files
├── lovd_[timestamp].txt           # LOVD data export
├── gnomad_[timestamp].csv         # gnomAD frequency data
├── clinvar_[timestamp].csv        # ClinVar variant data
└── spliceai_[timestamp].csv       # SpliceAI predictions

database/                          # Database (persistent)
└── kath.db                        # SQLite database with metadata, analysis history, file index
```

## Volume Mount Details

### Docker Run Command

The `start-kath.sh` script sets up persistent volumes automatically:

```bash
docker run \
  -v "$WORKSPACE_DIR:/kath/app/back_end/src/workspace/$WORKSPACE_UUID" \
  -v "$DATABASE_DIR:/kath/app/back_end/instance" \
  ...
```

Where:
- `$WORKSPACE_DIR` = `./data` (host directory)
- `$WORKSPACE_UUID` = `default` (workspace name inside container)
- `$DATABASE_DIR` = `./database` (host database directory)

### Dockerfile Volume Declarations

The Dockerfile declares these as named volumes:

```dockerfile
VOLUME ["${APP_DIR}/back_end/instance", "${APP_DIR}/back_end/src/workspace"]
```

This ensures containers always respect the volume mount structure.

## How Data Persistence Works

### 1. **Workspace Initialization**
When the container starts:
1. KATH checks if `/kath/app/back_end/src/workspace/default/` exists
2. If the directory is empty (first run), template files are copied
3. If the directory has existing files (subsequent runs), they are discovered and loaded
4. All existing CSV files are automatically indexed in the database

### 2. **File Discovery and Indexing**
The application automatically discovers existing data files:
- CSV files in the workspace are indexed into the SQLite database
- File metadata (headers, row counts) is extracted and cached
- Previous analysis results are immediately available without re-processing

### 3. **Persistent Storage Flow**
```
User Uploads File
    ↓
Container Processes (analysis tools: CADD, SpliceAI, etc.)
    ↓
Results Written to ./data/ (host filesystem)
    ↓
Metadata Recorded in ./database/kath.db
    ↓
Container Stopped / Removed
    ↓
Host Retains data/ and database/ directories
    ↓
Container Restarted
    ↓
Data Immediately Available (no re-processing needed)
```

## Using Persistent Data

### Accessing Previous Data

When you restart KATH with the same `data/` and `database/` directories:

```bash
./start-kath.sh
```

All previous data is automatically available:
1. Historical CSV files appear in the workspace
2. Analysis metadata is restored from the database
3. You can immediately re-run tools or export previous results
4. No data re-processing is required

### Example Workflow

```bash
# First run - analyze genetic data
./start-kath.sh
# [User uploads file, runs CADD analysis]
# [Results saved to ./data/cadd_*.csv]
# [Press Ctrl+C to stop]

# Later - access same data
./start-kath.sh
# [All previous files and results are available]
# [Can run additional analyses or export results]
```

## Verifying Data Persistence

### Check Data Directory

```bash
# View workspace data files
ls -lah data/

# Should show:
# -rw-r--r-- all_merged_*.csv
# -rw-r--r-- cadd_*.csv
# -rw-r--r-- clinvar_*.csv
# -rw-r--r-- gnomad_*.csv
# drwxr-xr-x cadd/
# drwxr-xr-x spliceai/
# etc.
```

### Check Database

```bash
# View database file
ls -lah database/

# Should show:
# -rw-r--r-- kath.db (typically 100KB-1MB)
```

### Verify Inside Container

```bash
# After container is running, check from another terminal:
docker exec kath ls -lah /kath/app/back_end/src/workspace/default/

# Should show all the CSV files and directories
```

### Check Database Contents

```bash
# View database tables and metadata
docker exec kath sqlite3 /kath/app/back_end/instance/kath.db ".tables"

# Should show: file_metadata  variant_metadata  workspace_metadata
```

## Backup and Restore

### Backing Up Data

```bash
# Backup workspace data
tar -czf kath_data_backup_$(date +%Y%m%d).tar.gz data/

# Backup database
tar -czf kath_db_backup_$(date +%Y%m%d).tar.gz database/

# Backup both
tar -czf kath_backup_$(date +%Y%m%d).tar.gz data/ database/
```

### Restoring Data

```bash
# Restore from backup (must be stopped first)
docker-compose down

# Restore data
tar -xzf kath_data_backup_YYYYMMDD.tar.gz

# Restore database
tar -xzf kath_db_backup_YYYYMMDD.tar.gz

# Restart
./start-kath.sh
```

## Managing Persistent Storage

### Clearing Old Data

To start fresh while preserving the application:

```bash
# Stop the container
./start-kath.sh  # [Ctrl+C to stop]

# Clear workspace (but keep structure)
rm -rf data/*.csv data/cadd data/spliceai data/lovd_*

# Clear database
rm -f database/kath.db

# Restart (template will be re-created)
./start-kath.sh
```

### Moving Data Between Systems

To migrate KATH to a different system:

```bash
# On source system - backup
tar -czf kath_complete_backup.tar.gz data/ database/

# Transfer file to destination system
scp kath_complete_backup.tar.gz user@destination:/path/to/kath/

# On destination system - restore
tar -xzf kath_complete_backup.tar.gz

# Verify
ls -la data/ database/

# Run
./start-kath.sh
```

## Troubleshooting Data Persistence

### "Files Not Found After Restart"

**Problem**: Data files that existed previously are not visible after restart.

**Solutions**:
1. Check if `data/` and `database/` directories still exist:
   ```bash
   ls -la data/ database/
   ```

2. Verify Docker volume mount:
   ```bash
   docker inspect kath | grep -A 5 "Mounts"
   ```

3. Check file permissions (should be readable by container):
   ```bash
   ls -la data/
   # Should show permissions like: drwxrwxr-x
   ```

### "Database Corruption / Unexpected Errors"

**Problem**: SQLite database appears corrupted or entries are missing.

**Solution**: Database can be regenerated (will re-index files):
```bash
# Stop container
./start-kath.sh  # [Ctrl+C]

# Remove corrupt database
rm database/kath.db

# Restart - database will be recreated
./start-kath.sh
```

### "Out of Disk Space"

**Problem**: Container stops because host is out of space.

**Solutions**:
1. Check disk usage:
   ```bash
   du -sh data/ database/
   df -h
   ```

2. Archive old data:
   ```bash
   tar -czf archive_old_data.tar.gz data/
   rm -rf data/
   mkdir data
   ```

3. Move data to larger disk/partition

## Docker Compose Persistent Volumes

If using `docker-compose.yml`:

```yaml
version: '3.8'
services:
  kath:
    image: cpu64/kath:latest
    volumes:
      - ./data:/kath/app/back_end/src/workspace/default
      - ./database:/kath/app/back_end/instance
      - ./config:/config
    ports:
      - "5173:5173"
      - "8080:8080"
```

This ensures the same volumes are always used.

## Data Persistence with Named Volumes

For production deployments, use Docker named volumes:

```bash
# Create named volumes
docker volume create kath_data
docker volume create kath_database

# Run with named volumes
docker run \
  -v kath_data:/kath/app/back_end/src/workspace/default \
  -v kath_database:/kath/app/back_end/instance \
  cpu64/kath:latest
```

Benefits:
- Volumes managed by Docker (portable across systems)
- Automatic driver selection (local, NFS, cloud storage)
- Easier to backup/restore
- Survives container deletion

## Viewing Named Volume Contents

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect kath_data

# Mount volume to inspect
docker run -v kath_data:/mnt alpine ls -la /mnt
```

## Configuration Persistence

Configuration files are also persistent via host directory mount:

```bash
docker run \
  -v ./config:/config \
  ...
```

Changes to `config/network_config.yaml` and `config/docker-resources.yaml` survive container restarts without rebuilding.

## Best Practices

### 1. **Regular Backups**
```bash
# Weekly backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "backups/kath_backup_$DATE.tar.gz" data/ database/
echo "Backup completed: backups/kath_backup_$DATE.tar.gz"
```

### 2. **Monitor Disk Space**
```bash
# Check if data is growing too large
du -sh data/ database/
du -sh data/* | sort -h
```

### 3. **Document Your Data**
```bash
# Create metadata file
cat > data/README.md << EOF
# KATH Analysis Data

## Analysis Date
$(date)

## Files
$(ls -lh data/ | tail -n +2)

## Database Size
$(du -h database/kath.db)
EOF
```

### 4. **Use `.gitignore` for Large Files**
```bash
# Don't commit data/ and database/ to git
echo "data/" >> .gitignore
echo "database/" >> .gitignore
git add .gitignore
```

### 5. **Test Restore Procedures**
Periodically test that backups work:
```bash
# Extract backup to test directory
mkdir test_restore
tar -xzf backups/kath_backup_latest.tar.gz -C test_restore/
ls -la test_restore/data/
```

## Performance Considerations

### File System Performance
- **Fast SSD**: Use local SSD for best performance
- **Network Storage**: NFS mounts may be slower for frequent file access
- **Cloud Storage**: Use cloud-optimized volumes (AWS EBS, GCP Persistent Disk)

### Database Performance
- SQLite works best with local storage
- Large datasets (>100K variants) may benefit from journaling disable:
  ```bash
  docker exec kath sqlite3 /kath/app/back_end/instance/kath.db "PRAGMA journal_mode=WAL;"
  ```

## Summary

KATH ensures data persistence through:
1. ✅ **Host volume mounts** - Data survives container lifecycle
2. ✅ **SQLite database** - Metadata and analysis history
3. ✅ **Automatic discovery** - Previous files indexed on startup
4. ✅ **Backup/restore** - Simple tar-based backup system
5. ✅ **Configuration persistence** - Settings survive restarts

All your genetic analysis data is safe and accessible across container restarts!
