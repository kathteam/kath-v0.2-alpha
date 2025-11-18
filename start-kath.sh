#!/usr/bin/env bash

# KATH Initialization Script for Mac/Linux
# This script automates the setup and launch of the KATH genetic analysis tool

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

KATH_IMAGE="cpu64/kath:latest"
CONTAINER_NAME="kath"
FRONTEND_PORT=5173
BACKEND_PORT=8080
WORKSPACE_DIR="$SCRIPT_DIR/data"
DATABASE_DIR="$SCRIPT_DIR/database"
WORKSPACE_UUID="default"
CONFIG_DIR="$SCRIPT_DIR/config"
RESOURCES_CONFIG="$CONFIG_DIR/docker-resources.yaml"

# Function to parse YAML values (simple parser for basic key: value pairs)
get_yaml_value() {
    local file="$1"
    local key="$2"
    if [ -f "$file" ]; then
        grep "^[[:space:]]*$key:" "$file" | sed 's/.*:\s*"\?\([^"]*\)"\?$/\1/' | head -1
    fi
}

# Load resource limits from config file
load_resource_limits() {
    if [ -f "$RESOURCES_CONFIG" ]; then
        print_info "Loading resource limits from: $RESOURCES_CONFIG"
        DOCKER_MEMORY=$(get_yaml_value "$RESOURCES_CONFIG" "memory")
        DOCKER_MEMORY_SWAP=$(get_yaml_value "$RESOURCES_CONFIG" "memory_swap")
        DOCKER_CPUS=$(get_yaml_value "$RESOURCES_CONFIG" "cpus")
        CADD_MAX_WORKERS=$(get_yaml_value "$RESOURCES_CONFIG" "max_workers")

        # Set defaults if parsing failed
        DOCKER_MEMORY="${DOCKER_MEMORY:-4g}"
        DOCKER_MEMORY_SWAP="${DOCKER_MEMORY_SWAP:-4g}"
        DOCKER_CPUS="${DOCKER_CPUS:-4}"
        CADD_MAX_WORKERS="${CADD_MAX_WORKERS:-4}"

        print_info "Resource limits - Memory: $DOCKER_MEMORY, CPUs: $DOCKER_CPUS, Workers: $CADD_MAX_WORKERS"
    else
        # Use defaults if config file not found
        print_warning "Resource config not found, using defaults"
        DOCKER_MEMORY="4g"
        DOCKER_MEMORY_SWAP="4g"
        DOCKER_CPUS="4"
        CADD_MAX_WORKERS="4"
    fi
}

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
    if command -v docker > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if Docker daemon is running
