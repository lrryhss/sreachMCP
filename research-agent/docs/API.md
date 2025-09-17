# Research Agent API Specification

## API Version: 1.0.0

### Base URL
```
http://localhost:8080/api/v1
```

## Authentication
Currently, the API does not require authentication for local deployment. Future versions will support API key authentication.

## Content Types
- Request: `application/json`
- Response: `application/json` (except HTML reports)

## Rate Limiting
- Default: 100 requests per minute per IP
- Research endpoints: 10 concurrent research tasks per IP

## Endpoints

### 1. Research Operations

#### Start New Research
Initiates a new research task asynchronously.

```http
POST /research
```

**Request Body:**
```json
{
  "query": "string (required, max 500 chars)",
  "options": {
    "depth": "quick | standard | comprehensive",
    "max_sources": "integer (5-50, default: 20)",
    "languages": ["en", "es", "fr"],
    "time_range": "day | week | month | year | all",
    "include_pdfs": "boolean (default: true)",
    "include_academic": "boolean (default: false)",
    "follow_links": "boolean (default: true)",
    "custom_instructions": "string (optional, max 1000 chars)"
  },
  "output_format": "html | json | markdown",
  "webhook_url": "string (optional, URL for completion callback)"
}
```

**Response:**
```json
{
  "task_id": "res_7f3d2a1b9c5e",
  "status": "accepted",
  "estimated_duration_seconds": 120,
  "created_at": "2025-09-17T10:30:00Z",
  "links": {
    "status": "/api/v1/research/res_7f3d2a1b9c5e/status",
    "report": "/api/v1/research/res_7f3d2a1b9c5e/report",
    "stream": "/api/v1/research/res_7f3d2a1b9c5e/stream"
  }
}
```

**Status Codes:**
- `202 Accepted`: Research task started
- `400 Bad Request`: Invalid parameters
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: System overloaded

---

#### Get Research Status
Retrieves the current status of a research task.

```http
GET /research/{task_id}/status
```

**Path Parameters:**
- `task_id`: String (required) - The research task identifier

**Response:**
```json
{
  "task_id": "res_7f3d2a1b9c5e",
  "status": "processing | completed | failed",
  "progress": {
    "percentage": 65,
    "current_step": "content_extraction",
    "steps_completed": [
      "query_analysis",
      "search_execution",
      "url_collection"
    ],
    "steps_remaining": [
      "content_extraction",
      "synthesis",
      "report_generation"
    ],
    "sources_found": 25,
    "sources_processed": 15
  },
  "started_at": "2025-09-17T10:30:00Z",
  "updated_at": "2025-09-17T10:31:30Z",
  "estimated_completion": "2025-09-17T10:32:00Z",
  "error": null
}
```

**Status Codes:**
- `200 OK`: Status retrieved
- `404 Not Found`: Task not found

---

#### Get Research Report
Retrieves the completed research report.

```http
GET /research/{task_id}/report
```

**Path Parameters:**
- `task_id`: String (required)

**Query Parameters:**
- `format`: `html | json | markdown` (optional, default: html)

**Response (JSON format):**
```json
{
  "task_id": "res_7f3d2a1b9c5e",
  "query": "Latest developments in quantum computing",
  "status": "completed",
  "metadata": {
    "total_sources": 25,
    "sources_used": 20,
    "processing_time_seconds": 118,
    "report_generated_at": "2025-09-17T10:32:00Z"
  },
  "executive_summary": "string (200-500 words)",
  "key_findings": [
    {
      "finding": "string",
      "confidence": 0.95,
      "supporting_sources": [1, 3, 5]
    }
  ],
  "detailed_analysis": {
    "sections": [
      {
        "title": "string",
        "content": "string (markdown formatted)",
        "sources": [1, 2, 3]
      }
    ]
  },
  "sources": [
    {
      "id": 1,
      "title": "string",
      "url": "string",
      "author": "string",
      "published_date": "2025-09-15",
      "relevance_score": 0.92,
      "summary": "string (100-200 words)",
      "quotes": [
        {
          "text": "string",
          "context": "string"
        }
      ]
    }
  ],
  "related_topics": [
    "Quantum supremacy achievements",
    "Commercial quantum applications"
  ],
  "further_research": [
    "Specific quantum algorithm improvements",
    "Hardware limitations and solutions"
  ]
}
```

**Response (HTML format):**
Returns a complete HTML document with embedded CSS and optional JavaScript for interactivity.

**Status Codes:**
- `200 OK`: Report ready
- `202 Accepted`: Report still processing
- `404 Not Found`: Task not found
- `410 Gone`: Report expired

