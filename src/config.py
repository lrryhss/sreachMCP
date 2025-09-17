"""Configuration management for SearXNG MCP Server."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Server configuration."""

    # SearXNG settings
    searxng_url: str = Field(
        default="http://localhost:8888",
        description="Base URL for SearXNG instance"
    )
    searxng_auth_user: Optional[str] = Field(
        default=None,
        description="Username for SearXNG authentication"
    )
    searxng_auth_pass: Optional[str] = Field(
        default=None,
        description="Password for SearXNG authentication"
    )

    # MCP settings
    transport: str = Field(
        default="stdio",
        description="MCP transport type (stdio or sse)"
    )
    host: str = Field(
        default="127.0.0.1",
        description="Host for SSE transport"
    )
    port: int = Field(
        default=32769,
        description="Port for SSE transport"
    )

    # Search settings
    max_results: int = Field(
        default=10,
        description="Maximum number of search results"
    )
    default_language: str = Field(
        default="en",
        description="Default search language"
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed requests"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            searxng_url=os.getenv("SEARXNG_BASE_URL", "http://localhost:8888"),
            searxng_auth_user=os.getenv("SEARXNG_AUTH_USER"),
            searxng_auth_pass=os.getenv("SEARXNG_AUTH_PASS"),
            transport=os.getenv("MCP_TRANSPORT", "stdio"),
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "32769")),
            max_results=int(os.getenv("MAX_RESULTS", "10")),
            default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )