#!/usr/bin/env bash

# KATH Backend Test Runner
# This script provides convenient commands to run pytest with various configurations

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "  KATH Backend Test Runner"
    echo "=========================================="
    echo ""
}

# Check if virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Virtual environment not activated"

        # Try multiple common virtual environment locations
        if [[ -d "venv" ]]; then
            print_info "Activating virtual environment (venv)..."
            source venv/bin/activate
        elif [[ -d ".venv" ]]; then
            print_info "Activating virtual environment (.venv)..."
            source .venv/bin/activate
        elif [[ -d "../../.venv" ]]; then
            print_info "Activating virtual environment (../../.venv)..."
            source ../../.venv/bin/activate
        else
            print_error "Virtual environment not found. Please create one:"
            echo "  python3 -m venv venv"
            echo "  source venv/bin/activate"
            echo "  pip install -r requirements.txt requirements_dev.txt"
            exit 1
        fi
    else
        print_success "Virtual environment active: $VIRTUAL_ENV"
    fi
}

# Check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Installing test dependencies..."
        pip install -r requirements_dev.txt
    fi
}

# Show usage
show_usage() {
    cat << EOF
Usage: ./run_tests.sh [COMMAND] [OPTIONS]

Commands:
  all               Run all tests (default)
  unit              Run unit tests only
  integration       Run integration tests only
  fast              Run fast tests (exclude slow tests)
  tools             Run DNA tool tests
  data              Run data processing tests
  routes            Run API route tests
  coverage          Run tests with coverage report
  coverage-html     Generate HTML coverage report
  watch             Run tests in watch mode (requires pytest-watch)
  parallel          Run tests in parallel
  verbose           Run tests with verbose output
  failed            Re-run only failed tests from last run
  specific FILE     Run specific test file
  help              Show this help message

Examples:
  ./run_tests.sh                    # Run all tests
  ./run_tests.sh unit               # Run unit tests only
  ./run_tests.sh coverage           # Run with coverage
  ./run_tests.sh specific tests/unit/test_logging.py
  ./run_tests.sh parallel           # Run tests in parallel
  ./run_tests.sh verbose            # Verbose output

Options (can be combined):
  -v, --verbose     Verbose output
  -s, --stdout      Show print statements
  -x, --exitfirst   Stop on first failure
  -k EXPRESSION     Run tests matching expression
  --pdb             Drop into debugger on failure
  --lf              Run last failed tests
  --ff              Run failed tests first

EOF
}

# Run all tests
run_all_tests() {
    print_info "Running all tests..."
    pytest "$@"
}

# Run unit tests
run_unit_tests() {
    print_info "Running unit tests..."
    pytest -m unit "$@"
}

# Run integration tests
run_integration_tests() {
    print_info "Running integration tests..."
    pytest -m integration "$@"
}

# Run fast tests (exclude slow)
run_fast_tests() {
    print_info "Running fast tests (excluding slow tests)..."
    pytest -m "not slow" "$@"
}

# Run tool tests
run_tool_tests() {
    print_info "Running DNA analysis tool tests..."
    pytest -m tools "$@"
}

# Run data processing tests
run_data_tests() {
    print_info "Running data processing tests..."
    pytest -m data "$@"
}

# Run API route tests
run_route_tests() {
    print_info "Running API route tests..."
    pytest -m routes "$@"
}

# Run tests with coverage
run_coverage() {
    print_info "Running tests with coverage..."
    pytest --cov=src --cov-report=term-missing --cov-report=html "$@"

    if [[ $? -eq 0 ]]; then
        print_success "Tests completed! Coverage report generated."
        print_info "View HTML report: open htmlcov/index.html"
    fi
}

# Run tests with HTML coverage only
run_coverage_html() {
    print_info "Running tests with HTML coverage report..."
    pytest --cov=src --cov-report=html "$@"

    if [[ $? -eq 0 ]]; then
        print_success "Tests completed! Opening coverage report..."

        # Open coverage report based on OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open htmlcov/index.html
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v xdg-open &> /dev/null; then
                xdg-open htmlcov/index.html
            fi
        fi
    fi
}

