# KATH Build Instructions

## Overview

This document explains the build process for the KATH system,
including which scripts to use and when.

## Quick Answer: Which Scripts Do I Need?

**Short Answer:** Use **`build-kath-complete`** ONLY. It's the only script you need.

- ✅ **`build-kath-complete.sh`** (Linux/Mac) or
  **`build-kath-complete.ps1`** (Windows) - **USE THIS**
- ❌ **`build-docker.sh`** - Do NOT use this (deprecated)

## Build Scripts Explained

### 1. `build-kath-complete` (RECOMMENDED - Use This One)

**Status:** ✅ Current, Maintained, Unified Multi-Stage Build

**What it does:**

- Builds the complete KATH Docker image using a unified multi-stage Dockerfile
- Stage 1: Downloads and prepares reference files (hg38.fa, REVEL database, etc.)
- Stage 2: Builds the application (Python backend + Node.js frontend)
- Single build process - NO separate steps needed

**Why use it:**

- All-in-one solution
- Optimized caching for faster builds
- Multi-stage approach minimizes final image size
- Properly handles all dependencies
- Includes Firefox ESR binary and GeckoDriver
- CUDA support ready
- Configuration system integration

**Usage:**

```bash
# Linux/Mac - Standard build with caching
./build-kath-complete.sh

# Linux/Mac - Full rebuild from scratch (no cache)
./build-kath-complete.sh --full

# Linux/Mac - Build with custom tag
./build-kath-complete.sh --full v1.0

# Windows PowerShell - Standard build
.\build-kath-complete.ps1

# Windows PowerShell - Full rebuild
.\build-kath-complete.ps1 -Full

# Windows PowerShell - Build with custom tag
.\build-kath-complete.ps1 -Full -ImageTag "v1.0"

# Windows Batch (CMD)
build-kath-complete.bat
```

**Time:** 15-30 minutes depending on internet connection

**Output:** `cpu64/kath:latest` (or custom tag)

---

### 2. `build-docker` (DEPRECATED - Do NOT Use)

**Status:** ❌ Old, No Longer Maintained

**Why it exists:**

- Legacy script from earlier architecture
- Used with separate file building process
- Now replaced by unified `build-kath-complete`

**Why DON'T use it:**

- ❌ Builds from `app/` subdirectory (incorrect context)
- ❌ Uses `--progress=plain` (incompatible with older Docker)
- ❌ No longer the primary build path
- ❌ May cause conflicts if used alongside complete build

**⚠️ WARNING:** Do not use `build-docker.sh` for new builds. It is
deprecated and kept only for reference.

---

## Fresh Build Process

### Step 1: Clean the Project (Optional but Recommended)

Before building, clean up old artifacts to ensure a fresh build:

**Linux/Mac:**

```bash
./clean_all.sh
```

**Windows PowerShell:**

```powershell
.\clean_all.ps1
```

**Windows CMD:**

```cmd
clean_all.bat
```

**Options:**

```bash
./clean_all.sh --docker      # Also remove Docker images
./clean_all.sh --force       # Skip confirmation prompts
```

**What gets cleaned:**

- Python caches (`__pycache__`, `.pytest_cache`, `.mypy_cache`)
- Node.js caches (`node_modules`)
- Build artifacts (`dist`, `build`, `htmlcov`)
- Log files
- Temporary files

**What does NOT get cleaned:**

- Source code
- Configuration files
- Data files
- Environment files
- Git history

### Step 2: Install Node Dependencies (if cleaned)

If you ran `clean_all.sh --docker`, you'll need to reinstall Node dependencies:

```bash
cd app/front_end
npm install
cd ../..
```

### Step 3: Build the Docker Image

Run the build script:

**Linux/Mac:**

```bash
# Standard build (uses cache for speed)
./build-kath-complete.sh

# Or full rebuild from scratch
./build-kath-complete.sh --full
```

**Windows PowerShell:**

```powershell
# Standard build
.\build-kath-complete.ps1

# Or full rebuild
.\build-kath-complete.ps1 -Full
```

**Windows CMD:**

```cmd
build-kath-complete.bat
```

### Step 4: Verify the Build

After the build completes:

```bash
# Check that the image was created
docker images | grep cpu64/kath

# Test the image
docker run --rm cpu64/kath:latest ls -la /config/
```

---

## Complete Build Workflow

### For Linux/Mac Users

```bash
# 1. Navigate to project root
cd ~/KATH/kath-v0.2-alpha

# 2. Clean (optional but recommended)
./clean_all.sh

# 3. Install dependencies (if cleaned)
cd app/front_end && npm install && cd ../..

# 4. Build
./build-kath-complete.sh

# 5. Verify
docker images | grep cpu64/kath
```

### For Windows PowerShell Users

```powershell
# 1. Navigate to project root
cd C:\KATH\kath-v0.2-alpha

# 2. Clean (optional but recommended)
.\clean_all.ps1

# 3. Install dependencies (if cleaned)
cd app\front_end; npm install; cd ..\..

# 4. Build
.\build-kath-complete.ps1

# 5. Verify
docker images | Select-String "cpu64/kath"
```

### For Windows CMD Users

```cmd
# 1. Navigate to project root
cd C:\KATH\kath-v0.2-alpha

# 2. Clean (optional but recommended)
clean_all.bat

# 3. Install dependencies (if cleaned)
cd app\front_end && npm install && cd ..\..

# 4. Build
build-kath-complete.bat

# 5. Verify
docker images | findstr cpu64/kath
```

---

## Script Comparison Table

