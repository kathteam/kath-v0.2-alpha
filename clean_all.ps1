<#
.SYNOPSIS
    KATH Project Cleanup Script
    Cleans up all build artifacts, caches, and temporary files to prepare for a fresh build

.DESCRIPTION
    Removes Python caches, Node.js caches, build artifacts, logs, and temporary files
    Optionally removes Docker images

.PARAMETER Docker
    Also remove Docker images (cpu64/kath:*)

.PARAMETER Force
    Skip all confirmation prompts

.EXAMPLE
    # Clean build artifacts only
    .\clean_all.ps1

    # Clean everything including Docker images
    .\clean_all.ps1 -Docker

    # Clean without prompts
    .\clean_all.ps1 -Force -Docker
#>

param(
    [switch]$Docker = $false,
    [switch]$Force = $false,
    [switch]$Help = $false
)

# Script configuration
$ErrorActionPreference = "Continue"
$WarningPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$ProjectRoot = $ScriptDir

# Color definitions
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"

# Print functions
function Print-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor $ColorInfo -NoNewline
    Write-Host $Message
}

function Print-Success {
    param([string]$Message)
    Write-Host "[✓] " -ForegroundColor $ColorSuccess -NoNewline
    Write-Host $Message
}

function Print-Warning {
    param([string]$Message)
    Write-Host "[WARNING] " -ForegroundColor $ColorWarning -NoNewline
    Write-Host $Message
}

function Print-Error {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor $ColorError -NoNewline
    Write-Host $Message
}

function Print-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "  $Message"
    Write-Host "=============================================="
    Write-Host ""
}

function Show-Help {
    Write-Host @"

KATH Project Cleanup Script

Usage: .\clean_all.ps1 [OPTIONS]

Options:
  -Docker     Also remove Docker images (cpu64/kath:*)
  -Force      Skip all confirmation prompts
  -Help       Show this help message

Examples:
  # Clean build artifacts only (safe)
  .\clean_all.ps1

  # Clean everything including Docker images
  .\clean_all.ps1 -Docker

  # Clean without prompts
  .\clean_all.ps1 -Force -Docker

What gets cleaned:
  - Python cache (__pycache__, .pytest_cache, .mypy_cache)
  - Node.js cache (node_modules, npm caches)
  - Build artifacts (dist, build, htmlcov)
  - Log files
  - Test coverage data
  - Temporary files

What does NOT get cleaned (safe):
  - Source code
  - Configuration files
  - Data files (data/, database/)
  - Environment files (.env*)
  - Git history

"@
}

function Confirm-Action {
    param([string]$Prompt)

    if ($Force) {
        return $true
    }

    $response = Read-Host "$Prompt (y/N)"
    return $response -match "^[yY]"
}

