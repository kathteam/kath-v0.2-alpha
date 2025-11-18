#!/bin/bash
# Run Phase 2 tests in parallel (fastest)

cd "$(dirname "$0")" || exit 1
./run_phase2_tests.sh quick