| Feature | build-kath-complete | build-docker |
|---------|-------------------|--------------|
| Status | ✅ Current | ❌ Deprecated |
| Maintained | Yes | No |
| Multi-stage | Yes | No |
| Reference files | Included | Separate step |
| Application build | Included | Included |
| Context | Root dir | app/ subdir |
| Recommended | YES | NO |
| For new builds | ✅ Use this | ❌ Don't use |

---

## Build Architecture Explanation

### Multi-Stage Build Process (build-kath-complete)

The unified Dockerfile uses Docker's multi-stage build feature:

## Stage 1: Files (Alpine Linux)

- Small base image
- Downloads large reference files (hg38.fa, REVEL database)
- Processes and prepares files
- Output: Intermediate layer with prepared files

## Stage 2: Application (Ubuntu 24.04 + CUDA)

- Copies reference files from Stage 1
- Installs system dependencies
- Installs Python packages
- Installs Node.js and npm
- Installs Firefox ESR binary
- Installs GeckoDriver
- Copies application code
- Final output: `cpu64/kath:latest` image (~7.4GB)

**Benefits:**

- Files downloaded/processed once
- Final image doesn't include build tools
- Better caching strategy
- Faster rebuild times after first build

---

## Common Build Scenarios

### Scenario 1: Fresh Development Setup

```bash
# Clean everything
./clean_all.sh --docker --force

# Install fresh dependencies
cd app/front_end && npm install && cd ../..

# Build fresh image
./build-kath-complete.sh --full
```

**Time:** 30-40 minutes

---

### Scenario 2: Quick Rebuild (After Code Changes)

```bash
# Use cache (faster)
./build-kath-complete.sh
```

**Time:** 5-10 minutes (uses cached layers)

---

### Scenario 3: Complete System Reset

```bash
# Clean everything including Docker
./clean_all.sh --docker --force

# Install dependencies
cd app/front_end && npm install && cd ../..

# Full rebuild
./build-kath-complete.sh --full

# Verify
docker images | grep cpu64/kath
```

**Time:** 40-50 minutes

---

## Troubleshooting Build Issues

### Problem: "Docker is not running"

**Solution:**

```bash
# Linux
sudo systemctl start docker

# Mac
# Start Docker Desktop from Applications

# Windows
# Start Docker Desktop or
docker context use default
```

### Problem: "command not found: docker"

**Solution:** Docker is not installed

- Linux: `curl -fsSL https://get.docker.com | sh`
- Mac: `brew install --cask docker`
- Windows: Download Docker Desktop

### Problem: Build fails with "no space left on device"

**Solution:** Docker image is too large (~7.4GB)

```bash
# Free up disk space
docker system prune -a    # Removes unused images
rm -rf ~/Library/Caches   # On Mac
```

### Problem: Node modules installation fails

**Solution:**

```bash
# Reinstall Node modules
cd app/front_end
rm -rf node_modules package-lock.json
npm install
```

### Problem: Build cache issues

**Solution:** Use full rebuild to skip cache

```bash
./build-kath-complete.sh --full
```

---

## What NOT to Do

### ❌ DON'T Use These Commands

```bash
# WRONG - old script, incompatible context
./build-docker.sh

# WRONG - builds from wrong directory
docker build -f Dockerfile .

# WRONG - missing configuration
docker build -f app/Dockerfile app/

# WRONG - inconsistent image name
docker build -t kath:latest .
```

### ✅ DO Use These Commands

```bash
# Correct - use build script
./build-kath-complete.sh

# Correct - if running build manually
docker build -f app/Dockerfile -t cpu64/kath:latest .
```

---

## Environment Variables for Build

If you need to customize the build:

```bash
# Linux/Mac
export DOCKER_BUILDKIT=1                    # Use BuildKit
export DOCKER_BUILDKIT=0                    # Use legacy builder
export TAG="v1.0"                          # Custom image tag

# Windows PowerShell
$env:DOCKER_BUILDKIT=1
$env:TAG="v1.0"
```

---

## Next Steps After Build

Once the image is built successfully:

### Run with Docker Compose

```bash
docker-compose up -d
```

### Run with plain Docker

```bash
docker run -d \
  -p 5173:5173 \
  -p 8080:8080 \
  -v $(pwd)/config:/config:ro \
  cpu64/kath:latest
```

### Convert to Singularity (HPC)

```bash
singularity build kath.sif docker://cpu64/kath:latest
```

### Check Configuration

```bash
docker run --rm cpu64/kath:latest cat /config/network_config.yaml
```

---

## Summary

| Task | Command |
|------|---------|
| **Clean project** | `./clean_all.sh` |
| **Build image** | `./build-kath-complete.sh` |
| **Full rebuild** | `./build-kath-complete.sh --full` |
| **Verify build** | `docker images \| grep cpu64/kath` |
| **Run with Compose** | `docker-compose up -d` |
| **Check config** | `docker run --rm cpu64/kath:latest cat /config/*.yaml` |

---

## Recommended Build Process

For the best results, follow this process:

1. ✅ Clean the project (`./clean_all.sh`)
2. ✅ Install dependencies (`cd app/front_end && npm install`)
3. ✅ Build the image (`./build-kath-complete.sh`)
4. ✅ Verify the image (`docker images | grep cpu64/kath`)
5. ✅ Test the image (`docker run --rm ...`)

**Time needed:** 30-40 minutes for fresh build

**Expected result:** `cpu64/kath:latest` (~7.4GB) ready for deployment

---

## Support

For more information:

- Configuration: See `CONFIGURATION.md`
- Docker Compose: See `docker-compose.yml`
- Application setup: See `app/Dockerfile`
- Build script source: `build-kath-complete.sh` or
  `build-kath-complete.ps1`
