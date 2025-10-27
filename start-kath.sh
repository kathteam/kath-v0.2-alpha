#!/usr/bin/env bash

# KATH Initialization Script for Mac/Linux
# This script automates the setup and launch of the KATH genetic analysis tool

set -e  # Exit on error

# Get script directory (works in bash)
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

KATH_IMAGE="cpu64/kath:final-amd64-fixed"
CONTAINER_NAME="kath"
FRONTEND_PORT=5173
BACKEND_PORT=8080
WORKSPACE_DIR="$SCRIPT_DIR/data"

# Color output
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
    echo "  KATH Genetic Analysis Tool"
    echo "  Version: v0.2-alpha"
    echo "=========================================="
    echo ""
}

# Check if Docker is installed
check_docker_installed() {
    if command -v docker &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if Docker daemon is running
check_docker_running() {
    if docker info &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Install Docker on macOS
install_docker_mac() {
    print_info "Installing Docker Desktop for macOS..."

    if ! command -v brew &>/dev/null; then
        print_info "Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    brew install --cask docker

    if [ -d "/Applications/Docker.app" ]; then
        print_success "Docker Desktop installed successfully!"
        print_info "Starting Docker Desktop..."
        open -a Docker
        return 0
    else
        return 1
    fi
}

# Install Docker on Linux
install_docker_linux() {
    print_info "Installing Docker on Linux..."
    print_info "Please run the following commands manually with sudo privileges:"
    echo ""
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    echo "  sudo usermod -aG docker $USER"
    echo ""
    print_warning "After installation, log out and log back in, then run this script again."
    exit 1
}

# Wait for Docker to be ready
wait_for_docker() {
    print_info "Waiting for Docker to start..."
    local max_attempts=60
    local attempt=0

    while ! check_docker_running; do
        if [ $attempt -ge $max_attempts ]; then
            print_error "Docker failed to start within 60 seconds"
            return 1
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo ""
    print_success "Docker is running!"
    return 0
}

# Stop existing container if running
stop_existing_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_info "Stopping existing KATH container..."
        docker stop "$CONTAINER_NAME" &>/dev/null || true
        docker rm "$CONTAINER_NAME" &>/dev/null || true
        print_success "Existing container removed"
    fi
}

# Create workspace directory
setup_workspace() {
    if [ ! -d "$WORKSPACE_DIR" ]; then
        print_info "Creating workspace directory at $WORKSPACE_DIR..."
        mkdir -p "$WORKSPACE_DIR"
        print_success "Workspace directory created"
    else
        print_info "Workspace directory already exists: $WORKSPACE_DIR"
    fi
}

# Pull Docker image
pull_docker_image() {
    print_info "Pulling KATH Docker image (this may take a few minutes)..."
    if docker pull "$KATH_IMAGE"; then
        print_success "Docker image downloaded successfully"
        return 0
    else
        print_error "Failed to pull Docker image"
        return 1
    fi
}


# Run Docker container
run_container() {
    print_info "Starting KATH container..."

    # Run container with proper flags matching working example
    docker run \
        --name "$CONTAINER_NAME" \
        -v "$WORKSPACE_DIR:/kath/app/back_end/src/workspace/8d8ac610-566d-4ef0-9c22-186b2a5ed793" \
        -it \
        --rm \
        -p "${BACKEND_PORT}:8080" \
        -p "${FRONTEND_PORT}:5173" \
        -e DOMAIN=localhost \
        "$KATH_IMAGE"

    if [ $? -eq 0 ]; then
        print_success "KATH container stopped successfully!"
        return 0
    else
        print_error "KATH container exited with error"
        return 1
    fi
}

# Cleanup on exit
cleanup() {
    echo ""
    print_info "KATH is shutting down..."
    print_success "KATH stopped successfully"
    exit 0
}

# Main execution
main() {
    print_header

    # Trap Ctrl+C to cleanup (use INT and TERM instead of SIGINT/SIGTERM for compatibility)
    trap cleanup INT TERM

    # Check and install Docker if needed
    if ! check_docker_installed; then
        print_warning "Docker is not installed"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            install_docker_mac || {
                print_error "Failed to install Docker. Please install manually from https://www.docker.com/products/docker-desktop"
                exit 1
            }
        else
            install_docker_linux
        fi
    else
        print_success "Docker is installed"
    fi

    # Start Docker if not running
    if ! check_docker_running; then
        print_warning "Docker is not running"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_info "Starting Docker Desktop..."
            open -a Docker
            wait_for_docker || {
                print_error "Failed to start Docker"
                exit 1
            }
        else
            print_info "Starting Docker daemon..."
            sudo systemctl start docker || {
                print_error "Failed to start Docker. Please start it manually."
                exit 1
            }
            wait_for_docker || exit 1
        fi
    else
        print_success "Docker is running"
    fi

    # Setup workspace
    setup_workspace

    # Stop existing container
    stop_existing_container

    # Pull latest image
    pull_docker_image || exit 1

    # Open browser in background
    (
        sleep 10
        print_info "Opening browser at http://localhost:${FRONTEND_PORT}..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "http://localhost:${FRONTEND_PORT}" 2>/dev/null || true
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v xdg-open &>/dev/null; then
                xdg-open "http://localhost:${FRONTEND_PORT}" 2>/dev/null || true
            elif command -v gnome-open &>/dev/null; then
                gnome-open "http://localhost:${FRONTEND_PORT}" 2>/dev/null || true
            fi
        fi
    ) &

    # Show access information
    echo ""
    print_success "Starting KATH..."
    echo ""
    echo "  Frontend URL: http://localhost:${FRONTEND_PORT}"
    echo "  Backend API:  http://localhost:${BACKEND_PORT}"
    echo "  Workspace:    $WORKSPACE_DIR"
    echo ""
    print_info "Press Ctrl+C to stop KATH and exit"
    echo ""

    # Run container (this blocks until container exits)
    run_container
}

main "$@"
