#!/bin/bash
# KATH Complete Docker Build Script
# Builds both reference files and application images for the KATH system

set -e  # Exit on error

# Configuration
IMAGE_NAME="cpu64/kath"
FILES_IMAGE="${IMAGE_NAME}:files"
APP_IMAGE="${IMAGE_NAME}:latest"
IMAGE_TAG="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions (POSIX-compliant)
print_info() {
    printf "${CYAN}[INFO]${NC} %s\n" "$1"
}

print_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
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

# Show help
show_help() {
    cat << EOF

KATH Complete Docker Build Script (Unified Multi-Stage Build)

Usage:
  $0 [OPTIONS] [TAG]

Options:
  --full         Rebuild everything (full build with no cache)
  --help, -h     Show this help message

Arguments:
  TAG            Image tag for application (default: latest)

Default behavior:
  Builds the complete KATH system using unified multi-stage Dockerfile
  - Stage 1: Downloads reference files (hg38.fa, REVEL database, etc.)
  - Stage 2: Builds application (Python backend + Node.js frontend)
  - Includes: Firefox ESR binary, GeckoDriver, CUDA support

Examples:
  $0                      (standard build with caching)
  $0 --full               (rebuild from scratch, no cache)
  $0 --full v1.0          (full build with custom tag v1.0)

EOF
    exit 0
}

# Check if Docker is installed and running
check_docker() {
    print_info "Checking Docker installation..."

    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed!"
        echo ""
        echo "Please install Docker:"
        echo "  - Linux: curl -fsSL https://get.docker.com | sh"
        echo "  - Mac:   brew install --cask docker"
        echo "  - Or visit: https://docs.docker.com/get-docker/"
        echo ""
        exit 1
    fi

    print_success "Docker is installed"

    print_info "Checking Docker daemon..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running!"
        echo ""
        echo "Please start Docker:"

        if [ "$(uname -s)" = "Darwin" ]; then
            echo "  - Open Docker Desktop application"
            echo "  - Or run: open -a Docker"
        else
            echo "  - Run: sudo systemctl start docker"
            echo "  - Or run: sudo service docker start"
        fi
        echo ""
        exit 1
    fi

    print_success "Docker daemon is running"
}

# Check if image exists
image_exists() {
    docker inspect "$1" >/dev/null 2>&1
    return $?
}

# Build application image (includes reference files as multi-stage build)
# Note: The unified Dockerfile uses a multi-stage build:
#   - Stage 1: Alpine container downloads reference files
#   - Stage 2: Ubuntu CUDA container with application
build_app_image_unified() {
    print_header "Building Complete KATH Image (Unified Multi-Stage Build)"

    print_info "Building: ${APP_IMAGE}"
    print_info "This will download ~2GB of reference data and build the application"
    print_info "Expected time: 15-30 minutes"
    echo ""

    DOCKER_BUILDKIT=1 docker build \
        -t "${APP_IMAGE}" \
        -f app/Dockerfile \
        --progress=plain \
        app/

    if [ $? -eq 0 ]; then
        echo ""
        print_success "Application image built successfully!"
        docker images | grep "${IMAGE_NAME}"
        echo ""
    else
        echo ""
        print_error "Application build failed!"
        exit 1
    fi
}

# Deprecated: This function is no longer used with unified Dockerfile
# Kept for reference - the unified build handles everything in one stage
# build_app_image_old() {
#     Used to build just the application image assuming reference files existed
# }

# Show image details
show_image_details() {
    print_info "Image details:"
    docker inspect "${IMAGE_NAME}:${IMAGE_TAG}" --format='  Size: {{.Size}} bytes' 2>/dev/null || true
    docker inspect "${IMAGE_NAME}:${IMAGE_TAG}" --format='  Created: {{.Created}}' 2>/dev/null || true
    echo ""
}

# Show next steps
show_next_steps() {
    print_header "Next Steps"

    echo "To run KATH, use:"
    echo "  - ./start-kath.sh         (Bash script)"
    echo "  - docker-compose up       (Docker Compose)"
    echo ""
    echo "To access KATH:"
    echo "  - Frontend: http://localhost:5173"
    echo "  - Backend:  http://localhost:8080"
    echo "  - Health:   http://localhost:8080/api/v1/monitoring/health"
    echo ""
    echo "To clean up old images:"
    echo "  - docker system prune -af"
    echo ""
}

# Build complete system (unified multi-stage Dockerfile)
build_complete() {
    print_header "Building Complete KATH System"

    print_info "This will build a unified image with:"
    echo "  - Stage 1: Reference files (hg38.fa, REVEL database, etc.)"
    echo "  - Stage 2: Application (Python backend + Node.js frontend + Firefox + GeckoDriver)"
    echo ""
    print_info "Total expected time: 15-30 minutes"
    print_info "Total download size: ~2GB reference data"
    echo ""

    # Build unified application (both stages in one build)
    build_app_image_unified

    print_success "Complete build finished!"
    show_image_details
}

# Smart build: unified approach (no longer needs separate reference files image)
smart_build() {
    print_info "Building complete KATH system with unified multi-stage Dockerfile..."
    echo ""

    # With the unified Dockerfile, always build as a complete system
    # The multi-stage build handles reference files and application in one go
    build_complete

    print_success "Build complete!"
    show_next_steps
}

# Main execution
main() {
    print_header "KATH Complete Docker Build Script"

    # Parse command line arguments
    BUILD_MODE="${1:-}"

    case "${BUILD_MODE}" in
        --help|-h|help)
            show_help
            ;;

        --full)
            check_docker
            echo ""
            print_info "Building with --no-cache flag (full rebuild)"
            echo ""
            # Build with no cache for full rebuild
            print_header "Building Complete KATH System (No Cache)"
            print_info "Building: ${APP_IMAGE}"
            DOCKER_BUILDKIT=1 docker build \
                --no-cache \
                -t "${APP_IMAGE}" \
                -f app/Dockerfile \
                --progress=plain \
                app/
            if [ $? -eq 0 ]; then
                print_success "Build completed successfully!"
                show_image_details
                show_next_steps
            else
                print_error "Build failed!"
                exit 1
            fi
            exit 0
            ;;

        *)
            # Default: standard smart build
            check_docker
            echo ""
            smart_build
            exit 0
            ;;
    esac
}

# Run main function
main "$@"
