"""Content fetching and extraction client"""

import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
import trafilatura
from structlog import get_logger

logger = get_logger()


class ContentFetcher:
    """Fetches and extracts content from web pages"""

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: int = 10,
        max_content_size: int = 1048576,
        user_agent: str = "Mozilla/5.0 (Research-Agent/1.0)"
    ):
        """Initialize content fetcher

        Args:
            max_concurrent: Maximum concurrent fetches
            timeout: Request timeout in seconds
            max_content_size: Maximum content size in bytes
            user_agent: User agent string
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_content_size = max_content_size
        self.user_agent = user_agent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            headers={"User-Agent": self.user_agent}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()

    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from a URL

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """
        async with self.semaphore:
            try:
                if not self.session:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout),
                        headers={"User-Agent": self.user_agent}
                    ) as client:
                        response = await client.get(url)
                else:
                    response = await self.session.get(url)

                response.raise_for_status()

                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "text/plain" not in content_type:
                    logger.warning("Unsupported content type", url=url, content_type=content_type)
                    return None

                # Check content size
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_content_size:
                    logger.warning("Content too large", url=url, size=content_length)
                    return None

                return response.text

            except httpx.HTTPStatusError as e:
                logger.warning("HTTP error fetching URL", url=url, status=e.response.status_code)
                return None
            except Exception as e:
                logger.warning("Error fetching URL", url=url, error=str(e))
                return None

    def _extract_media(self, soup, url: str) -> list:
        """Extract media from BeautifulSoup object

        Args:
            soup: BeautifulSoup object
            url: Base URL for resolving relative URLs

        Returns:
            List of media items
        """
        from urllib.parse import urljoin
        media = []

        # Extract images
        for img in soup.find_all("img", src=True)[:5]:  # Limit to 5 images
            img_url = img.get("src")
            if img_url:
                # Make absolute URL if relative
                if not img_url.startswith(("http://", "https://")):
                    img_url = urljoin(url, img_url)

                media.append({
                    "url": img_url,
                    "type": "image",
                    "title": img.get("alt", ""),
                    "description": img.get("title", "")
                })

        # Extract videos
        for video in soup.find_all("video", src=True)[:3]:  # Limit to 3 videos
            video_url = video.get("src")
            if video_url:
                if not video_url.startswith(("http://", "https://")):
                    video_url = urljoin(url, video_url)

                media.append({
                    "url": video_url,
                    "type": "video",
                    "title": video.get("title", ""),
                    "thumbnail": video.get("poster", "")
                })

        # Check for YouTube embeds
        for iframe in soup.find_all("iframe", src=True)[:3]:
            iframe_src = iframe.get("src", "")
            if "youtube.com" in iframe_src or "youtu.be" in iframe_src:
                media.append({
                    "url": iframe_src.replace("/embed/", "/watch?v="),
                    "type": "youtube",
                    "title": iframe.get("title", "YouTube Video")
                })

        return media

    async def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract clean content from HTML

        Args:
            html: HTML content
            url: Source URL for context

        Returns:
            Extracted content with metadata
        """
        try:
            # Try trafilatura first (best for articles)
            extracted = trafilatura.extract(
                html,
                include_links=False,
                include_images=False,
                include_tables=True,
                deduplicate=True,
                output_format="dict"
            )

            if extracted and isinstance(extracted, dict) and extracted.get("text"):
                # Also try to extract media from the HTML
                soup = BeautifulSoup(html, "html.parser")
                media = self._extract_media(soup, url)

                return {
                    "url": url,
                    "title": extracted.get("title", ""),
                    "text": extracted["text"],
                    "author": extracted.get("author", ""),
                    "date": extracted.get("date", ""),
                    "method": "trafilatura",
                    "word_count": len(extracted["text"].split()),
                    "media": media
                }

            # Fallback to BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)

            # Extract media
            media = self._extract_media(soup, url)

            # Extract main content
            # Try to find main content areas
            main_content = soup.find("main") or soup.find("article") or soup.find("div", {"id": "content"})

            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                # Get all paragraph text
                paragraphs = soup.find_all("p")
                text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

            if not text:
                # Last resort - get all text
                text = soup.get_text(separator="\n", strip=True)

            # Clean up text
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n\n".join(lines)

            return {
                "url": url,
                "title": title,
                "text": text,
                "author": "",
                "date": "",
                "method": "beautifulsoup",
                "word_count": len(text.split()),
                "media": media
            }

        except Exception as e:
            logger.error("Content extraction failed", url=url, error=str(e))
            return {
                "url": url,
                "title": "",
                "text": "",
                "error": str(e),
                "method": "failed"
            }

    async def fetch_and_extract(self, url: str) -> Dict[str, Any]:
        """Fetch URL and extract content

        Args:
            url: URL to process

        Returns:
            Extracted content with metadata
        """
        logger.info("Fetching content", url=url)

        html = await self.fetch_url(url)
        if not html:
            return {
                "url": url,
                "title": "",
                "text": "",
                "error": "Failed to fetch content",
                "method": "failed"
            }

        content = await self.extract_content(html, url)
        logger.info(
            "Content extracted",
            url=url,
            method=content.get("method"),
            word_count=content.get("word_count", 0)
        )

        return content

    async def batch_fetch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch and extract content from multiple URLs

        Args:
            urls: List of URLs to process

        Returns:
            List of extracted content
        """
        logger.info("Starting batch fetch", url_count=len(urls))

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        # Create tasks for all URLs
        tasks = [self.fetch_and_extract(url) for url in unique_urls]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for url, result in zip(unique_urls, results):
            if isinstance(result, Exception):
                logger.warning("Fetch failed", url=url, error=str(result))
                processed_results.append({
                    "url": url,
                    "title": "",
                    "text": "",
                    "error": str(result),
                    "method": "failed"
                })
            else:
                processed_results.append(result)

        # Log summary
        successful = sum(1 for r in processed_results if r.get("text"))
        logger.info(
            "Batch fetch complete",
            total=len(unique_urls),
            successful=successful,
            failed=len(unique_urls) - successful
        )

        return processed_results

    def get_domain(self, url: str) -> str:
        """Extract domain from URL

        Args:
            url: URL string

        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"

    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for deduplication

        Args:
            content: Text content

        Returns:
            SHA256 hash
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def deduplicate_content(
        self,
        contents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate content based on text similarity

        Args:
            contents: List of content dictionaries

        Returns:
            Deduplicated content list
        """
        seen_hashes = set()
        unique_contents = []

        for content in contents:
            text = content.get("text", "")
            if text:
                # Simple hash-based deduplication
                content_hash = self.calculate_content_hash(text[:1000])  # Hash first 1000 chars
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    unique_contents.append(content)
            else:
                # Keep content without text (errors)
                unique_contents.append(content)

        logger.info(
            "Content deduplication",
            original=len(contents),
            unique=len(unique_contents),
            duplicates=len(contents) - len(unique_contents)
        )

        return unique_contents

    def prioritize_content(
        self,
        contents: List[Dict[str, Any]],
        max_items: int = 20
    ) -> List[Dict[str, Any]]:
        """Prioritize content based on quality signals

        Args:
            contents: List of content dictionaries
            max_items: Maximum items to return

        Returns:
            Prioritized content list
        """
        # Score each content item
        scored_contents = []
        for content in contents:
            score = 0

            # Has text content
            if content.get("text"):
                score += 10

            # Word count (prefer substantial content)
            word_count = content.get("word_count", 0)
            if word_count > 500:
                score += 5
            if word_count > 1000:
                score += 5

            # Has title
            if content.get("title"):
                score += 2

            # Successful extraction method
            if content.get("method") == "trafilatura":
                score += 3
            elif content.get("method") == "beautifulsoup":
                score += 1

            # No errors
            if not content.get("error"):
                score += 5

            scored_contents.append((score, content))

        # Sort by score (descending)
        scored_contents.sort(key=lambda x: x[0], reverse=True)

        # Return top items
        prioritized = [content for _, content in scored_contents[:max_items]]

        logger.info(
            "Content prioritization",
            total=len(contents),
            selected=len(prioritized)
        )

        return prioritized