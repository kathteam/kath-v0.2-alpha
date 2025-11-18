@echo off
REM KATH Backend Test Runner for Windows
REM This script provides convenient commands to run pytest with various configurations

setlocal enabledelayedexpansion

set COMMAND=%1
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Default to 'all' if no command provided
if "%COMMAND%"=="" set COMMAND=all

echo.
echo ==========================================
echo   KATH Backend Test Runner
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [WARNING] Virtual environment not found
    echo Please create one:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt requirements_dev.txt
    exit /b 1
)

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if pytest is installed
pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pytest not found. Installing test dependencies...
    pip install -r requirements_dev.txt
)

REM Parse command
if "%COMMAND%"=="all" goto run_all
if "%COMMAND%"=="unit" goto run_unit
if "%COMMAND%"=="integration" goto run_integration
if "%COMMAND%"=="fast" goto run_fast
if "%COMMAND%"=="tools" goto run_tools
if "%COMMAND%"=="data" goto run_data
if "%COMMAND%"=="routes" goto run_routes
if "%COMMAND%"=="coverage" goto run_coverage
if "%COMMAND%"=="coverage-html" goto run_coverage_html
if "%COMMAND%"=="parallel" goto run_parallel
if "%COMMAND%"=="verbose" goto run_verbose
if "%COMMAND%"=="failed" goto run_failed
if "%COMMAND%"=="clean" goto clean_artifacts
if "%COMMAND%"=="check" goto check_environment
if "%COMMAND%"=="help" goto show_usage
if "%COMMAND%"=="-h" goto show_usage
if "%COMMAND%"=="--help" goto show_usage

echo [ERROR] Unknown command: %COMMAND%
echo.
goto show_usage

:run_all
echo [INFO] Running all tests...
pytest
goto end

:run_unit
echo [INFO] Running unit tests...
pytest -m unit
goto end

:run_integration
echo [INFO] Running integration tests...
pytest -m integration
goto end

:run_fast
echo [INFO] Running fast tests (excluding slow tests)...
pytest -m "not slow"
goto end

:run_tools
echo [INFO] Running DNA analysis tool tests...
pytest -m tools
goto end

:run_data
echo [INFO] Running data processing tests...
pytest -m data
goto end

:run_routes
echo [INFO] Running API route tests...
pytest -m routes
goto end

:run_coverage
echo [INFO] Running tests with coverage...
pytest --cov=src --cov-report=term-missing --cov-report=html
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Tests completed! Coverage report generated.
    echo [INFO] View HTML report: htmlcov\index.html
)
goto end

:run_coverage_html
echo [INFO] Running tests with HTML coverage report...
pytest --cov=src --cov-report=html
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Tests completed! Opening coverage report...
    start htmlcov\index.html
)
goto end

:run_parallel
echo [INFO] Running tests in parallel...
pytest -n auto
goto end

:run_verbose
echo [INFO] Running tests with verbose output...
pytest -vv
goto end

:run_failed
echo [INFO] Re-running failed tests from last run...
pytest --lf
goto end

:clean_artifacts
echo [INFO] Cleaning test artifacts...
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist htmlcov rmdir /s /q htmlcov
if exist .coverage del /q .coverage
for /d /r tests %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo [SUCCESS] Test artifacts cleaned
goto end

:check_environment
echo [INFO] Checking test environment...
echo.

REM Check Python version
python --version

REM Check pytest version
pytest --version

REM Check Redis
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Redis is running
) else (
    echo [WARNING] Redis not running (some integration tests may fail)
    echo [INFO] Start Redis: redis-server
)

REM Count test files
set test_count=0
for /r tests %%f in (test_*.py) do set /a test_count+=1
echo [INFO] Found %test_count% test files

echo.
goto end

:show_usage
echo Usage: run_tests.bat [COMMAND]
echo.
echo Commands:
echo   all               Run all tests (default)
echo   unit              Run unit tests only
echo   integration       Run integration tests only
echo   fast              Run fast tests (exclude slow tests)
echo   tools             Run DNA tool tests
echo   data              Run data processing tests
echo   routes            Run API route tests
echo   coverage          Run tests with coverage report
echo   coverage-html     Generate HTML coverage report
echo   parallel          Run tests in parallel
echo   verbose           Run tests with verbose output
echo   failed            Re-run only failed tests from last run
echo   clean             Clean test artifacts
echo   check             Check test environment
echo   help              Show this help message
echo.
echo Examples:
echo   run_tests.bat                 # Run all tests
echo   run_tests.bat unit            # Run unit tests only
echo   run_tests.bat coverage        # Run with coverage
echo   run_tests.bat parallel        # Run tests in parallel
echo.
goto end

:end
echo.
if %errorlevel% equ 0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [ERROR] Some tests failed!
)

exit /b %errorlevel%
