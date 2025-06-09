#!/bin/bash

check_docker_running() {
    if ! docker info &>/dev/null; then
        return 1
    else
        return 0
    fi
}

# Check if Docker Desktop is installed
if [ ! -d "/Applications/Docker.app" ]; then
    echo "Docker Desktop is not installed."

    # Check if Homebrew is installed
    if ! command -v brew &>/dev/null; then
        echo "Homebrew is not installed. Installing Homebrew..."

        # Install Homebrew
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Update Homebrew
        echo "Updating Homebrew..."
        brew update
    else
        echo "Homebrew is already installed."
    fi

    # Install Docker Desktop using Homebrew
    echo "Installing Docker Desktop..."
    brew install --cask docker

    # Verify installation
    if [ -d "/Applications/Docker.app" ]; then
        echo "Docker Desktop has been successfully installed!"
    else
        echo "Docker installation failed. Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
        exit 1
    fi

else
    echo "Docker Desktop is already installed."
fi

# Trap for interrupt signal (Ctrl+C or kill command)
trap 'echo "Interrupt signal received. Stopping Docker Desktop..."; pkill Docker; exit 0' SIGINT

# Check if Docker is running
echo "Checking if Docker Desktop is running..."
if ! check_docker_running; then
    echo "Docker Desktop is not running. Launching Docker Desktop..."
    open -a Docker
    echo "Please wait for Docker Desktop to initialize. This may take a minute..."

    # Wait for Docker to start
    while ! check_docker_running; do
        sleep 1
        echo -n "."
    done
    echo -e "\nDocker Desktop is up and running."
else
    echo "Docker Desktop is already running."
fi

# Create directory
mkdir -p "$HOME/Desktop/kath"

# Run a kath container
echo "Downloading Docker container..."
docker pull cpu64/kath:final
echo "Running Docker container..."
docker run -t --rm --name kath -p 8080:8080 -p 5173:5173 -v "$HOME/Desktop/kath/:/kath/app/back_end/src/workspace" cpu64/kath:final

# TODO: figure out and fix quitting
while check_docker_running; do
    sleep 1
done
