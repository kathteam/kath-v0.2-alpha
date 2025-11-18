#!/bin/bash
#
# KATH Project Cleanup Script
# Cleans up all build artifacts, caches, and temporary files
# to prepare for a fresh build
#
# Usage: ./clean_all.sh [--docker] [--force]
#
# Options:
#   --docker    Also remove Docker images (requires confirmation)
#   --force     Skip confirmation prompts
#   --help      Show this help message
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
CLEAN_DOCKER=false
FORCE_MODE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Print functions
print_info() {
    printf "${CYAN}[INFO]${NC} %s\n" "$1"
}

print_success() {
    printf "${GREEN}[✓]${NC} %s\n" "$1"
}

print_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

print_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}

print_header() {
    echo ""
    echo "=============================================="
    echo "  $1"
    echo "=============================================="
    echo ""
}

# Confirm action
confirm() {
    if [ "$FORCE_MODE" = true ]; then
        return 0
    fi

    local prompt="$1"
    local response

    printf "${YELLOW}%s (y/N): ${NC}" "$prompt"
    read -r response

    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker)
                CLEAN_DOCKER=true
                shift
                ;;
            --force)
                FORCE_MODE=true
                shift
                ;;
            --help|-h)
                show_help
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help
show_help() {
    cat << EOF

KATH Project Cleanup Script

Usage: $0 [OPTIONS]

Options:
  --docker    Also remove Docker images (cpu64/kath:*)
  --force     Skip all confirmation prompts
  --help, -h  Show this help message

Examples:
  # Clean build artifacts only (safe)
  $0

  # Clean everything including Docker images
  $0 --docker

  # Clean without prompts
  $0 --force --docker

What gets cleaned:
  - Python cache (__pycache__, .pytest_cache, .mypy_cache)
  - Node.js cache (node_modules, npm caches)
  - Build artifacts (dist, build, htmlcov)
  - Log files
  - Test coverage data
  - Temporary files

What does NOT get cleaned (safe):
  - Source code
  - Configuration files
  - Data files (data/, database/)
  - Environment files (.env*)
  - Git history

EOF
}

# Clean Python caches
clean_python() {
    print_info "Cleaning Python caches..."

    # Remove __pycache__ directories
    if find "$PROJECT_ROOT" -type d -name "__pycache__" 2>/dev/null | grep -q .; then
        find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        print_success "Removed __pycache__ directories"
    fi

    # Remove .pytest_cache
    if [ -d "$PROJECT_ROOT"/.pytest_cache ]; then
        rm -rf "$PROJECT_ROOT"/.pytest_cache
        print_success "Removed .pytest_cache"
    fi

    # Remove .mypy_cache
    if [ -d "$PROJECT_ROOT"/.mypy_cache ]; then
        rm -rf "$PROJECT_ROOT"/.mypy_cache
        print_success "Removed .mypy_cache"
    fi

    # Remove .egg-info directories
    if find "$PROJECT_ROOT" -type d -name "*.egg-info" 2>/dev/null | grep -q .; then
        find "$PROJECT_ROOT" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
        print_success "Removed .egg-info directories"
    fi

    # Remove compiled Python files
    if find "$PROJECT_ROOT" -type f -name "*.pyc" 2>/dev/null | grep -q .; then
        find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
        print_success "Removed .pyc files"
    fi

    if find "$PROJECT_ROOT" -type f -name "*.pyo" 2>/dev/null | grep -q .; then
        find "$PROJECT_ROOT" -type f -name "*.pyo" -delete 2>/dev/null || true
        print_success "Removed .pyo files"
    fi
}

# Clean Node.js caches
clean_nodejs() {
    print_info "Cleaning Node.js caches..."

    # Remove node_modules
    if [ -d "$PROJECT_ROOT"/app/front_end/node_modules ]; then
        print_warning "Removing node_modules (this may take a moment)..."
        rm -rf "$PROJECT_ROOT"/app/front_end/node_modules
        print_success "Removed node_modules"
    fi

    # Remove package-lock.json cache
    if [ -f "$PROJECT_ROOT"/app/front_end/.npmrc ]; then
        rm -f "$PROJECT_ROOT"/app/front_end/.npmrc
        print_success "Removed .npmrc"
    fi
}

