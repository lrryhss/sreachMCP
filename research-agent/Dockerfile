# Multi-stage build for Research Agent
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and add to docker group
RUN useradd -m -s /bin/bash research && \
    mkdir -p /app/logs /app/cache && \
    chown -R research:research /app && \
    groupadd -f docker && \
    usermod -aG docker research

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/research/.local

# Copy application code
COPY --chown=research:research . .

# Run as root for Docker access (Docker Desktop requirement)
# USER research

# Update PATH for root to use research user's packages
ENV PATH=/home/research/.local/bin:$PATH
ENV PYTHONPATH=/app:/home/research/.local/lib/python3.11/site-packages

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]