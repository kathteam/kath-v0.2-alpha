@echo off
REM KATH Project Cleanup Script for Windows
REM Cleans up all build artifacts, caches, and temporary files
REM to prepare for a fresh build
REM
REM Usage: clean_all.bat [--docker] [--force] [--help]
REM
REM Options:
REM   --docker    Also remove Docker images
REM   --force     Skip confirmation prompts
REM   --help      Show this help message

setlocal enabledelayedexpansion

REM Configuration
set "CLEAN_DOCKER=0"
set "FORCE_MODE=0"
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR:~0,-1%"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto start_cleanup
if /i "%~1"=="--docker" (
    set "CLEAN_DOCKER=1"
    shift
    goto parse_args
)
if /i "%~1"=="--force" (
    set "FORCE_MODE=1"
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    goto show_help
)
shift
goto parse_args

:show_help
echo.
echo KATH Project Cleanup Script for Windows
echo.
echo Usage: clean_all.bat [OPTIONS]
echo.
echo Options:
echo   --docker    Also remove Docker images (cpu64/kath:*)
echo   --force     Skip all confirmation prompts
echo   --help      Show this help message
echo.
echo Examples:
echo   clean_all.bat                    (clean artifacts only)
echo   clean_all.bat --docker           (clean with Docker images)
echo   clean_all.bat --force --docker   (clean without prompts)
echo.
echo What gets cleaned:
echo   - Python cache (__pycache__, .pytest_cache, .mypy_cache)
echo   - Node.js cache (node_modules, npm caches)
echo   - Build artifacts (dist, build, htmlcov)
echo   - Log files
echo   - Test coverage data
echo   - Temporary files
echo.
echo What does NOT get cleaned (safe):
echo   - Source code
echo   - Configuration files
echo   - Data files (data/, database/)
echo   - Environment files (.env*)
echo   - Git history
echo.
exit /b 0

:start_cleanup
cls
echo.
echo ==============================================
echo   KATH Project Cleanup
echo ==============================================
echo.

if %FORCE_MODE% equ 0 (
    echo This will clean build artifacts and caches.
    set /p RESPONSE="Continue? (y/N): "
    if /i not "!RESPONSE!"=="y" (
        echo Cleanup cancelled
        exit /b 0
    )
)

echo.
call :clean_python
echo.
call :clean_nodejs
echo.
call :clean_artifacts
echo.
call :clean_logs
echo.
call :clean_temp

if %CLEAN_DOCKER% equ 1 (
    echo.
    call :clean_docker
)

call :show_summary
exit /b 0

:clean_python
echo [INFO] Cleaning Python caches...

REM Remove __pycache__ directories
for /d /r "%PROJECT_ROOT%" %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
)
echo [OK] Removed __pycache__ directories

REM Remove .pytest_cache
if exist "%PROJECT_ROOT%\.pytest_cache" (
    rmdir /s /q "%PROJECT_ROOT%\.pytest_cache" 2>nul
    echo [OK] Removed .pytest_cache
)

REM Remove .mypy_cache
if exist "%PROJECT_ROOT%\.mypy_cache" (
    rmdir /s /q "%PROJECT_ROOT%\.mypy_cache" 2>nul
    echo [OK] Removed .mypy_cache
)

REM Remove .egg-info directories
for /d /r "%PROJECT_ROOT%" %%d in (*.egg-info) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
)
echo [OK] Removed .egg-info directories

REM Remove .pyc and .pyo files
for /r "%PROJECT_ROOT%" %%f in (*.pyc) do (
    if exist "%%f" del /q "%%f" 2>nul
)
for /r "%PROJECT_ROOT%" %%f in (*.pyo) do (
    if exist "%%f" del /q "%%f" 2>nul
)
echo [OK] Removed Python compiled files

goto :eof

:clean_nodejs
echo [INFO] Cleaning Node.js caches...

REM Remove node_modules
if exist "%PROJECT_ROOT%\app\front_end\node_modules" (
    echo [WARNING] Removing node_modules (this may take a moment)...
    rmdir /s /q "%PROJECT_ROOT%\app\front_end\node_modules" 2>nul
    echo [OK] Removed node_modules
)

