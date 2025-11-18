#!/bin/bash
# Run only Phase 2 unit tests

cd "$(dirname "$0")" || exit 1
./run_phase2_tests.sh unit
