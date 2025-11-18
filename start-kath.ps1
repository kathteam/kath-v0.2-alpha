# KATH Initialization Script for Windows (PowerShell)
# This script automates the setup and launch of the KATH genetic analysis tool

param(
    [switch]$NoWait
)

$ErrorActionPreference = "Stop"

$KATH_IMAGE = "cpu64/kath:latest"
$CONTAINER_NAME = "kath"
$FRONTEND_PORT = 5173
$BACKEND_PORT = 8080
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$WORKSPACE_DIR = Join-Path $SCRIPT_DIR "data"

function Write-Header {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  KATH Genetic Analysis Tool" -ForegroundColor Cyan
    Write-Host "  Version: v0.2-alpha" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warning2 {
    param([string]$Message)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Test-DockerInstalled {
    try {
        $null = Get-Command docker -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $?
    }
    catch {
        return $false
    }
}

function Wait-ForDocker {
    Write-Info "Waiting for Docker to start..."
    $maxAttempts = 60
    $attempt = 0

    while (-not (Test-DockerRunning)) {
        if ($attempt -ge $maxAttempts) {
            throw "Docker failed to start within 60 seconds"
        }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
        $attempt++
    }

    Write-Host ""
    Write-Success "Docker is running!"
}

function Stop-ExistingContainer {
    $existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $CONTAINER_NAME }
    if ($existing) {
        Write-Info "Stopping existing KATH container..."
        docker stop $CONTAINER_NAME 2>&1 | Out-Null
        docker rm $CONTAINER_NAME 2>&1 | Out-Null
        Write-Success "Existing container removed"
    }
}

function New-WorkspaceDirectory {
    if (-not (Test-Path $WORKSPACE_DIR)) {
        Write-Info "Creating workspace directory at $WORKSPACE_DIR..."
        New-Item -ItemType Directory -Path $WORKSPACE_DIR -Force | Out-Null
        Write-Success "Workspace directory created"
    }
    else {
        Write-Info "Workspace directory already exists: $WORKSPACE_DIR"
    }
}

function Get-DockerImage {
    Write-Info "Pulling KATH Docker image (this may take a few minutes)..."
    docker pull $KATH_IMAGE
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to pull Docker image"
    }
    Write-Success "Docker image downloaded successfully"
}

function Start-KathContainer {
    Write-Info "Starting KATH container..."

    # Start browser in background job (delayed)
    Start-Job -ScriptBlock {
        param($port)
        Start-Sleep -Seconds 10
        Start-Process "http://localhost:$port"
    } -ArgumentList $FRONTEND_PORT | Out-Null

    Write-Host ""
    Write-Success "Starting KATH..."
    Write-Host ""
    Write-Host "  Frontend URL: http://localhost:${FRONTEND_PORT}"
    Write-Host "  Backend API:  http://localhost:${BACKEND_PORT}"
    Write-Host "  Workspace:    $WORKSPACE_DIR"
    Write-Host ""
    Write-Info "Press Ctrl+C to stop KATH and exit"
    Write-Host ""

    # Run container (interactive, auto-remove on exit)
    docker run `
        --name $CONTAINER_NAME `
        -v "${WORKSPACE_DIR}:/kath/app/back_end/src/workspace/8d8ac610-566d-4ef0-9c22-186b2a5ed793" `
        -it `
        --rm `
        -p "${BACKEND_PORT}:8080" `
        -p "${FRONTEND_PORT}:5173" `
        -e DOMAIN=localhost `
        $KATH_IMAGE

    if ($LASTEXITCODE -ne 0) {
        throw "KATH container exited with error"
    }

    Write-Success "KATH stopped successfully!"
}

# Main execution
try {
    Write-Header

    # Check Docker installation
    if (-not (Test-DockerInstalled)) {
        Write-ErrorMsg "Docker is not installed!"
        Write-Host ""
        Write-Host "Please install Docker Desktop from:"
        Write-Host "https://www.docker.com/products/docker-desktop"
        Write-Host ""
        Write-Host "After installation, restart your computer and run this script again."
        exit 1
    }

    Write-Success "Docker is installed"

    # Check if Docker is running
    if (-not (Test-DockerRunning)) {
        Write-Warning2 "Docker is not running"
        Write-Info "Starting Docker Desktop..."

        $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerPath) {
            Start-Process $dockerPath
        }
        else {
            throw "Docker Desktop executable not found at expected path"
        }

        Wait-ForDocker
    }
    else {
        Write-Success "Docker is running"
    }

    # Setup workspace
    New-WorkspaceDirectory

    # Stop existing container
    Stop-ExistingContainer

    # Pull latest image
    Get-DockerImage

    # Run container (this blocks until container exits)
    Start-KathContainer
}
catch {
    Write-ErrorMsg $_.Exception.Message
    exit 1
}
