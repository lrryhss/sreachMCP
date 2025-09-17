#!/bin/bash
set -e

# Function to handle signals properly
trap_handler() {
    echo "Received shutdown signal, stopping server..." >&2
    kill -TERM "$child_pid" 2>/dev/null
    wait "$child_pid"
    exit 0
}

# Set up signal handlers
trap trap_handler SIGTERM SIGINT

# Wait for SearXNG to be ready (redirect to stderr to not interfere with stdio)
echo "Waiting for SearXNG to be ready..." >&2
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s -f -o /dev/null "${SEARXNG_BASE_URL:-http://searxng:8080}"; then
        echo "SearXNG is ready!" >&2
        break
    fi

    attempt=$((attempt + 1))
    echo "Waiting for SearXNG... (attempt $attempt/$max_attempts)" >&2
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: SearXNG did not become ready in time" >&2
    exit 1
fi

# Log startup information to stderr
echo "Starting SearXNG MCP Server..." >&2
echo "Configuration:" >&2
echo "  SEARXNG_BASE_URL: ${SEARXNG_BASE_URL:-http://searxng:8080}" >&2
echo "  MCP_TRANSPORT: ${MCP_TRANSPORT:-stdio}" >&2
echo "  LOG_LEVEL: ${LOG_LEVEL:-INFO}" >&2
echo "  MAX_RESULTS: ${MAX_RESULTS:-10}" >&2

# Execute the command passed to docker run
exec "$@"