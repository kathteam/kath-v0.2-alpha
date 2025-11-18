# Phase 2 Test Suite Runner Guide

This guide explains how to use the comprehensive Phase 2 test runner scripts to execute the 204-test suite that validates the Phase 2 database-driven variant analysis platform.

## Quick Start

### Run All Tests
```bash
cd app/back_end
./run_phase2_tests.sh all
```

### Run Only Unit Tests
```bash
./run_unit_tests.sh
```

### Run With Coverage Report
```bash
./run_tests_coverage.sh
```

### Run Tests in Parallel (Fastest)
```bash
./run_tests_quick.sh
```

---

## Main Test Runner Script

**File:** `run_phase2_tests.sh`

### Syntax
```bash
./run_phase2_tests.sh [option]
```

### Available Options

#### `all` (default)
Runs all 204 Phase 2 tests across all categories.

```bash
./run_phase2_tests.sh all
```

**What it tests:**
- Unit tests (92 tests)
- Integration tests (27 tests)
- Smoke & Sanity tests (35 tests)
- System tests (15 tests)
- API endpoint tests (50 tests)

**Expected Result:** ~139 passing, ~65 failing (as of current implementation)

---

#### `unit`
Runs only unit tests for Phase 2 modules.

```bash
./run_phase2_tests.sh unit
```

**Test Files:**
- `tests/unit/test_phase2_delta_sync.py` (25 tests)
- `tests/unit/test_phase2_merge_operations.py` (29 tests)
- `tests/unit/test_phase2_quality_filtering.py` (38 tests)

**Expected Result:** ~76 passing, ~19 failing

**Execution Time:** ~1 second

---

#### `integration`
Runs integration tests validating complete workflows.

```bash
./run_phase2_tests.sh integration
```

**Test File:** `tests/test_phase2_integration.py` (27 tests)

**Coverage:**
- Delta-sync workflows
- Merge operations
- Quality filtering
- Analysis integration
- Repository operations
- Complete pipelines

**Expected Result:** 27/27 passing (100%)

**Execution Time:** ~1 second

---

#### `smoke`
Runs smoke tests for critical paths and system health.

```bash
./run_phase2_tests.sh smoke
```

**From:** `tests/test_phase2_smoke_sanity.py` (~28 tests)

**Coverage:**
- Critical functionality paths
- Component instantiation
- System health checks
- Module importability

**Expected Result:** ~26 passing, 0-2 failing

**Execution Time:** ~0.5 seconds

---

#### `sanity`
Runs sanity tests for basic functionality.

```bash
./run_phase2_tests.sh sanity
```

**From:** `tests/test_phase2_smoke_sanity.py` (~7 tests)

**Coverage:**
- Model creation
- Basic configurations
- Threshold validation
- Data structure creation

**Expected Result:** ~5 passing, ~2 failing

**Execution Time:** ~0.5 seconds

---

#### `system`
Runs system integration tests.

```bash
./run_phase2_tests.sh system
```

**Test File:** `tests/test_phase2_system_integration.py` (15 tests)

**Coverage:**
- Delta-sync system workflows
- Merge system workflows
- Filtering system workflows
- Analysis system workflows
- Complete end-to-end pipelines
- Repository integration

**Expected Result:** ~12 passing, ~3 failing

**Execution Time:** ~1 second

---

#### `api`
Runs API endpoint tests.

```bash
./run_phase2_tests.sh api
```

**Test File:** `tests/integration/test_phase2_api_endpoints.py` (50 tests)

**Coverage:**
- Delta-sync endpoints (4 tests)
- Merge endpoints (7 tests)
- Filtering endpoints (4 tests)
- Analysis endpoints (7 tests)
- Data query endpoints (6 tests)
- Audit trail endpoints (2 tests)
- Health check endpoint (2 tests)
- Response formats (3 tests)
- Error handling (4 tests)
- Integration workflows (2 tests)

**Current Status:** API routing issues (0/50 passing)

**Note:** See PHASE2_TEST_EXECUTION_REPORT.md for routing issue details.

**Execution Time:** ~1 second

---

#### `coverage`
Runs all tests with code coverage analysis.

```bash
./run_phase2_tests.sh coverage
```

**Features:**
- Line coverage analysis
- Branch coverage analysis
- Missing line identification
- HTML coverage report generation

**Output:** 
- Terminal report with missing coverage
- `htmlcov/index.html` - interactive coverage report

**Expected Result:** ~95% coverage

**Execution Time:** ~5 seconds

---

#### `quick`
Runs all tests in parallel (requires pytest-xdist).

```bash
./run_phase2_tests.sh quick
```

**Features:**
- Parallel test execution
- Automatic CPU detection
- Faster execution than sequential

**Requirements:** `pytest-xdist` package installed

**Execution Time:** ~2-3 seconds (vs 5 seconds sequential)

---

#### `failed`
Runs only previously failed tests.

```bash
./run_phase2_tests.sh failed
```

**Purpose:**
- Debug recently failing tests
- Verify test fixes
- Iterative test development

**Requirements:** Pytest cache must exist (from previous run)

---

#### `verbose`
Runs all tests with maximum verbosity.

```bash
./run_phase2_tests.sh verbose
```

