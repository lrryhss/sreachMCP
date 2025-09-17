"""SearXNG API client for MCP server."""

import asyncio
import json
from typing import Dict, List, Optional, Any
import httpx
from structlog import get_logger

logger = get_logger()


class SearXNGClient:
    """Client for interacting with SearXNG search API."""

    def __init__(
        self,
        base_url: str,
        auth: Optional[tuple] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """Initialize the SearXNG client.

        Args:
            base_url: Base URL of the SearXNG instance
            auth: Optional (username, password) tuple for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=self.timeout,
            auth=self.auth if self.auth else None
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def health_check(self) -> bool:
        """Check if SearXNG instance is available.

        Returns:
            True if SearXNG is accessible, False otherwise
        """
        try:
            if not self.session:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{self.base_url}/")
                    return response.status_code == 200
            else:
                response = await self.session.get(f"{self.base_url}/")
                return response.status_code == 200
        except Exception as e:
            logger.warning("SearXNG health check failed", error=str(e))
            return False

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        engines: Optional[List[str]] = None,
        language: Optional[str] = None,
        time_range: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Perform a search query on SearXNG.

        Args:
            query: Search query string
            category: Search category (web, images, news, videos, files)
            engines: List of specific search engines to use
            language: Language code for results
            time_range: Time filter (day, month, year, all)
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            Dictionary containing search results
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        params = {
            "q": query,
            "format": "json",
        }

        if category:
            params["categories"] = category
        if engines:
            params["engines"] = ",".join(engines)
        if language:
            params["language"] = language
        if time_range:
            params["time_range"] = time_range

        # Add any additional parameters
        params.update(kwargs)

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Sending search request",
                    query=query,
                    params=params,
                    attempt=attempt + 1
                )

                response = await self.session.get(
                    f"{self.base_url}/search",
                    params=params
                )
                response.raise_for_status()

                data = response.json()

                # Format and limit results
                results = self.format_results(data, limit)

                logger.info(
                    "Search completed",
                    query=query,
                    result_count=len(results.get("results", []))
                )

                return results

            except httpx.HTTPStatusError as e:
                logger.error(
                    "HTTP error during search",
                    status=e.response.status_code,
                    error=str(e)
                )
                if attempt == self.max_retries - 1:
                    raise

            except Exception as e:
                logger.error(
                    "Unexpected error during search",
                    error=str(e),
                    attempt=attempt + 1
                )
                if attempt == self.max_retries - 1:
                    raise

            # Exponential backoff
            await asyncio.sleep(2 ** attempt)

        return {"results": [], "error": "Max retries exceeded"}

    def format_results(self, raw_data: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """Format raw SearXNG response data.

        Args:
            raw_data: Raw response from SearXNG
            limit: Maximum number of results to return

        Returns:
            Formatted search results
        """
        results = raw_data.get("results", [])[:limit]

        formatted_results = []
        for result in results:
            formatted_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "engine": result.get("engine", "unknown"),
            }

            # Add optional fields if present
            if "score" in result:
                formatted_result["score"] = result["score"]
            if "publishedDate" in result:
                formatted_result["published_date"] = result["publishedDate"]
            if "img_src" in result:
                formatted_result["image_url"] = result["img_src"]

            formatted_results.append(formatted_result)

        return {
            "results": formatted_results,
            "query": raw_data.get("query", ""),
            "number_of_results": len(formatted_results),
            "response_time": raw_data.get("timing", {}).get("total", 0)
        }