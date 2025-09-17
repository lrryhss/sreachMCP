# SearXNG MCP Server

A Model Context Protocol (MCP) server that integrates with SearXNG to provide privacy-respecting web search capabilities to AI assistants.

## Features

- 🔍 Web search through SearXNG metasearch engine
- 🔐 Privacy-focused search (no tracking)
- 🚀 Fast and efficient MCP integration
- 📦 Easy setup with Claude Code CLI
- 🔧 Configurable search parameters

## Prerequisites

- Docker (for containerized deployment) OR Python 3.9+ (for local deployment)
- SearXNG instance running (default: http://localhost:8090)
- Claude Code CLI

## Installation

Choose one of the following installation methods:

### Option 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd searxng-mcp-server
```

2. Build the Docker image:
```bash
docker build -t searxng-mcp-server:latest .
```

3. Run with Docker Compose (if you don't have SearXNG running):
```bash
docker-compose up -d
```

Or run standalone (if you already have SearXNG running):
```bash
docker run --rm -it \
  --add-host=host.docker.internal:host-gateway \
  -e SEARXNG_BASE_URL=http://host.docker.internal:8090 \
  searxng-mcp-server:latest
```

### Option 2: Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd searxng-mcp-server
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and set your SearXNG URL (default: http://localhost:8090)
```

## Configuration

Edit `.env` file to configure your SearXNG instance:

```env
# Your SearXNG instance URL
SEARXNG_BASE_URL=http://localhost:8888

# Optional authentication
# SEARXNG_AUTH_USER=username
# SEARXNG_AUTH_PASS=password
```

## Testing

Run the test script to verify connectivity:

```bash
./venv/bin/python tests/test_connection.py
```

This will:
- Check SearXNG connectivity
- Perform a test search
- Verify MCP server initialization

## Adding to Claude Code CLI

### Configuration File: `.mcp.json`

Create or update `.mcp.json` in your project root:

#### For Docker Installation

```json
{
  "mcpServers": {
    "searxng": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e",
        "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e",
        "LOG_LEVEL=ERROR",
        "searxng-mcp-server:latest"
      ]
    }
  }
}
```

#### For Local Installation

```json
{
  "mcpServers": {
    "searxng": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/searxng-mcp-server/src/server.py"],
      "env": {
        "SEARXNG_BASE_URL": "http://localhost:8090",
        "LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

Replace `/path/to/` with the actual paths to your virtual environment and project directory.

### Enable MCP Servers in Claude Code

Add to `.claude/settings.local.json`:

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["searxng"]
}
```

## Usage

Once configured, you can use the search tool in Claude Code:

- "Search for Python programming tutorials"
- "Find recent news about artificial intelligence"
- "Look up documentation for MCP protocol"

### Search Parameters

The search tool accepts the following parameters:

- `query` (required): Search query string
- `category`: web, images, news, videos, files
- `language`: Language code (e.g., en, es, fr)
- `time_range`: day, month, year, all
- `limit`: Maximum number of results (default: 10)
- `engines`: Specific search engines to use

## Running SearXNG with Docker

If you don't have a SearXNG instance, you can quickly start one with Docker:

```bash
docker run -d \
  --name searxng \
  -p 8888:8080 \
  -v ./searxng:/etc/searxng \
  -e BASE_URL=http://localhost:8888/ \
  --restart unless-stopped \
  searxng/searxng:latest
```

## Troubleshooting

### MCP Server Not Showing in Claude Code

1. Check if Docker is running:
```bash
docker ps
```

2. Verify the Docker image exists:
```bash
docker images | grep searxng-mcp-server
```

3. Check MCP logs:
```bash
ls ~/.cache/claude-cli-nodejs/*/mcp-logs-searxng/
```

4. Test the server manually:
```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "1.0.0", "capabilities": {}}, "id": 1}' | \
docker run --rm -i --add-host=host.docker.internal:host-gateway \
-e SEARXNG_BASE_URL=http://host.docker.internal:8090 \
-e LOG_LEVEL=ERROR searxng-mcp-server:latest 2>/dev/null
```

### SearXNG not accessible

1. Check if SearXNG is running:
```bash
curl http://localhost:8090
docker ps | grep searxng
```

2. Verify the URL in `.mcp.json` matches your SearXNG instance port

3. For WSL users, ensure `host.docker.internal` resolves correctly

### Common Issues and Fixes

#### "Connection closed" error
- **Issue**: Server output interfering with JSON-RPC protocol
- **Fix**: Ensure `LOG_LEVEL=ERROR` is set to minimize output

#### Docker image not found
- **Issue**: Image not built
- **Fix**: Build the image first:
```bash
docker build -t searxng-mcp-server:latest .
```

#### Port mismatch
- **Issue**: SearXNG running on different port than configured
- **Fix**: Update `SEARXNG_BASE_URL` in `.mcp.json` to match actual port

## Development

### Project Structure

```
searxng-mcp-server/
├── src/
│   ├── server.py           # Main MCP server
│   ├── searxng_client.py   # SearXNG API client
│   ├── tools.py            # MCP tool definitions
│   └── config.py           # Configuration management
├── tests/
│   └── test_connection.py  # Connection test script
├── .claude/
│   └── settings.local.json # Claude Code settings
├── .mcp.json               # MCP server configuration
├── .env.example            # Environment template
├── docker-entrypoint.sh    # Docker entrypoint script
├── docker-compose.yml      # Docker compose configuration
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
```

### Running in Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run server directly
python src/server.py

# Run with environment variables
SEARXNG_BASE_URL=http://localhost:8888 python src/server.py
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on GitHub.