# Run tests in parallel
run_parallel() {
    print_info "Running tests in parallel..."

    if ! pytest --version | grep -q "pytest-xdist"; then
        print_warning "pytest-xdist not installed. Installing..."
        pip install pytest-xdist
    fi

    pytest -n auto "$@"
}

# Run tests with verbose output
run_verbose() {
    print_info "Running tests with verbose output..."
    pytest -vv "$@"
}

# Run only failed tests from last run
run_failed() {
    print_info "Re-running failed tests from last run..."
    pytest --lf "$@"
}

# Run specific test file
run_specific() {
    local test_file="$1"
    shift

    if [[ ! -f "$test_file" ]]; then
        print_error "Test file not found: $test_file"
        exit 1
    fi

    print_info "Running specific test file: $test_file"
    pytest "$test_file" "$@"
}

# Watch mode (requires pytest-watch)
run_watch() {
    print_info "Running tests in watch mode..."

    if ! command -v ptw &> /dev/null; then
        print_warning "pytest-watch not installed. Installing..."
        pip install pytest-watch
    fi

    print_info "Watching for file changes (Ctrl+C to stop)..."
    ptw -- "$@"
}

# Clean test artifacts
clean_artifacts() {
    print_info "Cleaning test artifacts..."

    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf __pycache__
    find tests -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find tests -type d -name "*.pyc" -delete 2>/dev/null || true

    print_success "Test artifacts cleaned"
}

# Check test environment
check_environment() {
    print_header
    print_info "Checking test environment..."

    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python version: $python_version"

    # Check pytest version
    if command -v pytest &> /dev/null; then
        pytest_version=$(pytest --version 2>&1 | head -n 1)
        print_info "Pytest: $pytest_version"
    else
        print_warning "Pytest not installed"
    fi

    # Check if Redis is running (for integration tests)
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis is running (required for integration tests)"
        else
            print_warning "Redis not running (some integration tests may fail)"
            print_info "Start Redis: redis-server"
        fi
    else
        print_warning "Redis not installed (some integration tests may fail)"
    fi

    # Check test directory structure
    if [[ -d "tests" ]]; then
        test_count=$(find tests -name "test_*.py" | wc -l)
        print_info "Found $test_count test files"
    else
        print_error "tests/ directory not found"
        exit 1
    fi

    echo ""
}

# Main script logic
main() {
    # Check environment first
    check_venv
    check_pytest

    # Parse command
    COMMAND="${1:-all}"

    # Remove first argument if it exists
    if [ $# -gt 0 ]; then
        shift
    fi

    case "$COMMAND" in
        all)
            print_header
            run_all_tests "$@"
            ;;
        unit)
            print_header
            run_unit_tests "$@"
            ;;
        integration)
            print_header
            run_integration_tests "$@"
            ;;
        fast)
            print_header
            run_fast_tests "$@"
            ;;
        tools)
            print_header
            run_tool_tests "$@"
            ;;
        data)
            print_header
            run_data_tests "$@"
            ;;
        routes)
            print_header
            run_route_tests "$@"
            ;;
        coverage)
            print_header
            run_coverage "$@"
            ;;
        coverage-html)
            print_header
            run_coverage_html "$@"
            ;;
        parallel)
            print_header
            run_parallel "$@"
            ;;
        verbose)
            print_header
            run_verbose "$@"
            ;;
        failed)
            print_header
            run_failed "$@"
            ;;
        watch)
            print_header
            run_watch "$@"
            ;;
        specific)
            print_header
            if [[ -z "$1" ]]; then
                print_error "Please provide a test file path"
                echo "Example: ./run_tests.sh specific tests/unit/test_logging.py"
                exit 1
            fi
            run_specific "$@"
            ;;
        clean)
            print_header
            clean_artifacts
            ;;
        check)
            check_environment
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        echo ""
        print_success "All tests passed! "
    else
        echo ""
        print_error "Some tests failed! "
    fi

    exit $exit_code
}

# Run main function
main "$@"
