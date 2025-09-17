"""MCP tool definitions for SearXNG search."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from searxng_client import SearXNGClient
from structlog import get_logger

logger = get_logger()


class SearchParams(BaseModel):
    """Parameters for search tool."""

    query: str = Field(..., description="Search query string")
    category: Optional[str] = Field(
        None,
        description="Search category: web, images, news, videos, files"
    )
    language: Optional[str] = Field(
        None,
        description="Language code (e.g., en, es, fr)"
    )
    time_range: Optional[str] = Field(
        None,
        description="Time filter: day, month, year, all"
    )
    limit: Optional[int] = Field(
        10,
        description="Maximum number of results (default: 10)"
    )
    engines: Optional[List[str]] = Field(
        None,
        description="Specific search engines to use"
    )


class SearchTool:
    """Search tool implementation for MCP."""

    def __init__(self, client: SearXNGClient):
        """Initialize the search tool.

        Args:
            client: SearXNG client instance
        """
        self.client = client

    @property
    def name(self) -> str:
        """Tool name."""
        return "search_web"

    @property
    def description(self) -> str:
        """Tool description."""
        return "Search the web using SearXNG metasearch engine"

    @property
    def parameters(self) -> Dict[str, Any]:
        """Tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string"
                },
                "category": {
                    "type": "string",
                    "enum": ["web", "images", "news", "videos", "files"],
                    "description": "Search category"
                },
                "language": {
                    "type": "string",
                    "description": "Language code (e.g., en, es, fr)"
                },
                "time_range": {
                    "type": "string",
                    "enum": ["day", "month", "year", "all"],
                    "description": "Time filter"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                },
                "engines": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific search engines to use"
                }
            },
            "required": ["query"]
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the search tool.

        Args:
            params: Tool parameters

        Returns:
            Search results
        """
        try:
            # Validate parameters
            search_params = SearchParams(**params)

            logger.info(
                "Executing search",
                query=search_params.query,
                category=search_params.category
            )

            # Perform search using the client context manager
            async with self.client as client:
                results = await client.search(
                    query=search_params.query,
                    category=search_params.category,
                    engines=search_params.engines,
                    language=search_params.language,
                    time_range=search_params.time_range,
                    limit=search_params.limit or 10
                )

            # Format response for MCP
            formatted_results = self._format_for_mcp(results)

            return {
                "success": True,
                "data": formatted_results
            }

        except Exception as e:
            logger.error("Search tool execution failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def _format_for_mcp(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format search results for MCP response.

        Args:
            results: Raw search results

        Returns:
            Formatted results for MCP
        """
        formatted = {
            "query": results.get("query", ""),
            "result_count": results.get("number_of_results", 0),
            "response_time": results.get("response_time", 0),
            "results": []
        }

        for result in results.get("results", []):
            formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", ""),
                "source": result.get("engine", "")
            }

            # Add optional fields
            if "score" in result:
                formatted_result["relevance_score"] = result["score"]
            if "published_date" in result:
                formatted_result["published_date"] = result["published_date"]
            if "image_url" in result:
                formatted_result["image_url"] = result["image_url"]

            formatted["results"].append(formatted_result)

        return formatted


class ToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, SearchTool] = {}

    def register_tool(self, tool: SearchTool):
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        logger.info("Tool registered", tool_name=tool.name)

    def get_tool(self, name: str) -> Optional[SearchTool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.

        Returns:
            List of tool descriptions
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            for tool in self.tools.values()
        ]