# Clean Python caches
function Clean-Python {
    Print-Info "Cleaning Python caches..."

    # Remove __pycache__ directories
    $pycaches = Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
    if ($pycaches.Count -gt 0) {
        foreach ($cache in $pycaches) {
            Remove-Item -Path $cache.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed __pycache__ directories"
    }

    # Remove .pytest_cache
    if (Test-Path "$ProjectRoot\.pytest_cache") {
        Remove-Item -Path "$ProjectRoot\.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
        Print-Success "Removed .pytest_cache"
    }

    # Remove .mypy_cache
    if (Test-Path "$ProjectRoot\.mypy_cache") {
        Remove-Item -Path "$ProjectRoot\.mypy_cache" -Recurse -Force -ErrorAction SilentlyContinue
        Print-Success "Removed .mypy_cache"
    }

    # Remove .egg-info directories
    $egginfos = Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue
    if ($egginfos.Count -gt 0) {
        foreach ($egginfo in $egginfos) {
            Remove-Item -Path $egginfo.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed .egg-info directories"
    }

    # Remove compiled Python files
    $pycs = Get-ChildItem -Path $ProjectRoot -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
    $pyos = Get-ChildItem -Path $ProjectRoot -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue

    if ($pycs.Count -gt 0) {
        foreach ($pyc in $pycs) {
            Remove-Item -Path $pyc.FullName -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed .pyc files"
    }

    if ($pyos.Count -gt 0) {
        foreach ($pyo in $pyos) {
            Remove-Item -Path $pyo.FullName -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed .pyo files"
    }
}

# Clean Node.js caches
function Clean-NodeJS {
    Print-Info "Cleaning Node.js caches..."

    # Remove node_modules
    $nodeModulesPath = "$ProjectRoot\app\front_end\node_modules"
    if (Test-Path $nodeModulesPath) {
        Print-Warning "Removing node_modules (this may take a moment)..."
        Remove-Item -Path $nodeModulesPath -Recurse -Force -ErrorAction SilentlyContinue
        Print-Success "Removed node_modules"
    }

    # Remove .npmrc
    $npmrcPath = "$ProjectRoot\app\front_end\.npmrc"
    if (Test-Path $npmrcPath) {
        Remove-Item -Path $npmrcPath -Force -ErrorAction SilentlyContinue
        Print-Success "Removed .npmrc"
    }
}

# Clean build artifacts
function Clean-Artifacts {
    Print-Info "Cleaning build artifacts..."

    $dirsToClean = @("dist", "build", "htmlcov", ".venv", ".venv3")

    foreach ($dir in $dirsToClean) {
        $backendPath = "$ProjectRoot\app\back_end\$dir"
        $rootPath = "$ProjectRoot\$dir"

        if (Test-Path $backendPath) {
            Remove-Item -Path $backendPath -Recurse -Force -ErrorAction SilentlyContinue
            Print-Success "Removed app\back_end\$dir"
        }

        if (Test-Path $rootPath) {
            Remove-Item -Path $rootPath -Recurse -Force -ErrorAction SilentlyContinue
            Print-Success "Removed $dir"
        }
    }

    # Remove coverage files
    $coveragePath = "$ProjectRoot\.coverage"
    if (Test-Path $coveragePath) {
        Remove-Item -Path $coveragePath -Force -ErrorAction SilentlyContinue
        Print-Success "Removed .coverage"
    }
}

# Clean logs
function Clean-Logs {
    Print-Info "Cleaning log files..."

    # Remove log directories
    $logsPath = "$ProjectRoot\app\back_end\src\logs"
    if (Test-Path $logsPath) {
        Remove-Item -Path "$logsPath\*" -Force -Recurse -ErrorAction SilentlyContinue
        Print-Success "Cleaned src\logs"
    }

    # Remove log files
    $logFiles = Get-ChildItem -Path $ProjectRoot -Recurse -Filter "*.log" -ErrorAction SilentlyContinue
    if ($logFiles.Count -gt 0) {
        foreach ($logFile in $logFiles) {
            Remove-Item -Path $logFile.FullName -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed .log files"
    }
}

# Clean temporary files
function Clean-Temp {
    Print-Info "Cleaning temporary files..."

    # Remove OS-specific files
    $osFiles = Get-ChildItem -Path $ProjectRoot -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq ".DS_Store" -or $_.Name -eq "Thumbs.db" }

    if ($osFiles.Count -gt 0) {
        foreach ($file in $osFiles) {
            Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed OS temporary files"
    }

    # Remove editor backup files
    $editorFiles = Get-ChildItem -Path $ProjectRoot -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '~$|\.swp$|\.swo$' }

    if ($editorFiles.Count -gt 0) {
        foreach ($file in $editorFiles) {
            Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
        }
        Print-Success "Removed editor backup files"
    }
}

# Clean Docker images
function Clean-Docker {
    if (-not $Docker) {
        return
    }

    Print-Header "Docker Cleanup"

    # Check if Docker is installed
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Print-Warning "Docker is not installed, skipping Docker cleanup"
        return
    }

    # List KATH images
    try {
        $kathImages = docker images --filter "reference=cpu64/kath:*" --format "{{.Repository}}:{{.Tag}}" 2>$null
    }
    catch {
        Print-Warning "Could not list Docker images"
        return
    }

    if (-not $kathImages) {
        Print-Info "No KATH Docker images found"
        return
    }

    Print-Warning "The following Docker images will be removed:"
    foreach ($image in $kathImages) {
        Write-Host "  - $image"
    }
    Write-Host ""

    if (-not (Confirm-Action "Remove all KATH Docker images?")) {
        Print-Info "Docker images NOT removed"
        return
    }

    foreach ($image in $kathImages) {
        try {
            docker rmi $image 2>$null
            Print-Success "Removed $image"
        }
        catch {
            Print-Warning "Failed to remove $image (may be in use)"
        }
    }

    # Clean dangling images
    try {
        $danglingCount = @(docker images -f "dangling=true" -q 2>$null).Count
        if ($danglingCount -gt 0) {
            Print-Info "Found $danglingCount dangling images"
            if (Confirm-Action "Remove dangling images?") {
                docker image prune -f --filter "dangling=true" 2>$null
                Print-Success "Removed dangling images"
            }
        }
    }
    catch {
        # Silently ignore errors
    }
}

# Generate cleanup summary
function Show-Summary {
    Print-Header "Cleanup Summary"
    Write-Host "The following items were cleaned:"
    Write-Host "  ✓ Python caches (__pycache__, .pytest_cache, .mypy_cache)"
    Write-Host "  ✓ Compiled Python files (.pyc, .pyo)"
    Write-Host "  ✓ Node.js cache (node_modules)"
    Write-Host "  ✓ Build artifacts (dist, build, htmlcov)"
    Write-Host "  ✓ Log files"
    Write-Host "  ✓ Temporary files (.DS_Store, *.swp, etc.)"

    if ($Docker) {
        Write-Host "  ✓ Docker images (if confirmed)"
    }

    Write-Host ""
    Print-Success "Cleanup complete!"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. npm install (in app\front_end)"
    Write-Host "  2. .\build-kath-complete.ps1 [-Full]"
    Write-Host ""
}

# Main execution
function Main {
    if ($Help) {
        Show-Help
        exit 0
    }

    Print-Header "KATH Project Cleanup"

    if (-not (Confirm-Action "This will clean build artifacts and caches. Continue?")) {
        Print-Info "Cleanup cancelled"
        exit 0
    }

    Write-Host ""
    Clean-Python
    Write-Host ""
    Clean-NodeJS
    Write-Host ""
    Clean-Artifacts
    Write-Host ""
    Clean-Logs
    Write-Host ""
    Clean-Temp

    if ($Docker) {
        Write-Host ""
        Clean-Docker
    }

    Show-Summary
}

Main