**Features:**
- Maximum verbosity (-vv)
- Long tracebacks (--tb=long)
- Local variable printing (--showlocals)

**Purpose:** Detailed debugging of test failures

**Execution Time:** ~10 seconds

---

#### `help`
Displays help information.

```bash
./run_phase2_tests.sh help
```

Shows usage, options, examples, and notes.

---

## Helper Scripts

### `run_unit_tests.sh`
Shortcut for running unit tests only.

```bash
./run_unit_tests.sh
```

Equivalent to: `./run_phase2_tests.sh unit`

---

### `run_tests_coverage.sh`
Shortcut for running all tests with coverage.

```bash
./run_tests_coverage.sh
```

Equivalent to: `./run_phase2_tests.sh coverage`

---

### `run_tests_quick.sh`
Shortcut for running tests in parallel.

```bash
./run_tests_quick.sh
```

Equivalent to: `./run_phase2_tests.sh quick`

---

## Understanding Test Results

### Test Output Format

```
tests/unit/test_phase2_delta_sync.py::TestDeltaSyncManagerInitialization::test_initialization_with_session PASSED [  0%]
```

**Components:**
- `tests/unit/test_phase2_delta_sync.py` - Test file
- `TestDeltaSyncManagerInitialization` - Test class
- `test_initialization_with_session` - Test method
- `PASSED` - Result (PASSED or FAILED)
- `[  0%]` - Progress percentage

### Summary Line

```
================== 139 passed, 65 failed, 1 warning in 4.77s ====================
```

**Interpretation:**
- 139 tests passed
- 65 tests failed
- 1 warning issued
- Total execution time: 4.77 seconds

---

## Coverage Report

After running with coverage:

```bash
./run_tests_coverage.sh
```

Coverage report is generated in `htmlcov/index.html`

Open in browser:
```bash
open htmlcov/index.html        # macOS
xdg-open htmlcov/index.html    # Linux
start htmlcov/index.html       # Windows
```

### Coverage Metrics

- **Line Coverage:** % of code lines executed
- **Branch Coverage:** % of conditional branches taken
- **Missing Lines:** Lines not covered by tests

**Target:** >90% coverage for Phase 2 modules

---

## Common Workflows

### 1. Validate Core Functionality
```bash
./run_phase2_tests.sh integration
```
Fastest way to verify core functionality (100% passing)

### 2. Debug Failing Tests
```bash
./run_phase2_tests.sh failed  # Run only failed tests
# or
./run_phase2_tests.sh verbose # Maximum detail
```

### 3. Check Coverage Before Commit
```bash
./run_tests_coverage.sh
# Review htmlcov/index.html in browser
```

### 4. Quick Validation During Development
```bash
./run_phase2_tests.sh unit  # Fast unit test validation
```

### 5. Full Test Suite for CI/CD
```bash
./run_phase2_tests.sh quick  # Parallel execution
# or
./run_tests_coverage.sh      # With coverage metrics
```

---

## Troubleshooting

### Tests Can't Find Dependencies

**Error:** `ModuleNotFoundError: No module named 'pytest'`

**Solution:**
```bash
pip install -r requirements.txt -r requirements_dev.txt --break-system-packages
```

### Pre-commit Hook Issues

**Error:** ``pre-commit` not found`

**Note:** This is expected. The test scripts work correctly despite this message.

### Flask Test Client 404 Errors

**Symptom:** All API endpoint tests fail with 404

**Status:** Known issue documented in PHASE2_TEST_EXECUTION_REPORT.md

**Workaround:** Focus on unit and integration tests for now

### Coverage Report Not Generated

**Check:**
1. Verify `htmlcov/` directory exists
2. Check file permissions
3. Ensure pytest-cov is installed

---

## Test Statistics

### Total Tests: 204

| Category | Count | Pass Rate | Time |
|----------|-------|-----------|------|
| Unit | 92 | 80% | ~1s |
| Integration | 27 | 100% | ~1s |
| Smoke/Sanity | 35 | 94% | ~1s |
| System | 15 | 80% | ~1s |
| API | 50 | 0%* | ~1s |
| **Total** | **204** | **68%** | **~5s** |

*API tests have routing issues documented in execution report

---

## Best Practices

1. **Run unit tests frequently** during development
   ```bash
   ./run_unit_tests.sh
   ```

2. **Run integration tests** before commits
   ```bash
   ./run_phase2_tests.sh integration
   ```

3. **Generate coverage** before submitting PRs
   ```bash
   ./run_tests_coverage.sh
   ```

4. **Use quick mode** for CI/CD pipelines
   ```bash
   ./run_phase2_tests.sh quick
   ```

5. **Document test failures** in issue reports
   ```bash
   ./run_phase2_tests.sh verbose > test_output.log
   ```

---

## Additional Resources

- **PHASE2_TEST_EXECUTION_REPORT.md** - Detailed test results and failure analysis
- **PHASE2_COMPREHENSIVE_TEST_PLAN.md** - Complete test documentation
- **pytest.ini** - Pytest configuration

---

## Questions?

Refer to the test execution reports for:
- Detailed failure analysis
- Root cause identification
- Recommended fixes
- Coverage metrics

Generated: November 17, 2024
Test Suite Version: 1.0
