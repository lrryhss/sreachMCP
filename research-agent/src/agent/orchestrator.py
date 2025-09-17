"""Research orchestrator - coordinates the entire research workflow"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from structlog import get_logger

from ..clients.ollama_client import OllamaClient
from ..clients.mcp_client import MCPSearchClient
from ..clients.content_fetcher import ContentFetcher
from ..config import settings

logger = get_logger()


class ResearchStatus(Enum):
    """Research task status"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    SEARCHING = "searching"
    FETCHING = "fetching"
    SYNTHESIZING = "synthesizing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchDepth(Enum):
    """Research depth levels"""
    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class ResearchOrchestrator:
    """Orchestrates the research workflow"""

    def __init__(self):
        """Initialize the orchestrator"""
        self.ollama_client = OllamaClient(
            base_url=settings.ollama.base_url,
            model=settings.ollama.model,
            timeout=settings.ollama.timeout
        )
        self.search_client = MCPSearchClient(
            timeout=settings.mcp.timeout,
            searxng_url="http://host.docker.internal:8090"
        )
        self.content_fetcher = ContentFetcher(
            max_concurrent=settings.content_fetching.max_concurrent,
            timeout=settings.content_fetching.timeout,
            max_content_size=settings.content_fetching.max_content_size,
            user_agent=settings.content_fetching.user_agent
        )

        # Task tracking
        self.tasks: Dict[str, Dict[str, Any]] = {}

    async def execute_research(
        self,
        query: str,
        depth: str = "standard",
        max_sources: int = 20,
        options: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a complete research task

        Args:
            query: Research query
            depth: Research depth (quick, standard, comprehensive)
            max_sources: Maximum number of sources to use
            options: Additional options

        Returns:
            Research results
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = f"res_{uuid.uuid4().hex[:12]}"

        # Initialize task tracking if not already done
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "id": task_id,
                "query": query,
                "status": ResearchStatus.PENDING,
                "progress": 0,
                "created_at": datetime.utcnow().isoformat(),
                "steps_completed": [],
                "current_step": "initializing"
            }

        try:
            logger.info("Starting research", task_id=task_id, query=query, depth=depth)

            # Step 1: Analyze query
            await self.update_task_status(task_id, ResearchStatus.ANALYZING, 10, "query_analysis")
            async with self.ollama_client as ollama:
                query_analysis = await ollama.analyze_query(query)

            logger.info("Query analyzed", task_id=task_id, strategies=len(query_analysis.get("search_strategies", [])))

            # Step 2: Execute searches
            await self.update_task_status(task_id, ResearchStatus.SEARCHING, 25, "search_execution")
            search_strategies = query_analysis.get("search_strategies", [query])[:3]
            all_search_results = await self.search_client.batch_search(
                queries=search_strategies,
                limit_per_query=10
            )

            # Collect all URLs
            all_urls = []
            for query_results in all_search_results.values():
                urls = self.search_client.extract_urls_from_results({"results": query_results})
                all_urls.extend(urls)

            # Deduplicate URLs
            unique_urls = list(dict.fromkeys(all_urls))[:max_sources]
            logger.info("URLs collected", task_id=task_id, total_urls=len(all_urls), unique_urls=len(unique_urls))

            if not unique_urls:
                raise ValueError("No URLs found from search results")

            # Step 3: Fetch content
            await self.update_task_status(task_id, ResearchStatus.FETCHING, 50, "content_fetching")
            async with self.content_fetcher as fetcher:
                contents = await fetcher.batch_fetch(unique_urls)

                # Filter and prioritize content
                valid_contents = [c for c in contents if c.get("text")]
                prioritized_contents = fetcher.prioritize_content(valid_contents, max_sources)

            logger.info(
                "Content fetched",
                task_id=task_id,
                fetched=len(contents),
                valid=len(valid_contents),
                used=len(prioritized_contents)
            )

            # If no content could be fetched, use search snippets as fallback
            if not prioritized_contents:
                logger.warning("No content fetched, using search snippets as fallback")
                prioritized_contents = self._create_content_from_search_results(
                    all_search_results, unique_urls, max_sources
                )

            # Step 4: Summarize individual sources
            await self.update_task_status(task_id, ResearchStatus.SYNTHESIZING, 70, "content_synthesis")
            summaries = []
            async with self.ollama_client as ollama:
                for i, content in enumerate(prioritized_contents):
                    # Update progress
                    progress = 70 + (15 * i / len(prioritized_contents))
                    self.tasks[task_id]["progress"] = progress

                    # Summarize content
                    summary = await ollama.summarize_content(
                        content=content["text"][:8000],  # Limit content length
                        max_length=300,
                        focus=query
                    )

                    summaries.append({
                        "url": content["url"],
                        "title": content.get("title", ""),
                        "summary": summary,
                        "word_count": content.get("word_count", 0),
                        "extraction_method": content.get("method", "")
                    })

            # Step 5: Synthesize research
            await self.update_task_status(task_id, ResearchStatus.SYNTHESIZING, 85, "research_synthesis")
            async with self.ollama_client as ollama:
                synthesis = await ollama.synthesize_research(summaries, query)

            # Step 6: Complete
            await self.update_task_status(task_id, ResearchStatus.COMPLETED, 100, "completed")

            # Prepare final results
            results = {
                "task_id": task_id,
                "query": query,
                "status": ResearchStatus.COMPLETED.value,
                "query_analysis": query_analysis,
                "sources_used": len(summaries),
                "synthesis": synthesis,
                "sources": summaries,
                "metadata": {
                    "depth": depth,
                    "max_sources": max_sources,
                    "search_strategies": search_strategies,
                    "total_urls_found": len(all_urls),
                    "unique_urls": len(unique_urls),
                    "content_fetched": len(contents),
                    "valid_content": len(valid_contents)
                },
                "completed_at": datetime.utcnow().isoformat()
            }

            self.tasks[task_id]["results"] = results
            return results

        except Exception as e:
            logger.error("Research failed", task_id=task_id, error=str(e))
            await self.update_task_status(task_id, ResearchStatus.FAILED, self.tasks[task_id]["progress"], "error")
            self.tasks[task_id]["error"] = str(e)
            raise

    def _create_content_from_search_results(
        self,
        search_results: Dict[str, List[Dict[str, Any]]],
        urls: List[str],
        max_sources: int
    ) -> List[Dict[str, Any]]:
        """Create content from search result snippets when fetching fails

        Args:
            search_results: Search results by query
            urls: List of URLs that were attempted
            max_sources: Maximum number of sources to use

        Returns:
            List of content dictionaries with snippets
        """
        contents = []
        url_to_result = {}

        # Map URLs to their search result data
        for results in search_results.values():
            for result in results:
                if isinstance(result, dict) and "url" in result:
                    url_to_result[result["url"]] = result

        # Create content from search results
        for url in urls[:max_sources]:
            if url in url_to_result:
                result = url_to_result[url]
                content = {
                    "url": url,
                    "title": result.get("title", "Untitled"),
                    "text": result.get("snippet", result.get("content", "")),
                    "word_count": len(result.get("snippet", "").split()),
                    "method": "search_snippet"
                }
                contents.append(content)

        return contents

    async def update_task_status(
        self,
        task_id: str,
        status: ResearchStatus,
        progress: int,
        current_step: str
    ):
        """Update task status

        Args:
            task_id: Task identifier
            status: New status
            progress: Progress percentage
            current_step: Current step name
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task["status"] = status
            task["progress"] = progress
            task["current_step"] = current_step

            if current_step not in task["steps_completed"] and current_step != "error":
                task["steps_completed"].append(current_step)

            task["updated_at"] = datetime.utcnow().isoformat()

            logger.info(
                "Task status updated",
                task_id=task_id,
                status=status.value,
                progress=progress,
                step=current_step
            )

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status

        Args:
            task_id: Task identifier

        Returns:
            Task status or None if not found
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "task_id": task_id,
                "status": task["status"].value if isinstance(task["status"], ResearchStatus) else task["status"],
                "progress": {
                    "percentage": task["progress"],
                    "current_step": task["current_step"],
                    "steps_completed": task["steps_completed"]
                },
                "query": task["query"],
                "created_at": task["created_at"],
                "updated_at": task.get("updated_at"),
                "error": task.get("error")
            }
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a research task

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if not found
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task["status"] not in [ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.CANCELLED]:
                task["status"] = ResearchStatus.CANCELLED
                task["cancelled_at"] = datetime.utcnow().isoformat()
                logger.info("Task cancelled", task_id=task_id)
                return True
        return False

    async def get_task_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task results

        Args:
            task_id: Task identifier

        Returns:
            Task results or None if not found/incomplete
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task["status"] == ResearchStatus.COMPLETED:
                return task.get("results")
        return None

    def get_research_depth_config(self, depth: str) -> Dict[str, Any]:
        """Get configuration for research depth

        Args:
            depth: Research depth level

        Returns:
            Configuration parameters
        """
        configs = {
            ResearchDepth.QUICK: {
                "max_searches": 1,
                "max_sources": 5,
                "summarization_length": 200,
                "synthesis_detail": "brief"
            },
            ResearchDepth.STANDARD: {
                "max_searches": 3,
                "max_sources": 15,
                "summarization_length": 300,
                "synthesis_detail": "standard"
            },
            ResearchDepth.COMPREHENSIVE: {
                "max_searches": 5,
                "max_sources": 30,
                "summarization_length": 500,
                "synthesis_detail": "detailed"
            }
        }

        try:
            depth_enum = ResearchDepth(depth)
            return configs[depth_enum]
        except ValueError:
            return configs[ResearchDepth.STANDARD]