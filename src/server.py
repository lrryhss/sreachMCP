#!/usr/bin/env python3
"""SearXNG MCP Server implementation."""

import asyncio
import json
import sys
import signal
from typing import Any, Dict, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from structlog import get_logger, configure, PrintLoggerFactory
from structlog.processors import JSONRenderer, TimeStamper, add_log_level

from config import Config
from searxng_client import SearXNGClient
from tools import SearchTool, ToolRegistry


# Configure structured logging to stderr
configure(
    processors=[
        TimeStamper(fmt="iso"),
        add_log_level,
        JSONRenderer()
    ],
    logger_factory=PrintLoggerFactory(file=sys.stderr)
)

logger = get_logger()


class SearXNGMCPServer:
    """MCP server for SearXNG search integration."""

    def __init__(self, config: Config):
        """Initialize the MCP server.

        Args:
            config: Server configuration
        """
        self.config = config
        self.server = Server("searxng-mcp")
        self.tool_registry = ToolRegistry()
        self.client = None

        # Setup auth if configured
        auth = None
        if config.searxng_auth_user and config.searxng_auth_pass:
            auth = (config.searxng_auth_user, config.searxng_auth_pass)

        self.client_auth = auth

    async def initialize(self):
        """Initialize the server and register handlers."""
        logger.info(
            "Initializing SearXNG MCP Server",
            transport=self.config.transport,
            searxng_url=self.config.searxng_url
        )

        # Create SearXNG client
        self.client = SearXNGClient(
            base_url=self.config.searxng_url,
            auth=self.client_auth,
            timeout=self.config.request_timeout,
            max_retries=self.config.retry_attempts
        )

        # Check SearXNG availability
        async with self.client as client:
            if await client.health_check():
                logger.info("SearXNG instance is available")
            else:
                logger.warning("SearXNG instance health check failed")

        # Register search tool
        search_tool = SearchTool(self.client)
        self.tool_registry.register_tool(search_tool)

        # Register MCP handlers
        @self.server.list_tools()
        async def list_tools() -> list[dict]:
            """List available tools."""
            tools = self.tool_registry.list_tools()
            logger.debug(f"Listing {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
            """Execute a tool."""
            logger.info(f"Tool call requested", tool_name=name, arguments=arguments)

            tool = self.tool_registry.get_tool(name)
            if not tool:
                error_msg = f"Tool '{name}' not found"
                logger.error(error_msg)
                return {"error": error_msg}

            async with self.client as client:
                result = await tool.execute(arguments)
                logger.debug(f"Tool execution completed", tool_name=name, success=result.get("success"))
                return result

        logger.info("Server initialization complete")

    async def run_stdio(self):
        """Run the server in stdio mode."""
        logger.info("Starting server in stdio mode")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

    async def run_sse(self):
        """Run the server in SSE mode."""
        # SSE implementation would go here
        # For now, we'll focus on stdio mode
        raise NotImplementedError("SSE transport not yet implemented")

    async def run(self):
        """Run the server based on configured transport."""
        await self.initialize()

        if self.config.transport == "stdio":
            await self.run_stdio()
        elif self.config.transport == "sse":
            await self.run_sse()
        else:
            raise ValueError(f"Unknown transport: {self.config.transport}")


async def main():
    """Main entry point."""
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Shutdown signal received")
        for task in asyncio.all_tasks():
            task.cancel()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Load configuration
        config = Config.from_env()

        # Configure logging level
        import logging
        logging.basicConfig(level=getattr(logging, config.log_level))

        # Log container environment info
        logger.info(
            "Starting SearXNG MCP Server",
            version="0.1.0",
            container_mode=True if sys.platform == "linux" else False,
            searxng_url=config.searxng_url
        )

        # Create and run server
        server = SearXNGMCPServer(config)
        await server.run()

    except asyncio.CancelledError:
        logger.info("Server shutdown complete")
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())