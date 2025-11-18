#!/usr/bin/env pwsh
# KATH Complete Docker Build Script for PowerShell
# Builds both reference files and application images

param(
    [Parameter(Position=0)]
    [ValidateSet("--full", "--help", "-h", "help")]
    [string]$BuildMode = "",

    [Parameter()]
    [string]$Tag = "latest"
)

# Configuration
$ImageName = "cpu64/kath"
$FilesImage = "${ImageName}:files"
$AppImage = "${ImageName}:${Tag}"
$ErrorActionPreference = "Stop"

# Color functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "  $Message"
    Write-Host "=============================================="
    Write-Host ""
}

function Show-Help {
    Write-Host ""
    Write-Host "KATH Complete Docker Build Script (PowerShell - Unified Multi-Stage Build)"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\build-kath-complete.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --full         Rebuild everything (full build with no cache)"
    Write-Host "  --help, -h     Show this help message"
    Write-Host "  -Tag <tag>     Specify image tag (default: latest)"
    Write-Host ""
    Write-Host "Default behavior:"
    Write-Host "  Builds the complete KATH system using unified multi-stage Dockerfile"
    Write-Host "  - Stage 1: Downloads reference files (hg38.fa, REVEL database, etc.)"
    Write-Host "  - Stage 2: Builds application (Python backend + Node.js frontend)"
    Write-Host "  - Includes: Firefox ESR binary, GeckoDriver, CUDA support"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\build-kath-complete.ps1              (standard build)"
    Write-Host "  .\build-kath-complete.ps1 --full       (rebuild from scratch)"
    Write-Host "  .\build-kath-complete.ps1 -Tag v1.0    (custom tag)"
    Write-Host ""
    exit 0
}

function Test-Docker {
    Write-Info "Checking Docker installation..."

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-ErrorMsg "Docker is not installed!"
        Write-Host ""
        Write-Host "Please install Docker Desktop from:"
        Write-Host "https://www.docker.com/products/docker-desktop"
        Write-Host ""
        exit 1
    }

    Write-Success "Docker is installed"

    Write-Info "Checking Docker daemon..."
    try {
        $null = docker info 2>&1
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-ErrorMsg "Docker daemon is not running!"
        Write-Host ""
        Write-Host "Starting Docker Desktop..."

        $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerPath) {
            Start-Process $dockerPath
            Write-Info "Waiting for Docker to start..."
            Start-Sleep -Seconds 10

            # Wait up to 60 seconds for Docker to be ready
            $counter = 0
            while ($counter -lt 60) {
                try {
                    $null = docker info 2>&1
                    Write-Success "Docker is ready"
                    return
                }
                catch {
                    $counter++
                    Start-Sleep -Seconds 1
                }
            }

            Write-ErrorMsg "Docker failed to start after 60 seconds"
            exit 1
        }
        else {
            Write-Host "Please start Docker Desktop manually and try again."
            exit 1
        }
    }
}

function Test-ImageExists {
    param([string]$ImageName)

    try {
        $null = docker inspect $ImageName 2>&1
        return $true
    }
    catch {
        return $false
    }
}

function Build-UnifiedImage {
    Write-Header "Building Complete KATH System (Unified Multi-Stage Build)"

    Write-Info "Building: $AppImage"
    Write-Info "This will build both reference files and application in one image"
    Write-Info "Expected time: 15-30 minutes"
    Write-Host ""

    $env:DOCKER_BUILDKIT = "1"

    docker build `
        -t $AppImage `
        -f app/Dockerfile `
        --progress=plain `
        app/

    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Build failed!"
        exit 1
    }

    Write-Host ""
    Write-Success "Complete KATH image built successfully!"
    docker images | Select-String $ImageName
    Write-Host ""
}

# Deprecated: Build-AppImage is no longer needed with unified Dockerfile
# The unified build handles both stages in one go

function Show-NextSteps {
    Write-Header "Next Steps"

    Write-Host "To run KATH, use:"
    Write-Host "  - .\start-kath.ps1        (PowerShell script)"
    Write-Host "  - start-kath.bat          (Windows batch script)"
    Write-Host "  - docker-compose up       (Docker Compose)"
    Write-Host ""
    Write-Host "To access KATH:"
    Write-Host "  - Frontend: http://localhost:5173"
    Write-Host "  - Backend:  http://localhost:8080"
    Write-Host "  - Health:   http://localhost:8080/api/v1/monitoring/health"
    Write-Host ""
    Write-Host "To clean up old images:"
    Write-Host "  - docker system prune -af"
    Write-Host ""
}

function Show-ImageDetails {
    Write-Info "Image details:"
    $size = docker inspect $AppImage --format='Size: {{.Size}} bytes' 2>$null
    $created = docker inspect $AppImage --format='Created: {{.Created}}' 2>$null
    Write-Host "  $size"
    Write-Host "  $created"
    Write-Host ""
}

# Main execution
Write-Header "KATH Complete Docker Build Script"

# Show help if requested
if ($BuildMode -in @("--help", "-h", "help")) {
    Show-Help
}

# Check Docker
Test-Docker
Write-Host ""

# Determine build mode
switch ($BuildMode) {
    "--full" {
        Write-Info "Building with --no-cache flag (full rebuild from scratch)"
        Write-Host ""

        Write-Header "Building Complete KATH System (No Cache)"
        Write-Info "Building: $AppImage"
        Write-Host ""

        $env:DOCKER_BUILDKIT = "1"

        docker build `
            --no-cache `
            -t $AppImage `
            -f app/Dockerfile `
            --progress=plain `
            app/

        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "Build failed!"
            exit 1
        }

        Write-Success "Complete build finished!"
        Show-ImageDetails
        Show-NextSteps
        exit 0
    }

    default {
        # Standard build mode - unified multi-stage
        Build-UnifiedImage
        Show-ImageDetails
        Show-NextSteps
        exit 0
    }
}
