# SearXNG MCP Server Design Document

## Executive Summary

This document outlines the design and architecture for a Model Context Protocol (MCP) server that integrates with a SearXNG search container. The server will provide privacy-respecting search capabilities to AI assistants and LLM applications through a standardized protocol.

## System Overview

### Purpose
Create an MCP server that:
- Connects to an existing SearXNG container instance
- Exposes search functionality through the MCP protocol
- Enables AI assistants to perform web searches while preserving privacy
- Supports both stdio and SSE transport protocols

### Key Components
1. **MCP Server**: Core server implementation handling protocol communication
2. **SearXNG Client**: API client for interacting with SearXNG container
3. **Search Tools**: Exposed tools for AI assistant consumption
4. **Configuration Layer**: Environment-based configuration management

## Architecture

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        A[AI Assistant<br/>Claude/VSCode/etc]
    end

    subgraph "MCP Server"
        B[MCP Protocol Handler<br/>JSON-RPC 2.0]
        C[Tool Registry]
        D[SearXNG Client]
    end

    subgraph "Search Engine"
        E[SearXNG Container<br/>Port 8888]
        F[Search Engines<br/>Google, Bing, DuckDuckGo, etc]
    end

    A <-->|"MCP Protocol<br/>(stdio/SSE)"| B
    B --> C
    C --> D
    D <-->|"HTTP/REST API"| E
    E <-->|"Meta Search"| F

    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#f3e5f5
```

### Component Details

#### 1. MCP Server Core
- **Protocol**: JSON-RPC 2.0 over stdio or SSE
- **Language**: Python 3.9+
- **Responsibilities**:
  - Handle MCP protocol communication
  - Manage client connections
  - Route requests to appropriate handlers
  - Implement capability negotiation

#### 2. SearXNG Client Module
- **Purpose**: Abstract SearXNG API interactions
- **Features**:
  - Connection management
  - Request formatting
  - Response parsing
  - Error handling and retries
  - Authentication support (if required)

#### 3. Search Tool Implementation
- **Tool Name**: `search_web`
- **Parameters**:
  - `query` (string, required): Search query
  - `category` (string, optional): web, images, news, videos, files
  - `language` (string, optional): Language code (e.g., en, es, fr)
  - `time_range` (string, optional): day, month, year, all
  - `limit` (integer, optional): Number of results (default: 10)
  - `engines` (array, optional): Specific search engines to use

## API Specifications

### MCP Protocol Methods

#### Initialize Connection
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "0.1.0",
    "capabilities": {
      "tools": {}
    }
  }
}
```

#### Search Tool Invocation
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_web",
    "arguments": {
      "query": "example search",
      "category": "web",
      "limit": 10
    }
  }
}
```

### SearXNG API Integration

#### Search Endpoint
- **URL**: `{SEARXNG_BASE_URL}/search`
- **Method**: GET or POST
- **Parameters**:
  ```
  q: search query
  categories: comma-separated categories
  engines: comma-separated engines
  language: language code
  time_range: time filter
  format: json
  ```

#### Response Format
```json
{
  "results": [
    {
      "url": "https://example.com",
      "title": "Result Title",
      "content": "Result description...",
      "engine": "google",
      "score": 0.95
    }
  ],
  "number_of_results": 100,
  "query": "search query"
}
```

## Implementation Details

### Project Structure
```
searxng-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py           # Main MCP server
│   ├── searxng_client.py   # SearXNG API client
│   ├── tools.py            # Tool definitions
│   ├── config.py           # Configuration management
│   └── utils.py            # Utility functions
├── tests/
│   ├── test_server.py
│   ├── test_client.py
│   └── test_tools.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── package.json            # MCP configuration
├── Dockerfile              # Optional containerization
└── README.md
```

### Core Classes and Functions

#### Class Diagram

```mermaid
classDiagram
    class SearXNGMCPServer {
        -Config config
        -SearXNGClient client
        -ToolRegistry tools
        +__init__(config: Config)
        +handle_request(request: dict) dict
        +initialize(params: dict) dict
        +call_tool(name: str, args: dict) dict
        +start_server() void
    }

    class SearXNGClient {
        -str base_url
        -Optional~dict~ auth
        -AsyncClient session
        +__init__(base_url: str, auth: Optional~dict~)
        +search(query: str, **kwargs) dict
        +health_check() bool
        +format_results(raw_results: dict) list
    }

    class ToolRegistry {
        -dict tools
        +register_tool(name: str, handler: callable) void
        +get_tool(name: str) callable
        +list_tools() list
    }

    class Config {
        +str searxng_url
        +str transport
        +str host
        +int port
        +str log_level
        +from_env() Config
    }

    class SearchTool {
        -SearXNGClient client
        +execute(params: dict) dict
        +validate_params(params: dict) bool
    }

    SearXNGMCPServer --> SearXNGClient
    SearXNGMCPServer --> ToolRegistry
    SearXNGMCPServer --> Config
    ToolRegistry --> SearchTool
    SearchTool --> SearXNGClient
