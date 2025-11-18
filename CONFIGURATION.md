# KATH Network Configuration Guide

## Overview

KATH uses a flexible configuration system that allows network customization
(ports, hostnames, etc.) **without rebuilding the Docker container**. This
guide explains how to configure and use these settings.

## Configuration File

The network configuration is stored in `config/network_config.yaml`. This file defines:

- Backend API port and hostname
- Frontend server port and hostname
- CORS allowed origins
- Redis connection settings
- Health check configuration

## Quick Start

### Docker Compose

```bash
# 1. Edit the network configuration (optional)
vi config/network_config.yaml

# 2. Start the application
docker-compose up -d

# 3. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8080
# Health check: http://localhost:8080/api/v1/monitoring/health
```

### Docker Run

```bash
# Mount the config directory and customize settings
docker run -d \
  -p 5173:5173 \
  -p 8080:8080 \
  -v $(pwd)/config:/config:ro \
  -v $(pwd)/data:/kath/app/back_end/src/workspace/default \
  -v $(pwd)/database:/kath/app/back_end/instance \
  cpu64/kath:latest
```

### Singularity

```bash
# Build Singularity image from Docker image
singularity build kath.sif docker://cpu64/kath:latest

# Run with default configuration
singularity run kath.sif

# Run with custom network configuration
NETWORK_CONFIG_PATH=/path/to/network_config.yaml singularity run kath.sif
```

## Configuration Options

### Backend Configuration

```yaml
backend:
  host: "0.0.0.0"      # Host to bind Flask server (0.0.0.0 = all interfaces)
  port: 8080           # Port for backend API server
  domain: "localhost"  # Domain/hostname for clients to connect to
```

**Environment Variable Overrides:**

- `BACKEND_HOST` or `FLASK_RUN_HOST`
- `BACKEND_PORT` or `FLASK_RUN_PORT`
- `DOMAIN`

### Frontend Configuration

```yaml
frontend:
  host: "0.0.0.0"      # Host to bind Vite dev server
  port: 5173           # Port for frontend server
```

**Environment Variable Overrides:**

- `FRONTEND_HOST`
- `FRONTEND_PORT` or `PORT`

### CORS Configuration

```yaml
cors:
  allowed_origins: "*"  # Change to specific origins for production
```

Examples:

```yaml
# Allow single origin
allowed_origins: "http://localhost:5173"

# Allow multiple origins (comma-separated)
allowed_origins: "http://localhost:5173,http://localhost:3000,https://example.com"

# Allow all origins (development only)
allowed_origins: "*"
```

**Environment Variable Override:**

- `ORIGINS`

### Redis Configuration

```yaml
redis:
  host: "localhost"    # Redis server hostname
  port: 6379          # Redis server port
  database: 0         # Redis database number (0-15)
```

**Environment Variable Overrides:**

- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`

## Common Use Cases

### Remote Development Server

To expose the application on a specific hostname/IP:

```yaml
backend:
  host: "0.0.0.0"
  port: 8080
  domain: "192.168.1.100"  # Or your hostname/IP

frontend:
  host: "0.0.0.0"
  port: 5173

cors:
  allowed_origins: "http://192.168.1.100:5173"
```

Then access at: `http://192.168.1.100:5173`

### Production Deployment

```yaml
backend:
  host: "127.0.0.1"    # Listen on localhost only
  port: 8080
  domain: "example.com"

frontend:
  host: "127.0.0.1"
  port: 5173

cors:
  allowed_origins: "https://example.com"
```

Use a reverse proxy (nginx, Apache) to expose the services publicly.

### Custom Ports

```yaml
backend:
  host: "0.0.0.0"
  port: 3000           # Custom port

frontend:
  host: "0.0.0.0"
  port: 3001           # Custom port

cors:
  allowed_origins: "http://localhost:3001"
```

### HPC Cluster (Singularity)

```yaml
backend:
  host: "0.0.0.0"
  port: 8080
  domain: "compute-node-01"

frontend:
  host: "0.0.0.0"
  port: 5173

redis:
  host: "localhost"
  port: 6379
  database: 0
```

Run with: `singularity run kath.sif`

## Modifying Configuration at Runtime

### Docker Compose Setup

```bash
# 1. Stop the container
docker-compose down

# 2. Edit configuration
vi config/network_config.yaml

# 3. Restart
docker-compose up -d
```

**No rebuild required!** The container will reload the configuration automatically.

### Docker Container Restart

```bash
# Update the mounted config file
vi config/network_config.yaml

# Restart the container
docker restart <container-id>
```

### Singularity Instance

```bash
# Stop the instance
singularity instance stop kath

# Update config
vi config/network_config.yaml

# Restart the instance
singularity instance start -B config:/config kath kath.sif
```

## Environment Variable Precedence

Settings are loaded in this order (highest to lowest priority):

1. Environment variables (e.g., `BACKEND_PORT=9000`)
2. YAML configuration file (`config/network_config.yaml`)
3. Hardcoded defaults in the application

Example: If you set `BACKEND_PORT=9000` as an environment variable, it will
override the YAML setting.

```bash
docker run -e BACKEND_PORT=9000 cpu64/kath:latest
```

## Troubleshooting

### "Connection refused" errors

1. Check if ports are available:

   ```bash
   netstat -tuln | grep 8080
   netstat -tuln | grep 5173
   ```

2. Check network configuration:

   ```bash
   docker logs <container-id> | grep "Configuration loaded"
   ```

3. Verify CORS settings match your domain

### Frontend cannot connect to API

1. Check the domain configuration
2. Verify CORS allowed_origins includes your frontend URL
3. Check that backend port is accessible from frontend container

```bash
docker exec <container-id> curl -v http://localhost:8080/api/v1/monitoring/health
```

### Redis connection errors

1. Verify Redis is running:

   ```bash
   docker exec <container-id> redis-cli ping
   ```

2. Check Redis configuration:

   ```bash
   docker logs <container-id> | grep "Redis"
   ```

## Loading Custom Configuration Paths

You can specify a custom configuration file path:

```bash
# Docker
docker run -e NETWORK_CONFIG_PATH=/custom/path/config.yaml cpu64/kath:latest

# Singularity
NETWORK_CONFIG_PATH=/custom/path/config.yaml singularity run kath.sif

# Compose
NETWORK_CONFIG_PATH=/etc/kath/network_config.yaml docker-compose up
```

## Configuration in Python Code

To access configuration programmatically:

```python
from src.settings import get_settings

settings = get_settings()
print(f"Backend: {settings.flask_host}:{settings.flask_port}")
print(f"Domain: {settings.domain}")
print(f"CORS Origins: {settings.cors_origins}")
print(f"Redis: {settings.redis_url}")
```

## Performance Considerations

- **YAML parsing**: Configuration is loaded once at startup
- **Restart required**: Changes to configuration require container restart
- **Caching**: Settings are cached using `@lru_cache()` for performance

## Security Notes

- **Production**: Never use `allowed_origins: "*"` in production
- **Binding**: Don't bind to `0.0.0.0` if the service should only be local
- **Redis**: Use proper authentication in production environments
- **HTTPS**: Use a reverse proxy with SSL/TLS for production deployments

## Getting Help

For issues related to network configuration:

1. Check `docker logs` output
2. Verify the YAML syntax is valid
3. Ensure ports are not already in use
4. Check that volume mounts are correct
5. Verify environment variables are set correctly
