#!/usr/bin/env bash

# KATH Data Persistence Verification Script
# This script verifies that data persistence is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo "  KATH Data Persistence Verification"
    echo "=========================================="
    echo ""
}

verify_directories() {
    print_info "Checking data directories..."

    if [ -d "data" ]; then
        print_success "data/ directory exists"
        local data_size=$(du -sh data/ 2>/dev/null | cut -f1)
        print_info "  Size: $data_size"
        local data_files=$(find data -type f | wc -l)
        print_info "  Files: $data_files"
    else
        print_warning "data/ directory does not exist (will be created on first run)"
    fi

    echo ""

    if [ -d "database" ]; then
        print_success "database/ directory exists"
        local db_size=$(du -sh database/ 2>/dev/null | cut -f1)
        print_info "  Size: $db_size"
        if [ -f "database/kath.db" ]; then
            print_success "  kath.db database file exists"
            local db_file_size=$(ls -lh database/kath.db | awk '{print $5}')
            print_info "    Database size: $db_file_size"
        fi
    else
        print_warning "database/ directory does not exist (will be created on first run)"
    fi
}

verify_data_files() {
    print_info "Checking for analysis result files..."

    if [ ! -d "data" ]; then
        print_warning "data/ directory does not exist - skipping file check"
        return
    fi

    local csv_count=$(find data -maxdepth 1 -name "*.csv" -type f 2>/dev/null | wc -l)
    if [ "$csv_count" -gt 0 ]; then
        print_success "Found $csv_count CSV analysis files"
        find data -maxdepth 1 -name "*.csv" -type f 2>/dev/null | while read file; do
            local size=$(ls -lh "$file" | awk '{print $5}')
            local rows=$(wc -l < "$file" 2>/dev/null || echo "?")
            print_info "  $(basename $file) - Size: $size, Rows: $rows"
        done
    else
        print_warning "No CSV analysis files found (expected if this is first run)"
    fi

    echo ""

    # Check for analysis subdirectories
    local cadd_files=$(find data/cadd -type f 2>/dev/null | wc -l)
    if [ "$cadd_files" -gt 0 ]; then
        print_success "Found $cadd_files CADD analysis files"
    fi

    local spliceai_files=$(find data/spliceai -type f 2>/dev/null | wc -l)
    if [ "$spliceai_files" -gt 0 ]; then
        print_success "Found $spliceai_files SpliceAI analysis files"
    fi

    local lovd_dirs=$(find data -maxdepth 1 -name "lovd_*" -type d 2>/dev/null | wc -l)
    if [ "$lovd_dirs" -gt 0 ]; then
        print_success "Found $lovd_dirs LOVD database directories"
    fi
}

verify_directory_permissions() {
    print_info "Checking directory permissions..."

    if [ ! -d "data" ]; then
        print_warning "data/ directory does not exist - skipping permission check"
        return
    fi

    if [ -w "data" ]; then
        print_success "data/ directory is writable"
    else
        print_error "data/ directory is NOT writable - Docker may not be able to write data"
    fi

    if [ -w "database" ] 2>/dev/null; then
        print_success "database/ directory is writable"
    elif [ -d "database" ]; then
        print_error "database/ directory is NOT writable - Docker may not be able to write data"
    fi
}

verify_container_mounts() {
    print_info "Checking Docker container volume mounts..."

    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed or not in PATH - skipping container check"
        return
    fi

    if ! docker ps -a --format '{{.Names}}' | grep -q "^kath$"; then
        print_warning "KATH container is not currently running - unable to verify active mounts"
        print_info "  (Start KATH with ./start-kath.sh to verify mounts)"
        return
    fi

    print_info "Checking mounts in running container..."

    # Check workspace volume mount
    local workspace_mount=$(docker inspect kath 2>/dev/null | grep -A 20 "Mounts" | grep "workspace" || true)
    if [ -n "$workspace_mount" ]; then
        print_success "Workspace volume is mounted"
    else
        print_warning "Could not verify workspace mount"
    fi

    # Check instance volume mount (database)
    local instance_mount=$(docker inspect kath 2>/dev/null | grep -A 20 "Mounts" | grep "instance" || true)
    if [ -n "$instance_mount" ]; then
        print_success "Database volume is mounted"
    else
        print_warning "Could not verify database mount"
    fi
}

