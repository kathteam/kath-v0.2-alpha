#!/bin/bash
set -e

# Configuration initialization script
# Loads network settings from YAML config file or environment variables

# Default values (can be overridden by network_config.yaml or environment variables)
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-${FLASK_RUN_PORT:-8080}}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-${PORT:-5173}}"
DOMAIN="${DOMAIN:-localhost}"

# Export for use in subprocesses
export FLASK_RUN_HOST="${BACKEND_HOST}"
export FLASK_RUN_PORT="${BACKEND_PORT}"
export PORT="${FRONTEND_PORT}"
export DOMAIN="${DOMAIN}"

# Set CORS origins
export ORIGINS="http://${DOMAIN}:${FRONTEND_PORT}"

# Set Vite API URLs
export VITE_API_URL="http://${DOMAIN}:${BACKEND_PORT}/api/v1"
export VITE_SOCKET_URL="http://${DOMAIN}:${BACKEND_PORT}"

echo "====================================="
echo "KATH Application Startup"
echo "====================================="
echo "Configuration loaded:"
echo "  Backend: http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "  Domain: ${DOMAIN}"
echo "  API URL: ${VITE_API_URL}"
echo "  CORS Origins: ${ORIGINS}"
echo "====================================="
echo ""

# Generate frontend environment files from network config
# This allows the frontend to use the same configuration as the backend
echo "Generating frontend environment configuration..."
cd ./front_end/
if [ -f "generate-env.js" ]; then
    node generate-env.js || echo "Warning: Could not generate frontend env files, using defaults"
else
    echo "Warning: generate-env.js not found, using default environment files"
fi
cd ..

echo "Starting Redis server..."
redis-server --daemonize yes --port 6379 || echo "Warning: Redis startup may have issues"

echo "Starting backend API server..."
cd ./back_end/
gunicorn -c gunicorn_config.py run:app &
BACKEND_PID=$!
cd ..

echo "Starting frontend development server..."
cd ./front_end/
npm run dev &
FRONTEND_PID=$!
cd ..

echo "All services started. Press Ctrl+C to stop."
echo ""

# Wait for processes
wait