check_docker_running() {
    if docker info > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Install Docker on macOS
install_docker_mac() {
    print_info "Installing Docker Desktop for macOS..."

    if ! command -v brew > /dev/null 2>&1; then
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
        docker stop "$CONTAINER_NAME" > /dev/null 2>&1 || true
        docker rm "$CONTAINER_NAME" > /dev/null 2>&1 || true
        print_success "Existing container removed"
    fi
}

# Create workspace and database directories
setup_workspace() {
    if [ ! -d "$WORKSPACE_DIR" ]; then
        print_info "Creating workspace directory at $WORKSPACE_DIR..."
        mkdir -p "$WORKSPACE_DIR"
        print_success "Workspace directory created"
    else
        print_info "Workspace directory already exists: $WORKSPACE_DIR"
    fi

    if [ ! -d "$DATABASE_DIR" ]; then
        print_info "Creating database directory at $DATABASE_DIR..."
        mkdir -p "$DATABASE_DIR"
        print_success "Database directory created"
    else
        print_info "Database directory already exists: $DATABASE_DIR"
    fi
}

# Check if Docker image exists locally
check_image_exists() {
    if docker inspect "$KATH_IMAGE" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Pull Docker image (only if not available locally)
pull_docker_image() {
    if check_image_exists; then
        print_success "KATH Docker image found locally"
        return 0
    fi

    print_info "KATH Docker image not found locally"
    print_info "Pulling KATH Docker image from registry (this may take a few minutes)..."
    if docker pull "$KATH_IMAGE"; then
        print_success "Docker image downloaded successfully"
        return 0
    else
        print_error "Failed to pull Docker image from registry"
        print_error "Please build the image first using: ./build-kath-complete.sh"
        return 1
    fi
}


# Run Docker container
run_container() {
    print_info "Starting KATH container..."

    # Run container with proper volume mounts for workspace and database
    # Resource limits are applied from docker-resources.yaml to prevent system freezing
    docker run \
        --name "$CONTAINER_NAME" \
        -v "$WORKSPACE_DIR:/kath/app/back_end/src/workspace/$WORKSPACE_UUID" \
        -v "$DATABASE_DIR:/kath/app/back_end/instance" \
        -it \
        --rm \
        -p "${BACKEND_PORT}:8080" \
        -p "${FRONTEND_PORT}:5173" \
        --memory="$DOCKER_MEMORY" \
        --memory-swap="$DOCKER_MEMORY_SWAP" \
        --cpus="$DOCKER_CPUS" \
        -e DOMAIN=localhost \
        -e USE_DATABASE_BACKEND=true \
        -e DATABASE_PATH=instance/kath.db \
        -e CADD_MAX_WORKERS="$CADD_MAX_WORKERS" \
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

    # Load resource limits from config file before anything else
    load_resource_limits

    # Trap Ctrl+C to cleanup (use INT and TERM instead of SIGINT/SIGTERM for compatibility)
    trap cleanup INT TERM

    # Check and install Docker if needed
    if ! check_docker_installed; then
        print_warning "Docker is not installed"

        case "$OSTYPE" in
            darwin*)
                install_docker_mac || {
                    print_error "Failed to install Docker. Please install manually from https://www.docker.com/products/docker-desktop"
                    exit 1
                }
                ;;
            *)
                install_docker_linux
                ;;
        esac
    else
        print_success "Docker is installed"
    fi

    # Start Docker if not running
    if ! check_docker_running; then
        print_warning "Docker is not running"

        case "$OSTYPE" in
            darwin*)
                print_info "Starting Docker Desktop..."
                open -a Docker
                wait_for_docker || {
                    print_error "Failed to start Docker"
                    exit 1
                }
                ;;
            *)
                print_info "Starting Docker daemon..."
                sudo systemctl start docker || {
                    print_error "Failed to start Docker. Please start it manually."
                    exit 1
                }
                wait_for_docker || exit 1
                ;;
        esac
    else
        print_success "Docker is running"
    fi

    # Setup workspace
    setup_workspace

    # Stop existing container
    stop_existing_container

    # Pull latest image
    pull_docker_image || exit 1

    # Start Docker container and open browser in background
    open_browser_bg() {
        sleep 15
        print_info "Opening browser at http://localhost:${FRONTEND_PORT}..."

        # Try to open browser on host system using appropriate method
        case "$OSTYPE" in
            darwin*)
                # macOS - use open command which will use default browser
                if command -v open > /dev/null 2>&1; then
                    open "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1 || {
                        print_error "Failed to open browser. Please visit: http://localhost:${FRONTEND_PORT}"
                        return 1
                    }
                else
                    print_error "Browser not found. Please visit: http://localhost:${FRONTEND_PORT}"
                    return 1
                fi
                ;;
            linux-gnu* | linux*)
                # Linux - try multiple browsers in order of preference
                opened=false
                # POSIX-compatible browser list (space-separated string)
                browsers="xdg-open firefox brave brave-browser chromium chromium-browser google-chrome chrome microsoft-edge edge"

                for browser in $browsers; do
                    if command -v "$browser" > /dev/null 2>&1; then
                        print_info "Found browser: $browser"
                        if [ "$browser" = "xdg-open" ]; then
                            xdg-open "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1 && opened=true && break
                        else
                            "$browser" "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1 & opened=true && break
                        fi
                    fi
                done

                if [ "$opened" = false ]; then
                    print_error "No browser found. Please visit: http://localhost:${FRONTEND_PORT}"
                    return 1
                fi
                ;;
            *)
                # Unknown OS - still try to open with common commands
                opened=false
                # POSIX-compatible browser list (space-separated string)
                browsers="open xdg-open firefox brave chromium google-chrome edge"

                for browser in $browsers; do
                    if command -v "$browser" > /dev/null 2>&1; then
                        print_info "Found browser: $browser"
                        "$browser" "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1 & opened=true && break
                    fi
                done

                if [ "$opened" = false ]; then
                    print_warning "Unknown OS type. Please manually visit: http://localhost:${FRONTEND_PORT}"
                    return 1
                fi
                ;;
        esac

        print_success "Browser opened successfully"
    }

    # Run browser opening in background
    open_browser_bg &

    # Show access information
    echo ""
    print_success "Starting KATH..."
    echo ""
    echo "  Frontend URL: http://localhost:${FRONTEND_PORT}"
    echo "  Backend API:  http://localhost:${BACKEND_PORT}"
    echo "  Health Check: http://localhost:${BACKEND_PORT}/api/v1/monitoring/health"
    echo ""
    echo "  Data Directories:"
    echo "    Workspace:  $WORKSPACE_DIR"
    echo "    Database:   $DATABASE_DIR"
    echo ""
    print_info "Press Ctrl+C to stop KATH and exit"
    echo ""

    # Run container (this blocks until container exits)
    run_container
}

main "$@"
