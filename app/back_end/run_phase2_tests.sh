#!/bin/bash

################################################################################
# Phase 2 Test Suite Runner Script
#
# This script runs the comprehensive Phase 2 test suite with various options
# for different testing needs.
#
# Usage:
#   ./run_phase2_tests.sh [option]
#
# Options:
#   all       - Run all Phase 2 tests (default)
#   unit      - Run only unit tests
#   integration - Run only integration tests
#   smoke     - Run only smoke tests
#   sanity    - Run only sanity tests
#   system    - Run only system integration tests
#   api       - Run only API endpoint tests
#   failed    - Run only previously failed tests
#   coverage  - Run all tests with coverage report
#   quick     - Run tests in parallel (fastest)
#   verbose   - Run with maximum verbosity
#   help      - Show this help message
#
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default option
OPTION="${1:-all}"

# Test directories
UNIT_TESTS="tests/unit/test_phase2*.py"
INTEGRATION_TESTS="tests/test_phase2_integration.py"
SMOKE_SANITY_TESTS="tests/test_phase2_smoke_sanity.py"
SYSTEM_TESTS="tests/test_phase2_system_integration.py"
API_TESTS="tests/integration/test_phase2_api_endpoints.py"

# Common pytest options
COMMON_OPTS="--tb=short -v"

print_header() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

show_help() {
    cat << 'HELP'
Phase 2 Test Suite Runner

Usage: ./run_phase2_tests.sh [option]

Available Options:
  all         Run all Phase 2 tests (default)
  unit        Run only unit tests
  integration Run only integration tests
  smoke       Run only smoke tests
  sanity      Run only sanity tests
  system      Run only system integration tests
  api         Run only API endpoint tests
  failed      Run only previously failed tests (requires pytest cache)
  coverage    Run all tests with coverage report
  quick       Run tests in parallel (requires pytest-xdist)
  verbose     Run with maximum verbosity
  help        Show this help message

Examples:
  ./run_phase2_tests.sh all          # Run everything
  ./run_phase2_tests.sh unit         # Run unit tests only
  ./run_phase2_tests.sh coverage     # Run with coverage report
  ./run_phase2_tests.sh quick        # Run tests in parallel

Notes:
  - Tests require pytest and all dependencies installed
  - Coverage reports are saved to htmlcov/ directory
  - Failed tests cache is maintained in .pytest_cache/
HELP
}

run_all_tests() {
    print_header "Running ALL Phase 2 Tests"
    python3 -m pytest \
        $UNIT_TESTS \
        $INTEGRATION_TESTS \
        $SMOKE_SANITY_TESTS \
        $SYSTEM_TESTS \
        $API_TESTS \
        $COMMON_OPTS
}

run_unit_tests() {
    print_header "Running UNIT Tests"
    python3 -m pytest $UNIT_TESTS $COMMON_OPTS
}

run_integration_tests() {
    print_header "Running INTEGRATION Tests"
    python3 -m pytest $INTEGRATION_TESTS $COMMON_OPTS
}

run_smoke_tests() {
    print_header "Running SMOKE Tests"
    python3 -m pytest $SMOKE_SANITY_TESTS -m smoke $COMMON_OPTS
}

run_sanity_tests() {
    print_header "Running SANITY Tests"
    python3 -m pytest $SMOKE_SANITY_TESTS -m sanity $COMMON_OPTS
}

run_system_tests() {
    print_header "Running SYSTEM Tests"
    python3 -m pytest $SYSTEM_TESTS $COMMON_OPTS
}

run_api_tests() {
    print_header "Running API ENDPOINT Tests"
    python3 -m pytest $API_TESTS $COMMON_OPTS
}

run_failed_tests() {
    print_header "Running FAILED Tests (from cache)"
    python3 -m pytest --lf $COMMON_OPTS \
        $UNIT_TESTS \
        $INTEGRATION_TESTS \
        $SMOKE_SANITY_TESTS \
        $SYSTEM_TESTS \
        $API_TESTS
}

run_coverage_tests() {
    print_header "Running ALL Tests with COVERAGE Report"
    python3 -m pytest \
        $UNIT_TESTS \
        $INTEGRATION_TESTS \
        $SMOKE_SANITY_TESTS \
        $SYSTEM_TESTS \
        $API_TESTS \
        --cov=src \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-branch \
        $COMMON_OPTS
    print_success "Coverage report generated in htmlcov/index.html"
}

run_quick_tests() {
    print_header "Running Tests in PARALLEL (quick mode)"
    print_info "This requires pytest-xdist to be installed"
    python3 -m pytest \
        $UNIT_TESTS \
        $INTEGRATION_TESTS \
        $SMOKE_SANITY_TESTS \
        $SYSTEM_TESTS \
        $API_TESTS \
        -n auto \
        $COMMON_OPTS
}

run_verbose_tests() {
    print_header "Running ALL Tests with MAXIMUM Verbosity"
    python3 -m pytest \
        $UNIT_TESTS \
        $INTEGRATION_TESTS \
        $SMOKE_SANITY_TESTS \
        $SYSTEM_TESTS \
        $API_TESTS \
        -vv \
        --tb=long \
        --showlocals
}

# Main script logic
case "$OPTION" in
    all)
        run_all_tests
        ;;
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    smoke)
        run_smoke_tests
        ;;
    sanity)
        run_sanity_tests
        ;;
    system)
        run_system_tests
        ;;
    api)
        run_api_tests
        ;;
    failed)
        run_failed_tests
        ;;
    coverage)
        run_coverage_tests
        ;;
    quick)
        run_quick_tests
        ;;
    verbose)
        run_verbose_tests
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown option: $OPTION"
        echo ""
        show_help
        exit 1
        ;;
esac

# Print summary
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    print_success "Test execution completed successfully"
else
    print_error "Test execution failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