```

#### Sequence Diagram for Search Request

```mermaid
sequenceDiagram
    participant AI as AI Assistant
    participant MCP as MCP Server
    participant TR as Tool Registry
    participant ST as Search Tool
    participant SC as SearXNG Client
    participant SX as SearXNG Container

    AI->>MCP: tools/call (search_web)
    MCP->>TR: get_tool("search_web")
    TR->>MCP: return SearchTool
    MCP->>ST: execute(params)
    ST->>ST: validate_params()
    ST->>SC: search(query, options)
    SC->>SX: GET /search?q=query
    SX->>SC: JSON results
    SC->>SC: format_results()
    SC->>ST: formatted results
    ST->>MCP: tool response
    MCP->>AI: JSON-RPC response
```

### Error Handling Strategy

```mermaid
stateDiagram-v2
    [*] --> Request
    Request --> Validation

    Validation --> Execute: Valid
    Validation --> Error: Invalid

    Execute --> Success: OK
    Execute --> Retry: Retryable Error
    Execute --> Error: Fatal Error

    Retry --> Execute: Attempts < Max
    Retry --> Error: Max Attempts

    Success --> Format
    Format --> [*]

    Error --> LogError
    LogError --> ReturnError
    ReturnError --> [*]

    note right of Retry
        Exponential backoff:
        1s, 2s, 4s, 8s
    end note

    note right of Error
        Error Types:
        - Connection Failed
        - Invalid Parameters
        - SearXNG Unavailable
        - Rate Limited
        - Malformed Response
    end note
```

1. **Connection Errors**: Retry with exponential backoff
2. **Invalid Parameters**: Return descriptive error messages
3. **SearXNG Unavailable**: Cache last known good configuration
4. **Rate Limiting**: Implement request throttling
5. **Malformed Responses**: Graceful degradation with partial results

## Configuration

### Environment Variables
```env
# Required
SEARXNG_BASE_URL=http://localhost:8888

# Optional
SEARXNG_AUTH_USER=username
SEARXNG_AUTH_PASS=password
MCP_TRANSPORT=stdio  # or sse
MCP_HOST=127.0.0.1
MCP_PORT=32769
LOG_LEVEL=INFO
MAX_RESULTS=50
DEFAULT_LANGUAGE=en
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "searxng": {
      "command": "python",
      "args": ["/path/to/searxng-mcp-server/src/server.py"],
      "env": {
        "SEARXNG_BASE_URL": "http://localhost:8888"
      }
    }
  }
}
```

### SSE Transport Configuration
```json
{
  "mcpServers": {
    "searxng": {
      "transport": "sse",
      "url": "http://localhost:32769/sse",
      "env": {
        "SEARXNG_BASE_URL": "http://localhost:8888"
      }
    }
  }
}
```

## Deployment

### Deployment Architecture

```mermaid
graph LR
    subgraph "Development Environment"
        A1[Local MCP Server]
        A2[Local SearXNG]
        A3[Claude Desktop]
        A1 <--> A2
        A3 <--> A1
    end

    subgraph "Docker Compose Stack"
        B1[MCP Container]
        B2[SearXNG Container]
        B3[Network Bridge]
        B1 <--> B3
        B2 <--> B3
    end

    subgraph "Production Environment"
        C1[MCP Server Cluster]
        C2[Load Balancer]
        C3[SearXNG Instances]
        C4[Redis Cache]
        C2 --> C1
        C1 <--> C3
        C1 <--> C4
    end

    style A1 fill:#e8f5e9
    style B1 fill:#e3f2fd
    style C1 fill:#fff3e0
```

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd searxng-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your SearXNG container URL

# Run server
python src/server.py
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio

CMD ["python", "src/server.py"]
```

### Docker Compose Integration
```yaml
version: '3.8'

services:
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8888:8080"
    volumes:
      - ./searxng:/etc/searxng

  mcp-server:
    build: .
    environment:
      - SEARXNG_BASE_URL=http://searxng:8080
      - MCP_TRANSPORT=sse
      - MCP_PORT=32769
    ports:
      - "32769:32769"
    depends_on:
      - searxng
```

## Security Considerations

### Authentication & Authorization
- Support for SearXNG instances with basic authentication
- Token-based authentication for production deployments
- Rate limiting per client connection