verify_volume_mount_paths() {
    print_info "Verifying Docker volume mount paths..."

    if ! command -v docker &> /dev/null; then
        print_warning "Docker not available - skipping path verification"
        return
    fi

    if ! docker ps -a --format '{{.Names}}' | grep -q "^kath$"; then
        print_warning "KATH container not running - cannot verify mount paths"
        return
    fi

    # Check if workspace files are accessible in container
    local container_data_count=$(docker exec kath find /kath/app/back_end/src/workspace/default -type f 2>/dev/null | wc -l || echo "0")
    if [ "$container_data_count" -gt 0 ]; then
        print_success "Container can access $container_data_count files in workspace"
    fi

    # Check database accessibility
    if docker exec kath [ -f /kath/app/back_end/instance/kath.db ] 2>/dev/null; then
        print_success "Container can access database file"
    fi
}

test_persistence_flow() {
    print_info "Testing persistence flow..."

    if [ ! -d "data" ]; then
        print_warning "data/ directory does not exist yet - cannot test persistence"
        print_info "  Run KATH with ./start-kath.sh to initialize directories"
        return
    fi

    # Create a test file
    local test_file="data/test_persistence_$(date +%s).txt"
    echo "Test file created at $(date)" > "$test_file"

    if [ -f "$test_file" ]; then
        print_success "Created test file: $(basename $test_file)"
        print_info "  This file should persist if you:"
        print_info "  1. Stop the container (Ctrl+C)"
        print_info "  2. Verify the file still exists: ls -l data/test_persistence_*"
        print_info "  3. Restart with ./start-kath.sh"
        print_info "  4. File should still be visible in the container"
    fi
}

generate_persistence_report() {
    print_info "Generating persistence report..."

    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local report_file="persistence_report_$timestamp.txt"

    {
        echo "KATH Data Persistence Report"
        echo "Generated: $(date)"
        echo ""
        echo "=== Directory Status ==="
        echo "data/ exists: $([ -d data ] && echo 'YES' || echo 'NO')"
        echo "database/ exists: $([ -d database ] && echo 'YES' || echo 'NO')"
        echo ""
        echo "=== Data Sizes ==="
        [ -d data ] && du -sh data/ || echo "data/ not found"
        [ -d database ] && du -sh database/ || echo "database/ not found"
        echo ""
        echo "=== File Count ==="
        [ -d data ] && echo "Files in data/: $(find data -type f 2>/dev/null | wc -l)" || echo "data/ not found"
        echo ""
        echo "=== CSV Files ==="
        [ -d data ] && find data -maxdepth 1 -name "*.csv" -type f -exec ls -lh {} \; || echo "No CSV files"
        echo ""
        echo "=== Database Status ==="
        [ -f "database/kath.db" ] && echo "Database size: $(ls -lh database/kath.db | awk '{print $5}')" || echo "Database not found"
        echo ""
        echo "=== Permissions ==="
        echo "data/ writable: $([ -w data ] && echo 'YES' || echo 'NO')"
        echo "database/ writable: $([ -w database ] && echo 'YES' || echo 'NO')"
    } > "$report_file"

    print_success "Persistence report saved to: $report_file"
}

main() {
    print_header

    verify_directories
    verify_data_files
    verify_directory_permissions
    verify_container_mounts
    verify_volume_mount_paths
    test_persistence_flow

    echo ""
    print_header
    generate_persistence_report

    echo ""
    print_success "Persistence verification complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review the persistence report: cat persistence_report_*.txt"
    echo "  2. Run KATH: ./start-kath.sh"
    echo "  3. Verify data survives container restart"
    echo "  4. Check DATA_PERSISTENCE.md for detailed information"
    echo ""
}

main "$@"
