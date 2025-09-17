#!/bin/bash

# Research Agent startup script

set -e

echo "🚀 Starting Research Agent..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker container"
    exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
fi

# Local development mode
echo "💻 Running in local development mode"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Export default environment variables if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating default .env file..."
    cat > .env << EOF
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=["*"]

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_TIMEOUT=120

# MCP Configuration
MCP_TIMEOUT=30

# Content Fetching
CONTENT_FETCHING_MAX_CONCURRENT=5
CONTENT_FETCHING_TIMEOUT=10
CONTENT_FETCHING_MAX_CONTENT_SIZE=1048576

# Research Configuration
RESEARCH_MAX_SOURCES_DEFAULT=20
RESEARCH_DEFAULT_DEPTH=standard

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=console
EOF
    echo "✅ Default .env file created"
fi

# Create necessary directories
mkdir -p logs cache

# Start the application
echo "🌐 Starting FastAPI server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 Documentation available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload