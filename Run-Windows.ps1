# Requires Admin rights
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "You must run this script as Administrator."
    exit 1
}

function Check-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check if Docker Desktop is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop is not installed."

    # Check if Chocolatey is installed
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "Chocolatey is not installed. Installing Chocolatey..."

        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

        # Install Chocolatey
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    } else {
        Write-Host "Chocolatey is already installed."
    }

    # Install Docker Desktop using Chocolatey
    Write-Host "Installing Docker Desktop..."
    choco install docker-desktop -y

    # Verify installation
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "Docker Desktop has been successfully installed!"
    } else {
        Write-Error "Docker installation failed. Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
        exit 1
    }

    Write-Host "Docker Desktop installed. Please restart the computer and run this script again."
    exit 0
} else {
    Write-Host "Docker Desktop is already installed."
}

# Check if Docker is running
Write-Host "Checking if Docker Desktop is running..."
if (-not (Check-DockerRunning)) {
    Write-Host "Docker Desktop is not running. Starting Docker Desktop..."
    Start-Process -FilePath "$Env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    Write-Host "Please wait for Docker Desktop to initialize..."

    # Wait for Docker to start
    while (-not (Check-DockerRunning)) {
        Start-Sleep -Seconds 1
        Write-Host -NoNewline "."
    }
    Write-Host "`nDocker Desktop is up and running."
} else {
    Write-Host "Docker Desktop is already running."
}


# Create folder
$folderPath = "$Env:USERPROFILE\Desktop\kath"
if (-not (Test-Path $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath | Out-Null
}

# Run kath container
Write-Host "Downloading Docker container..."
docker pull cpu64/kath:final
Write-Host "Running Docker container..."
docker run -t --rm --name kath -p 8080:8080 -p 5173:5173 -v "$folderPath:/kath/app/back_end/src/workspace" cpu64/kath:final

# TODO: figure out and fix quitting
while (Check-DockerRunning) {
    Start-Sleep -Seconds 1
}
