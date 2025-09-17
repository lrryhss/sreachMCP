# Research Agent Microservice

An intelligent research automation microservice that combines local LLM processing (Ollama), privacy-respecting web search (SearXNG MCP), and comprehensive content extraction to produce professional HTML reports with citations.

## Features

- 🤖 **AI-Powered Research**: Uses Ollama LLM for query understanding and content synthesis
- 🔍 **Privacy-First Search**: Integrates with SearXNG through MCP server
- 📄 **Smart Content Extraction**: Fetches and processes HTML, PDF, and other formats
- 📊 **Professional Reports**: Generates comprehensive HTML reports with citations
- ⚡ **Async Architecture**: High-performance async/await design for concurrent operations
- 🔄 **Real-time Updates**: SSE/WebSocket support for progress streaming
- 💾 **Intelligent Caching**: Multi-level caching for optimal performance
- 🛡️ **Security Built-in**: Rate limiting, input validation, content sanitization

## Architecture Overview

```
User Request → FastAPI → Research Orchestrator
                              ↓
                    Query Analysis (Ollama)
                              ↓
                    Search Execution (MCP/SearXNG)
                              ↓
                    Content Fetching (Web)
                              ↓
                    Synthesis (Ollama)
                              ↓
                    Report Generation → HTML/JSON/MD
```

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Ollama with `gpt-oss:20b` model
- SearXNG MCP Server (from parent project)
- Redis (included in docker-compose)

## Installation

### 1. Clone the Repository

```bash
cd research-agent
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Install Dependencies

#### Option A: Virtual Environment (Development)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Option B: Docker (Production)

```bash
docker-compose up -d
```

### 4. Verify Ollama Model

```bash
# Check if gpt-oss:20b is available
curl http://localhost:11434/api/tags

# If not, pull the model
ollama pull gpt-oss:20b
```

## Configuration

### Key Configuration Files

- **`.env`**: Environment variables
- **`config/default.yaml`**: Detailed application settings
- **`docker-compose.yml`**: Container orchestration

### Important Settings

```yaml
# Ollama Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=gpt-oss:20b

# MCP Server
MCP_SEARXNG_URL=http://host.docker.internal:8090

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Usage

### Starting the Service

#### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Start with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

#### Production Mode

```bash
# Using Docker Compose
docker-compose up -d

# Or using Docker directly
docker build -t research-agent .
docker run -p 8080:8080 research-agent
```

### API Examples

#### Start a Research Task

```bash
curl -X POST http://localhost:8080/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest developments in quantum computing 2025",
    "options": {
      "depth": "comprehensive",
      "max_sources": 20
    }
  }'
```

Response:
```json
{
  "task_id": "res_7f3d2a1b9c5e",
  "status": "accepted",
  "estimated_duration_seconds": 120
}
```

#### Check Research Status

```bash
curl http://localhost:8080/api/v1/research/res_7f3d2a1b9c5e/status
```

#### Stream Real-time Progress

```bash
curl -N http://localhost:8080/api/v1/research/res_7f3d2a1b9c5e/stream
```

#### Get Final Report

```bash
# HTML format (default)
curl http://localhost:8080/api/v1/research/res_7f3d2a1b9c5e/report

# JSON format
curl http://localhost:8080/api/v1/research/res_7f3d2a1b9c5e/report?format=json
```

### Python Client Example

```python
import httpx
import asyncio

async def research(query):
    async with httpx.AsyncClient() as client:
        # Start research
        response = await client.post(
            "http://localhost:8080/api/v1/research",
            json={
                "query": query,
                "options": {"depth": "standard"}
            }
        )
        task = response.json()

        # Wait for completion
        while True:
            status = await client.get(
                f"http://localhost:8080/api/v1/research/{task['task_id']}/status"
            )
            data = status.json()

            print(f"Progress: {data['progress']['percentage']}%")

            if data["status"] == "completed":
                break

            await asyncio.sleep(5)

        # Get report
        report = await client.get(
            f"http://localhost:8080/api/v1/research/{task['task_id']}/report",
            params={"format": "json"}
        )

        return report.json()

# Run research
result = asyncio.run(research("AI breakthroughs 2025"))
print(result["executive_summary"])
```