### Data Privacy
- No logging of search queries by default
- Optional audit logging with user consent
- Result sanitization to prevent XSS attacks
- No persistent storage of search history

### Network Security
- HTTPS support for production deployments
- Proxy support for corporate environments
- Connection encryption for SSE transport

## Testing Strategy

### Test Flow Diagram

```mermaid
flowchart TD
    A[Start Testing] --> B{Test Type}
    B -->|Unit| C[Component Tests]
    B -->|Integration| D[System Tests]
    B -->|E2E| E[End-to-End Tests]

    C --> C1[Test SearXNGClient]
    C --> C2[Test ToolRegistry]
    C --> C3[Test Config]
    C --> C4[Test SearchTool]

    D --> D1[Test MCP Protocol]
    D --> D2[Test SearXNG Connection]
    D --> D3[Test Transport Layers]

    E --> E1[Test with Claude Desktop]
    E --> E2[Test with VSCode]
    E --> E3[Performance Tests]

    C1 & C2 & C3 & C4 --> F[Unit Test Report]
    D1 & D2 & D3 --> G[Integration Test Report]
    E1 & E2 & E3 --> H[E2E Test Report]

    F & G & H --> I[Coverage Report]
    I --> J{Coverage >= 80%}
    J -->|Yes| K[Deploy]
    J -->|No| L[Fix Coverage]
    L --> A
```

### Unit Tests
- Test individual components in isolation
- Mock SearXNG API responses
- Validate parameter handling
- Error condition testing

### Integration Tests
- Test full request/response flow
- Verify SearXNG connectivity
- Transport protocol testing
- Performance benchmarking

### Test Coverage Goals
- Minimum 80% code coverage
- All error paths tested
- All tool parameters validated
- Transport switching tested

## Performance Considerations

### Optimization Strategies
1. **Connection Pooling**: Reuse HTTP connections to SearXNG
2. **Response Caching**: Cache frequent searches (configurable TTL)
3. **Async Operations**: Non-blocking I/O for all network calls
4. **Result Streaming**: Stream large result sets
5. **Request Batching**: Combine multiple searches when possible

### Scalability
- Horizontal scaling through multiple server instances
- Load balancing for SSE transport
- Connection limits per instance
- Resource monitoring and alerts

## Monitoring & Logging

### Metrics to Track
- Request count and latency
- Error rates by type
- SearXNG availability
- Search result quality scores
- Client connection statistics

### Logging Configuration
```python
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'mcp-server.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    }
}
```

## Future Enhancements

### Development Roadmap

```mermaid
gantt
    title SearXNG MCP Server Development Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1 MVP
    Basic Search Function    :a1, 2025-01-20, 7d
    Stdio Transport          :a2, after a1, 5d
    Claude Integration       :a3, after a2, 3d
    Basic Error Handling     :a4, after a2, 3d

    section Phase 2
    SSE Transport           :b1, after a3, 7d
    Advanced Parameters     :b2, after a3, 5d
    Result Caching          :b3, after b1, 5d
    Performance Optimize    :b4, after b3, 7d

    section Phase 3
    Multi-Instance Support  :c1, after b4, 10d
    Custom Engines          :c2, after c1, 7d
    Result Processing       :c3, after c1, 5d
    Analytics Dashboard     :c4, after c2, 10d

    section Phase 4
    Plugin Architecture     :d1, after c4, 14d
    Custom Formatters       :d2, after d1, 7d
    AI Result Ranking       :d3, after d1, 10d
    Multi-Language          :d4, after d2, 7d
```

### Phase 1 (MVP)
- Basic search functionality
- Stdio transport support
- Claude Desktop integration
- Basic error handling

### Phase 2
- SSE transport support
- Advanced search parameters
- Result caching
- Performance optimizations

### Phase 3
- Multiple SearXNG instance support
- Custom search engines
- Result post-processing
- Analytics dashboard

### Phase 4
- Plugin architecture for extensions
- Custom result formatters
- AI-powered result ranking
- Multi-language support

## Appendix

### Dependencies
```txt
# Core
mcp>=0.1.0
httpx>=0.24.0
python-dotenv>=1.0.0

# Async support
asyncio>=3.4.3
aiohttp>=3.8.0

# Utils
pydantic>=2.0.0
structlog>=23.0.0

# Development
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
mypy>=1.0.0
```

### References
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [SearXNG Documentation](https://docs.searxng.org)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### License
MIT License - See LICENSE file for details

### Contributors
- Initial Design: [Your Name]
- Review: [Team Members]

### Version History
- v0.1.0 - Initial design document
- Date: 2025-09-17