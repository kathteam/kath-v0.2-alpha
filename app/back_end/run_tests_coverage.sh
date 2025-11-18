#!/bin/bash
# Run all Phase 2 tests with coverage report

cd "$(dirname "$0")" || exit 1
./run_phase2_tests.sh coverage