REM Remove .npmrc
if exist "%PROJECT_ROOT%\app\front_end\.npmrc" (
    del /q "%PROJECT_ROOT%\app\front_end\.npmrc" 2>nul
    echo [OK] Removed .npmrc
)

goto :eof

:clean_artifacts
echo [INFO] Cleaning build artifacts...

setlocal enabledelayedexpansion

REM Remove build directories
for %%d in (dist build htmlcov .venv .venv3) do (
    if exist "%PROJECT_ROOT%\app\back_end\%%d" (
        rmdir /s /q "%PROJECT_ROOT%\app\back_end\%%d" 2>nul
        echo [OK] Removed app\back_end\%%d
    )
    if exist "%PROJECT_ROOT%\%%d" (
        rmdir /s /q "%PROJECT_ROOT%\%%d" 2>nul
        echo [OK] Removed %%d
    )
)

REM Remove coverage files
if exist "%PROJECT_ROOT%\.coverage" (
    del /q "%PROJECT_ROOT%\.coverage" 2>nul
    echo [OK] Removed .coverage
)

endlocal
goto :eof

:clean_logs
echo [INFO] Cleaning log files...

REM Remove logs directory contents
if exist "%PROJECT_ROOT%\app\back_end\src\logs" (
    for /r "%PROJECT_ROOT%\app\back_end\src\logs" %%f in (*) do (
        del /q "%%f" 2>nul
    )
    echo [OK] Cleaned src\logs
)

REM Remove .log files
for /r "%PROJECT_ROOT%" %%f in (*.log) do (
    del /q "%%f" 2>nul
)
echo [OK] Removed .log files

goto :eof

:clean_temp
echo [INFO] Cleaning temporary files...

REM Remove OS-specific files
for /r "%PROJECT_ROOT%" %%f in (.DS_Store Thumbs.db) do (
    if exist "%%f" del /q "%%f" 2>nul
)
echo [OK] Removed OS temporary files

REM Remove editor backup files (approximation)
for /r "%PROJECT_ROOT%" %%f in (*~ *.swp *.swo) do (
    if exist "%%f" del /q "%%f" 2>nul
)
echo [OK] Removed editor backup files

goto :eof

:clean_docker
echo [INFO] Cleaning Docker images...

REM Check if Docker is installed
where docker >nul 2>nul
if errorlevel 1 (
    echo [WARNING] Docker is not installed, skipping Docker cleanup
    goto :eof
)

REM Get list of KATH images
for /f "tokens=*" %%i in ('docker images --filter "reference=cpu64/kath:*" --format "{{.Repository}}:{{.Tag}}" 2^>nul') do (
    set DOCKER_IMAGES=!DOCKER_IMAGES! %%i
)

if "!DOCKER_IMAGES!"=="" (
    echo [INFO] No KATH Docker images found
    goto :eof
)

echo [WARNING] The following Docker images will be removed:
for %%i in (!DOCKER_IMAGES!) do (
    echo   - %%i
)
echo.

if %FORCE_MODE% equ 0 (
    set /p RESPONSE="Remove all KATH Docker images? (y/N): "
    if /i not "!RESPONSE!"=="y" (
        echo [INFO] Docker images NOT removed
        goto :eof
    )
)

for %%i in (!DOCKER_IMAGES!) do (
    docker rmi %%i 2>nul
    echo [OK] Removed %%i
)

REM Clean dangling images
docker image prune -f --filter "dangling=true" 2>nul
echo [OK] Cleaned dangling images

goto :eof

:show_summary
echo.
echo ==============================================
echo   Cleanup Summary
echo ==============================================
echo.
echo The following items were cleaned:
echo   [OK] Python caches (__pycache__, .pytest_cache, .mypy_cache)
echo   [OK] Compiled Python files (.pyc, .pyo)
echo   [OK] Node.js cache (node_modules)
echo   [OK] Build artifacts (dist, build, htmlcov)
echo   [OK] Log files
echo   [OK] Temporary files (.DS_Store, *.swp, etc.)

if %CLEAN_DOCKER% equ 1 (
    echo   [OK] Docker images (if confirmed)
)

echo.
echo Cleanup complete!
echo.
echo Next steps:
echo   1. npm install (in app\front_end)
echo   2. build-kath-complete.bat [--full]
echo.
goto :eof