## API Documentation

### Interactive API Docs

Once the service is running, visit:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research` | Start new research task |
| GET | `/api/v1/research/{task_id}/status` | Get task status |
| GET | `/api/v1/research/{task_id}/report` | Get research report |
| GET | `/api/v1/research/{task_id}/stream` | Stream progress (SSE) |
| DELETE | `/api/v1/research/{task_id}` | Cancel research task |
| POST | `/api/v1/research/{task_id}/export` | Export report (PDF/DOCX) |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

## Development

### Project Structure

```
research-agent/
├── docs/                    # Documentation
│   ├── DESIGN.md           # System design
│   ├── API.md              # API specification
│   └── ARCHITECTURE.md     # Architecture diagrams
├── src/                    # Source code
│   ├── agent/             # Core agent logic
│   ├── clients/           # External service clients
│   ├── models/            # Data models
│   ├── services/          # Business services
│   └── utils/             # Utilities
├── tests/                  # Test suite
├── config/                 # Configuration files
├── templates/              # HTML templates
└── static/                 # Static assets
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_orchestrator.py
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src

# Linting
pylint src
```

## Monitoring

### Health Endpoints

```bash
# Basic health check
curl http://localhost:8080/health

# Readiness check (includes service dependencies)
curl http://localhost:8080/ready

# Prometheus metrics
curl http://localhost:8080/metrics
```

### Logging

Logs are written to:
- Console (stdout) - structured JSON format
- File - `logs/research-agent.log` with rotation

### Metrics

Key metrics exposed:
- Request count and latency
- Research task duration
- Content fetch success rate
- Cache hit rates
- LLM response times

## Docker Deployment

### Build Image

```bash
docker build -t research-agent:latest .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

### Environment Variables for Docker

```yaml
environment:
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
  - MCP_SEARXNG_URL=http://host.docker.internal:8090
  - REDIS_HOST=redis
  - API_HOST=0.0.0.0
  - API_PORT=8080
```

## Troubleshooting

### Common Issues

#### Ollama Connection Failed
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify model is available
ollama list | grep gpt-oss
```

#### MCP Server Not Accessible
```bash
# Check MCP server is running
docker ps | grep searxng-mcp-server

# Test MCP server directly
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}' | \
  docker run --rm -i searxng-mcp-server:latest
```

#### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# If using Docker
docker-compose ps redis
```

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG uvicorn src.main:app --reload
```

## Performance Tuning

### Optimization Tips

1. **Increase Worker Count**: Set `API_WORKERS` based on CPU cores
2. **Adjust Concurrent Fetches**: Modify `MAX_CONCURRENT_FETCHES`
3. **Cache TTL**: Tune cache expiration times in config
4. **Redis Memory**: Configure Redis maxmemory policy
5. **Ollama Context**: Adjust context_length for better synthesis

### Scaling

For high load:
```yaml
# docker-compose.scale.yml
services:
  research-agent:
    deploy:
      replicas: 3

  nginx:
    image: nginx:alpine
    depends_on:
      - research-agent
    ports:
      - "80:80"
```

## Security Considerations

- **Rate Limiting**: Configurable per endpoint
- **Input Validation**: Query length and content limits
- **URL Filtering**: Blocklist for malicious domains
- **Content Sanitization**: XSS prevention in reports
- **No External APIs**: All processing done locally

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review API specification in `/docs/API.md`

## Roadmap

### Phase 1 (Current)
- ✅ Core research functionality
- ✅ Ollama integration
- ✅ MCP/SearXNG search
- ✅ Basic HTML reports

### Phase 2 (Planned)
- [ ] PDF export
- [ ] Academic paper focus
- [ ] Multi-language support
- [ ] Knowledge graph builder

### Phase 3 (Future)
- [ ] Fine-tuned domain models
- [ ] Collaborative research
- [ ] API for third-party apps
- [ ] Research templates

## Acknowledgments

- Ollama for local LLM processing
- SearXNG for privacy-respecting search
- FastAPI for the excellent framework
- The open-source community