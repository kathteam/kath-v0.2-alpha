#!/bin/bash
# Check Docker build status

echo "============================================"
echo "  Docker Build Status Checker"
echo "============================================"
echo ""

# Check if build process is running
if ps aux | grep -E "[d]ocker build.*cpu64/kath" > /dev/null; then
    echo " Build is RUNNING"
    echo ""

    # Show latest progress
    echo "Latest progress (last 10 lines):"
    echo "----------------------------------------"
    tail -10 docker-build.log
    echo ""

    # Show download progress if downloading
    if grep -q "% Total" docker-build.log | tail -5; then
        echo "Downloading files..."
    fi

else
    echo " Build is NOT running"
    echo ""

    # Check if completed successfully
    if grep -q "Docker image built successfully" docker-build.log; then
        echo " Build COMPLETED successfully!"
        echo ""

        # Show built images
        echo "KATH Docker images:"
        docker images | grep "cpu64/kath" | grep "latest"

    elif grep -q "ERROR\|FAILED\|error" docker-build.log | tail -20; then
        echo " Build FAILED with errors!"
        echo ""
        echo "Last 20 lines of log:"
        echo "----------------------------------------"
        tail -20 docker-build.log

    else
        echo "  Build status unknown"
        echo ""
        echo "Last 20 lines of log:"
        echo "----------------------------------------"
        tail -20 docker-build.log
    fi
fi

echo ""
echo "============================================"
echo "Full log: docker-build.log"
echo "Live monitor: tail -f docker-build.log"
echo "============================================"