---

#### Stream Research Progress (SSE)
Real-time updates via Server-Sent Events.

```http
GET /research/{task_id}/stream
```

**Event Stream Format:**
```
event: progress
data: {"step": "query_analysis", "message": "Analyzing research query", "percentage": 10}

event: source_found
data: {"url": "https://example.com", "title": "Example Article", "relevance": 0.89}

event: content_extracted
data: {"source_id": 5, "word_count": 2500, "extraction_method": "trafilatura"}

event: synthesis_update
data: {"message": "Synthesizing information from 15 sources", "percentage": 75}

event: complete
data: {"task_id": "res_7f3d2a1b9c5e", "report_url": "/api/v1/research/res_7f3d2a1b9c5e/report"}

event: error
data: {"error": "Rate limited by source", "recoverable": true}
```

---

#### Cancel Research Task
Cancels an ongoing research task.

```http
DELETE /research/{task_id}
```

**Response:**
```json
{
  "task_id": "res_7f3d2a1b9c5e",
  "status": "cancelled",
  "message": "Research task cancelled successfully"
}
```

**Status Codes:**
- `200 OK`: Task cancelled
- `404 Not Found`: Task not found
- `409 Conflict`: Task already completed

---

### 2. Export Operations

#### Export Report
Exports a report in various formats.

```http
POST /research/{task_id}/export
```

**Request Body:**
```json
{
  "format": "pdf | docx | markdown | json",
  "options": {
    "include_images": true,
    "include_charts": true,
    "paper_size": "letter | a4",
    "include_appendix": false
  }
}
```

**Response:**
```json
{
  "export_id": "exp_9a8b7c6d",
  "format": "pdf",
  "status": "processing",
  "download_url": "/api/v1/exports/exp_9a8b7c6d/download",
  "expires_at": "2025-09-17T11:32:00Z"
}
```

---

#### Download Export
Downloads an exported report file.

```http
GET /exports/{export_id}/download
```

**Response:**
Binary file with appropriate Content-Type header:
- PDF: `application/pdf`
- DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Markdown: `text/markdown`

---

### 3. Search Operations

#### Preview Search Results
Performs a quick search without full content extraction.

```http
POST /search/preview
```

**Request Body:**
```json
{
  "query": "string",
  "max_results": 10
}
```

**Response:**
```json
{
  "query": "quantum computing",
  "results": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string",
      "source": "google",
      "published_date": "2025-09-15"
    }
  ],
  "total_results": 150,
  "search_time_ms": 234
}
```

---

### 4. System Operations

#### Health Check
Basic health check endpoint.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-17T10:30:00Z"
}
```

---

#### Readiness Check
Checks if the service is ready to handle requests.

```http
GET /ready
```

**Response:**
```json
{
  "ready": true,
  "services": {
    "ollama": "connected",
    "mcp_server": "connected",
    "redis": "connected"
  }
}
```

---

#### Get System Metrics
Prometheus-compatible metrics endpoint.

```http
GET /metrics
```

**Response:**
```
# HELP research_requests_total Total number of research requests
# TYPE research_requests_total counter
research_requests_total 1234

# HELP research_duration_seconds Research task duration
# TYPE research_duration_seconds histogram
research_duration_seconds_bucket{le="30.0"} 100
research_duration_seconds_bucket{le="60.0"} 200
research_duration_seconds_bucket{le="120.0"} 350
```

---

#### Get API Version
Returns API version and capabilities.

```http
GET /version
```

**Response:**
```json
{
  "api_version": "1.0.0",
  "build_date": "2025-09-17",
  "capabilities": {
    "pdf_extraction": true,
    "academic_search": true,
    "streaming": true,
    "export_formats": ["pdf", "docx", "markdown", "json"]
  },
  "models": {
    "llm": "gpt-oss:20b",
    "embeddings": null
  }
}
```

---

### 5. Configuration Operations

#### Get Available Models
Lists available LLM models from Ollama.

```http
GET /config/models
```

**Response:**
```json
{
  "models": [
    {
      "name": "gpt-oss:20b",
      "size": "20B",
      "quantization": "Q4_K_M",
      "context_length": 8192,
      "active": true
    }
  ]
}
```

---

#### Get Search Engines
Lists available search engines via MCP.

```http
GET /config/engines
```

**Response:**
```json
{
  "engines": [
    {
      "name": "google",
      "enabled": true,
      "weight": 1.0
    },
    {
      "name": "bing",
      "enabled": true,
      "weight": 0.8
    },
    {
      "name": "duckduckgo",
      "enabled": true,
      "weight": 0.9
    }
  ]
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "field": "additional context"
    },
    "timestamp": "2025-09-17T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Codes

