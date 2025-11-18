@echo off
REM KATH Complete Docker Build Script for Windows
REM Builds both reference files and application images

setlocal enabledelayedexpansion

REM Configuration
set IMAGE_NAME=cpu64/kath
set FILES_IMAGE=%IMAGE_NAME%:files
set APP_IMAGE=%IMAGE_NAME%:latest
set BUILD_MODE=%1

REM Colors (Windows 10+ supports ANSI)
set "INFO=[94m[INFO][0m"
set "SUCCESS=[92m[SUCCESS][0m"
set "WARNING=[93m[WARNING][0m"
set "ERROR=[91m[ERROR][0m"

echo.
echo ==============================================
echo   KATH Complete Docker Build Script
echo ==============================================
echo.

REM Parse command line arguments
if "%BUILD_MODE%"=="--help" goto show_help
if "%BUILD_MODE%"=="-h" goto show_help
if "%BUILD_MODE%"=="help" goto show_help

REM Check if Docker is installed
echo %INFO% Checking Docker installation...
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo %SUCCESS% Docker is installed

REM Check if Docker is running
echo %INFO% Checking Docker daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Docker daemon is not running!
    echo.
    echo Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to start...
    timeout /t 10 >nul

    REM Wait up to 60 seconds for Docker to be ready
    set COUNTER=0
    :wait_docker
    docker info >nul 2>&1
    if %errorlevel% equ 0 goto docker_ready
    set /a COUNTER+=1
    if %COUNTER% geq 60 (
        echo %ERROR% Docker failed to start after 60 seconds
        pause
        exit /b 1
    )
    timeout /t 1 >nul
    goto wait_docker

    :docker_ready
    echo %SUCCESS% Docker is ready
)

echo %SUCCESS% Docker daemon is running
echo.

REM Determine build mode
if "%BUILD_MODE%"=="--full" goto build_full
if "%BUILD_MODE%"=="--app-only" goto build_app_only
if "%BUILD_MODE%"=="--files-only" goto build_files_only

REM Default: Check if files image exists
echo %INFO% Checking for reference files image...
docker inspect %FILES_IMAGE% >nul 2>&1
if %errorlevel% neq 0 (
    echo %WARNING% Reference files image not found
    echo %INFO% Will build complete system (reference files + application)
    goto build_full
) else (
    echo %SUCCESS% Reference files image found
    echo %INFO% Building application only
    goto build_app_only
)

:build_files_only
echo.
echo ============================================
echo   Building Reference Files Image
echo ============================================
echo.
echo %INFO% Building: %FILES_IMAGE%
echo %INFO% This will download ~2GB of reference data
echo %INFO% Expected time: 10-20 minutes
echo.

set DOCKER_BUILDKIT=1
docker build ^
    -t %FILES_IMAGE% ^
    -f app\Dockerfile.files ^
    --progress=plain ^
    app\

if %errorlevel% neq 0 (
    echo.
    echo %ERROR% Reference files build failed!
    pause
    exit /b 1
)

echo.
echo %SUCCESS% Reference files image built successfully!
docker images | findstr "%IMAGE_NAME%"
echo.
goto end

:build_app_only
echo.
echo ============================================
echo   Building Application Image
echo ============================================
echo.
echo %INFO% Building: %APP_IMAGE%
echo %INFO% Expected time: 5-15 minutes
echo.

set DOCKER_BUILDKIT=1
docker build ^
    -t %APP_IMAGE% ^
    -f app\Dockerfile ^
    --progress=plain ^
    app\

if %errorlevel% neq 0 (
    echo.
    echo %ERROR% Application build failed!
    pause
    exit /b 1
)

echo.
echo %SUCCESS% Application image built successfully!
docker images | findstr "%IMAGE_NAME%"
echo.
echo %SUCCESS% Build complete!
echo.
goto show_next_steps

:build_full
echo.
echo ============================================
echo   Building Complete KATH System
echo ============================================
echo.
echo %INFO% This will build:
echo   1. Reference files image (with hg38.fa, REVEL database)
echo   2. Application image (with Python backend and Node.js frontend)
echo.
echo %INFO% Total expected time: 15-30 minutes
echo %INFO% Total download size: ~2GB
echo.

REM Build reference files first
echo.
echo --- Stage 1/2: Reference Files ---
echo.
echo %INFO% Building: %FILES_IMAGE%
echo.

set DOCKER_BUILDKIT=1
docker build ^
    -t %FILES_IMAGE% ^
    -f app\Dockerfile.files ^
    --progress=plain ^
    app\

if %errorlevel% neq 0 (
    echo.
    echo %ERROR% Reference files build failed!
    pause
    exit /b 1
)

echo.
echo %SUCCESS% Reference files image built successfully!
echo.

REM Build application
echo.
echo --- Stage 2/2: Application ---
echo.
echo %INFO% Building: %APP_IMAGE%
echo.

docker build ^
    -t %APP_IMAGE% ^
    -f app\Dockerfile ^
    --progress=plain ^
    app\

if %errorlevel% neq 0 (
    echo.
    echo %ERROR% Application build failed!
    pause
    exit /b 1
)

echo.
echo %SUCCESS% Application image built successfully!
echo.

REM Show all images
echo %INFO% Built images:
docker images | findstr "%IMAGE_NAME%"
echo.

REM Show image details
echo %INFO% Image details:
for /f "tokens=*" %%i in ('docker inspect %APP_IMAGE% --format^="Size: {{.Size}} bytes"') do echo   %%i
for /f "tokens=*" %%i in ('docker inspect %APP_IMAGE% --format^="Created: {{.Created}}"') do echo   %%i
echo.

echo %SUCCESS% Complete build finished!
echo.

:show_next_steps
echo ==============================================
echo   Next Steps
echo ==============================================
echo.
echo To run KATH, use:
echo   - start-kath.bat          (Windows batch script)
echo   - docker-compose up       (Docker Compose)
echo.
echo To access KATH:
echo   - Frontend: http://localhost:5173
echo   - Backend:  http://localhost:8080
echo   - Health:   http://localhost:8080/api/v1/monitoring/health
echo.
echo To clean up old images:
echo   - docker system prune -af
echo.
goto end

:show_help
echo.
echo KATH Complete Docker Build Script
echo.
echo Usage:
echo   build-kath-complete.bat [OPTIONS]
echo.
echo Options:
echo   --full         Build both reference files and application images
echo   --app-only     Build only the application image (requires files image)
echo   --files-only   Build only the reference files image
echo   --help, -h     Show this help message
echo.
echo Default behavior:
echo   If reference files image exists: build application only
echo   If reference files image missing: build complete system
echo.
echo Examples:
echo   build-kath-complete.bat              (smart build)
echo   build-kath-complete.bat --full       (rebuild everything)
echo   build-kath-complete.bat --app-only   (quick rebuild)
echo.

:end
pause
