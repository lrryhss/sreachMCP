"""MCP Server client for SearXNG search integration"""

import json
import asyncio
import subprocess
import httpx
from typing import Dict, List, Optional, Any
from structlog import get_logger

logger = get_logger()


class MCPSearchClient:
    """Client for interacting with SearXNG MCP Server"""

    def __init__(self, timeout: int = 30, searxng_url: str = "http://localhost:8090"):
        """Initialize MCP client

        Args:
            timeout: Request timeout in seconds
            searxng_url: Direct URL to SearXNG instance for fallback
        """
        self.timeout = timeout
        self.searxng_url = searxng_url
        # The MCP server container is already running, we'll restart it for each request
        # This is not ideal but works with the current stdio-based MCP protocol
        self.container_name = "stoic_taussig"  # TODO: Make configurable

    async def search(
        self,
        query: str,
        category: str = "web",
        limit: int = 10,
        language: str = "en",
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute search via MCP server

        Args:
            query: Search query
            category: Search category (web, images, news, etc.)
            limit: Maximum number of results
            language: Language code
            time_range: Time filter (day, month, year, all)

        Returns:
            Search results from SearXNG
        """
        # Prepare JSON-RPC request for search tool
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_web",
                "arguments": {
                    "query": query,
                    "category": category,
                    "limit": limit,
                    "language": language
                }
            },
            "id": 2
        }

        if time_range:
            request["params"]["arguments"]["time_range"] = time_range

        try:
            # First initialize the MCP connection
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "research-agent",
                        "version": "1.0.0"
                    }
                },
                "id": 0
            }

            # Send initialization notification after init request
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }

            # Run the MCP server with proper sequence: init, initialized notification, then request
            full_input = json.dumps(init_request) + "\n" + json.dumps(initialized_notification) + "\n" + json.dumps(request)

            # Run a fresh MCP server instance
            result = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm", "-i",
                "--add-host=host.docker.internal:host-gateway",
                "-e", f"SEARXNG_BASE_URL=http://host.docker.internal:8090",
                "-e", "LOG_LEVEL=ERROR",
                "searxng-mcp-server:latest",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )

            stdout, _ = await asyncio.wait_for(
                result.communicate(input=full_input.encode()),
                timeout=self.timeout
            )

            # Parse the responses
            responses = stdout.decode().strip().split('\n')
            logger.debug(f"Got {len(responses)} response lines from MCP server")

            # Find the search response (looking for id=2)
            search_response = None
            init_response = None

            for response_line in responses:
                if not response_line.strip():
                    continue
                try:
                    response_data = json.loads(response_line)
                    resp_id = response_data.get("id")
                    logger.debug(f"Parsed response with id={resp_id}")

                    if resp_id == 0:
                        init_response = response_data
                    elif resp_id == 2:  # Our search request ID
                        search_response = response_data
                        break
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse line: {response_line[:100]}")
                    continue

            # If we only got init response, MCP server likely crashed after search
            if init_response and not search_response:
                logger.warning("MCP server returned only init response, likely crashed during search")
                # Try direct SearXNG fallback
                logger.info("Falling back to direct SearXNG HTTP API")
                return await self._search_direct(query, category, limit, language, time_range)

            if not search_response:
                logger.error("No valid search response received", responses=responses[:3])
                # Try direct SearXNG fallback
                logger.info("Falling back to direct SearXNG HTTP API")
                return await self._search_direct(query, category, limit, language, time_range)

            # Extract results
            if "result" in search_response:
                result_data = search_response["result"]
                # MCP returns list of TextContent objects
                if isinstance(result_data, list) and len(result_data) > 0:
                    # Get the text content from the first item
                    text_content = result_data[0].get("text", "") if isinstance(result_data[0], dict) else ""
                    # Parse the JSON response
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse MCP response", response=text_content[:200])
                        return {"results": []}
                elif isinstance(result_data, dict) and "data" in result_data:
                    return result_data["data"]
                return result_data
            elif "error" in search_response:
                logger.error("MCP search error", error=search_response["error"])
                return {"results": [], "error": search_response["error"]}

            return {"results": []}

        except asyncio.TimeoutError:
            logger.error("MCP search timeout", query=query)
            return {"results": [], "error": "Search timeout"}
        except Exception as e:
            logger.error("MCP search failed", error=str(e), query=query)
            return {"results": [], "error": str(e)}

    async def batch_search(
        self,
        queries: List[str],
        category: str = "web",
        limit_per_query: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute multiple searches

        Args:
            queries: List of search queries
            category: Search category
            limit_per_query: Results per query

        Returns:
            Dictionary mapping queries to results
        """
        results = {}

        for query in queries:
            logger.info("Executing search", query=query)
            search_results = await self.search(
                query=query,
                category=category,
                limit=limit_per_query
            )
            results[query] = search_results.get("results", [])

            # Small delay between searches to avoid overwhelming the server
            await asyncio.sleep(1)

        return results

    async def health_check(self) -> bool:
        """Check if MCP server is accessible

        Returns:
            True if MCP server responds to initialization
        """
        try:
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "research-agent",
                        "version": "1.0.0"
                    }
                },
                "id": 0
            }

            # Send initialization notification after init request
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }

            # Send proper MCP initialization sequence
            health_input = json.dumps(init_request) + "\n" + json.dumps(initialized_notification)

            result = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm", "-i",
                "--add-host=host.docker.internal:host-gateway",
                "-e", f"SEARXNG_BASE_URL=http://host.docker.internal:8090",
                "-e", "LOG_LEVEL=ERROR",
                "searxng-mcp-server:latest",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )

            stdout, _ = await asyncio.wait_for(
                result.communicate(input=health_input.encode()),
                timeout=5
            )

            # Check if we got a valid response
            response = stdout.decode().strip()
            if response:
                data = json.loads(response.split('\n')[0])
                return "result" in data or "error" not in data

            return False

        except Exception as e:
            logger.warning("MCP health check failed", error=str(e))
            return False

    def extract_urls_from_results(
        self,
        search_results: Dict[str, Any]
    ) -> List[str]:
        """Extract URLs from search results

        Args:
            search_results: Search results from MCP

        Returns:
            List of URLs
        """
        urls = []

        if isinstance(search_results, dict):
            results = search_results.get("results", [])
        else:
            results = search_results if isinstance(search_results, list) else []

        for result in results:
            if isinstance(result, dict) and "url" in result:
                urls.append(result["url"])

        return urls

    def format_search_results(
        self,
        search_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format search results for processing

        Args:
            search_results: Raw search results

        Returns:
            Formatted results list
        """
        formatted = []

        if isinstance(search_results, dict):
            results = search_results.get("results", [])
        else:
            results = search_results if isinstance(search_results, list) else []

        for result in results:
            if isinstance(result, dict):
                formatted_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", result.get("content", "")),
                    "source": result.get("source", result.get("engine", "unknown"))
                }

                # Add optional fields if present
                if "relevance_score" in result or "score" in result:
                    formatted_result["score"] = result.get("relevance_score", result.get("score", 0))

                formatted.append(formatted_result)

        return formatted

    async def _search_direct(
        self,
        query: str,
        category: str = "web",
        limit: int = 10,
        language: Optional[str] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Direct search via SearXNG HTTP API (fallback)

        Args:
            query: Search query
            category: Search category
            limit: Maximum number of results
            language: Language code
            time_range: Time filter

        Returns:
            Search results
        """
        try:
            params = {
                "q": query,
                "format": "json",
                "category_general": 1 if category == "web" else 0,
                "safesearch": 0,
                "limit": limit
            }

            if language:
                params["language"] = language
            if time_range:
                params["time_range"] = time_range

            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                response = await client.get(
                    f"{self.searxng_url}/search",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

            # Format the results
            formatted_results = {
                "query": query,
                "result_count": len(data.get("results", [])),
                "response_time": data.get("response_time", 0),
                "results": []
            }

            for result in data.get("results", [])[:limit]:
                formatted_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", ""),
                    "source": result.get("engine", "unknown")
                }
                if "score" in result:
                    formatted_result["relevance_score"] = result["score"]
                formatted_results["results"].append(formatted_result)

            logger.info("Direct SearXNG search successful", results_count=len(formatted_results["results"]))
            return formatted_results

        except Exception as e:
            logger.error("Direct SearXNG search failed", error=str(e))
            return {"results": [], "error": str(e)}