| Code | Description |
|------|------------|
| `INVALID_QUERY` | Query validation failed |
| `TASK_NOT_FOUND` | Research task does not exist |
| `RATE_LIMITED` | Too many requests |
| `SERVICE_UNAVAILABLE` | Ollama or MCP server unavailable |
| `CONTENT_FETCH_FAILED` | Failed to fetch web content |
| `SYNTHESIS_FAILED` | LLM synthesis error |
| `EXPORT_FAILED` | Export generation failed |
| `TIMEOUT` | Operation timed out |
| `INSUFFICIENT_SOURCES` | Not enough sources found |
| `INVALID_FORMAT` | Unsupported format requested |

---

## WebSocket Endpoint (Alternative to SSE)

### Research Progress WebSocket
```
ws://localhost:8080/ws/research/{task_id}
```

**Message Format (Client → Server):**
```json
{
  "type": "subscribe | unsubscribe | cancel",
  "task_id": "res_7f3d2a1b9c5e"
}
```

**Message Format (Server → Client):**
```json
{
  "type": "progress | source | synthesis | complete | error",
  "task_id": "res_7f3d2a1b9c5e",
  "timestamp": "2025-09-17T10:30:00Z",
  "data": {
    // Type-specific data
  }
}
```

---

## Rate Limiting Headers

All responses include rate limiting information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1694952000
X-RateLimit-Retry-After: 60
```

---

## CORS Configuration

For browser-based clients:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

---

## Request ID Tracking

All requests are assigned a unique ID for tracking:

```
X-Request-ID: req_7f3d2a1b9c5e4d6f
```

Include this ID when reporting issues or checking logs.

---

## Pagination

For endpoints that return lists:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  },
  "links": {
    "first": "/api/v1/resource?page=1",
    "last": "/api/v1/resource?page=5",
    "next": "/api/v1/resource?page=2",
    "prev": null
  }
}
```

---

## Webhooks

For async operations, webhooks can be configured:

**Webhook Payload:**
```json
{
  "event": "research.completed",
  "task_id": "res_7f3d2a1b9c5e",
  "timestamp": "2025-09-17T10:32:00Z",
  "data": {
    "status": "completed",
    "report_url": "https://your-domain.com/api/v1/research/res_7f3d2a1b9c5e/report"
  }
}
```

**Webhook Events:**
- `research.started`
- `research.progress`
- `research.completed`
- `research.failed`
- `research.cancelled`

---

## SDK Examples

### Python
```python
import httpx
import asyncio

async def research(query):
    async with httpx.AsyncClient() as client:
        # Start research
        response = await client.post(
            "http://localhost:8080/api/v1/research",
            json={"query": query, "options": {"depth": "comprehensive"}}
        )
        task = response.json()

        # Poll for completion
        while True:
            status = await client.get(
                f"http://localhost:8080/api/v1/research/{task['task_id']}/status"
            )
            if status.json()["status"] == "completed":
                break
            await asyncio.sleep(5)

        # Get report
        report = await client.get(
            f"http://localhost:8080/api/v1/research/{task['task_id']}/report"
        )
        return report.json()
```

### JavaScript
```javascript
async function research(query) {
  // Start research
  const startResponse = await fetch('http://localhost:8080/api/v1/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, options: { depth: 'standard' } })
  });
  const { task_id } = await startResponse.json();

  // Stream progress
  const eventSource = new EventSource(
    `http://localhost:8080/api/v1/research/${task_id}/stream`
  );

  return new Promise((resolve, reject) => {
    eventSource.addEventListener('complete', (event) => {
      eventSource.close();
      resolve(JSON.parse(event.data));
    });

    eventSource.addEventListener('error', (event) => {
      eventSource.close();
      reject(JSON.parse(event.data));
    });
  });
}
```

### cURL
```bash
# Start research
curl -X POST http://localhost:8080/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"query":"quantum computing breakthroughs","options":{"depth":"standard"}}'

# Check status
curl http://localhost:8080/api/v1/research/res_7f3d2a1b9c5e/status

# Get report
curl http://localhost:8080/api/v1/research/res_7f3d2a1b9c5e/report
```

---

## API Versioning

The API uses URL versioning. Current version: `v1`

Future versions will maintain backward compatibility for at least 6 months after deprecation notice.

Deprecated endpoints will include:
```
X-Deprecated: true
X-Sunset-Date: 2026-03-17
```