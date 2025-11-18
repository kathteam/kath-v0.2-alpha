@echo off
REM KATH Initialization Script for Windows
REM This script automates the setup and launch of the KATH genetic analysis tool

setlocal enabledelayedexpansion

set KATH_IMAGE=cpu64/kath:latest
set CONTAINER_NAME=kath
set FRONTEND_PORT=5173
set BACKEND_PORT=8080
set SCRIPT_DIR=%~dp0
set WORKSPACE_DIR=%SCRIPT_DIR%data
set DATABASE_DIR=%SCRIPT_DIR%database
set WORKSPACE_UUID=default

echo.
echo ==========================================
echo   KATH Genetic Analysis Tool
echo   Version: v0.2-alpha
echo ==========================================
echo.

REM Check if Docker is installed
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    echo After installation, restart your computer and run this script again.
    pause
    exit /b 1
)

echo [INFO] Docker is installed

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker is not running
    echo [INFO] Starting Docker Desktop...

    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

    echo [INFO] Waiting for Docker to start (this may take 30-60 seconds)...
    timeout /t 10 /nobreak >nul

    set MAX_ATTEMPTS=60
    set ATTEMPT=0

    :wait_docker
    docker info >nul 2>&1
    if %errorlevel% equ 0 goto docker_ready

    set /a ATTEMPT+=1
    if !ATTEMPT! geq !MAX_ATTEMPTS! (
        echo [ERROR] Docker failed to start within 60 seconds
        echo Please start Docker Desktop manually and try again
        pause
        exit /b 1
    )

    timeout /t 1 /nobreak >nul
    goto wait_docker

    :docker_ready
    echo [SUCCESS] Docker is running!
) else (
    echo [SUCCESS] Docker is running
)

REM Create workspace and database directories
if not exist "%WORKSPACE_DIR%" (
    echo [INFO] Creating workspace directory at %WORKSPACE_DIR%...
    mkdir "%WORKSPACE_DIR%"
    echo [SUCCESS] Workspace directory created
) else (
    echo [INFO] Workspace directory already exists: %WORKSPACE_DIR%
)

if not exist "%DATABASE_DIR%" (
    echo [INFO] Creating database directory at %DATABASE_DIR%...
    mkdir "%DATABASE_DIR%"
    echo [SUCCESS] Database directory created
) else (
    echo [INFO] Database directory already exists: %DATABASE_DIR%
)

REM Stop existing container if running
docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Stopping existing KATH container...
    docker stop %CONTAINER_NAME% >nul 2>&1
    docker rm %CONTAINER_NAME% >nul 2>&1
    echo [SUCCESS] Existing container removed
)

REM Pull Docker image
echo [INFO] Pulling KATH Docker image (this may take a few minutes)...
docker pull %KATH_IMAGE%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to pull Docker image
    pause
    exit /b 1
)
echo [SUCCESS] Docker image downloaded successfully

REM Open browser in background (delayed)
echo [INFO] Browser will open in 10 seconds...
start "" cmd /c "timeout /t 10 /nobreak >nul && start http://localhost:%FRONTEND_PORT%"

echo.
echo [SUCCESS] Starting KATH...
echo.
echo   Frontend URL: http://localhost:%FRONTEND_PORT%
echo   Backend API:  http://localhost:%BACKEND_PORT%
echo   Health Check: http://localhost:%BACKEND_PORT%/api/v1/monitoring/health
echo.
echo   Data Directories:
echo     Workspace:  %WORKSPACE_DIR%
echo     Database:   %DATABASE_DIR%
echo.
echo [INFO] Press Ctrl+C to stop KATH and exit
echo.

REM Run Docker container (interactive, auto-remove on exit)
docker run --name %CONTAINER_NAME% -v "%WORKSPACE_DIR%:/kath/app/back_end/src/workspace/%WORKSPACE_UUID%" -v "%DATABASE_DIR%:/kath/app/back_end/instance" -it --rm -p %BACKEND_PORT%:8080 -p %FRONTEND_PORT%:5173 -e DOMAIN=localhost -e USE_DATABASE_BACKEND=true -e DATABASE_PATH=instance/kath.db %KATH_IMAGE%

echo.
echo [SUCCESS] KATH stopped successfully