# Clean build artifacts
clean_artifacts() {
    print_info "Cleaning build artifacts..."

    # Remove build directories
    for dir in "dist" "build" "htmlcov" ".venv" ".venv3"; do
        if [ -d "$PROJECT_ROOT"/app/back_end/"$dir" ]; then
            rm -rf "$PROJECT_ROOT"/app/back_end/"$dir"
            print_success "Removed app/back_end/$dir"
        fi
        if [ -d "$PROJECT_ROOT"/"$dir" ]; then
            rm -rf "$PROJECT_ROOT"/"$dir"
            print_success "Removed $dir"
        fi
    done

    # Remove coverage files
    if [ -f "$PROJECT_ROOT"/.coverage ]; then
        rm -f "$PROJECT_ROOT"/.coverage
        print_success "Removed .coverage"
    fi
}

# Clean logs
clean_logs() {
    print_info "Cleaning log files..."

    # Remove log directories
    if [ -d "$PROJECT_ROOT"/app/back_end/src/logs ]; then
        rm -rf "$PROJECT_ROOT"/app/back_end/src/logs/*
        print_success "Cleaned src/logs"
    fi

    # Remove log files
    if find "$PROJECT_ROOT" -type f -name "*.log" 2>/dev/null | grep -q .; then
        find "$PROJECT_ROOT" -type f -name "*.log" -delete 2>/dev/null || true
        print_success "Removed .log files"
    fi
}

# Clean temporary files
clean_temp() {
    print_info "Cleaning temporary files..."

    # Remove OS-specific files
    find "$PROJECT_ROOT" -type f \( -name ".DS_Store" -o -name "Thumbs.db" \) -delete 2>/dev/null || true
    print_success "Removed OS temporary files"

    # Remove editor backup files
    find "$PROJECT_ROOT" -type f \( -name "*~" -o -name "*.swp" -o -name "*.swo" \) -delete 2>/dev/null || true
    print_success "Removed editor backup files"
}

# Clean Docker images
clean_docker() {
    if [ "$CLEAN_DOCKER" = false ]; then
        return
    fi

    print_header "Docker Cleanup"

    if ! command -v docker > /dev/null 2>&1; then
        print_warning "Docker is not installed, skipping Docker cleanup"
        return
    fi

    # List KATH images
    local kath_images
    kath_images=$(docker images --filter "reference=cpu64/kath:*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || echo "")

    if [ -z "$kath_images" ]; then
        print_info "No KATH Docker images found"
        return
    fi

    print_warning "The following Docker images will be removed:"
    echo "$kath_images" | while read -r image; do
        echo "  - $image"
    done
    echo ""

    if ! confirm "Remove all KATH Docker images?"; then
        print_info "Docker images NOT removed"
        return
    fi

    echo "$kath_images" | while read -r image; do
        if docker rmi "$image" 2>/dev/null; then
            print_success "Removed $image"
        else
            print_warning "Failed to remove $image (may be in use)"
        fi
    done

    # Clean dangling images
    local dangling_count
    dangling_count=$(docker images -f "dangling=true" -q | wc -l)
    if [ "$dangling_count" -gt 0 ]; then
        print_info "Found $dangling_count dangling images"
        if confirm "Remove dangling images?"; then
            docker image prune -f --filter "dangling=true" > /dev/null
            print_success "Removed dangling images"
        fi
    fi
}

# Generate cleanup summary
summary() {
    print_header "Cleanup Summary"
    echo "The following items were cleaned:"
    echo "  ✓ Python caches (__pycache__, .pytest_cache, .mypy_cache)"
    echo "  ✓ Compiled Python files (.pyc, .pyo)"
    echo "  ✓ Node.js cache (node_modules)"
    echo "  ✓ Build artifacts (dist, build, htmlcov)"
    echo "  ✓ Log files"
    echo "  ✓ Temporary files (.DS_Store, *.swp, etc.)"

    if [ "$CLEAN_DOCKER" = true ]; then
        echo "  ✓ Docker images (if confirmed)"
    fi

    echo ""
    print_success "Cleanup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. npm install (in app/front_end)"
    echo "  2. ./build-kath-complete.sh [--full]"
    echo ""
}

# Main execution
main() {
    parse_args "$@"

    print_header "KATH Project Cleanup"

    if ! confirm "This will clean build artifacts and caches. Continue?"; then
        print_info "Cleanup cancelled"
        exit 0
    fi

    echo ""
    clean_python
    echo ""
    clean_nodejs
    echo ""
    clean_artifacts
    echo ""
    clean_logs
    echo ""
    clean_temp

    if [ "$CLEAN_DOCKER" = true ]; then
        echo ""
        clean_docker
    fi

    summary
}

main "$@"
