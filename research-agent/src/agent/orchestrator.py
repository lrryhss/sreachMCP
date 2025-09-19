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
from ..database.connection import db_manager
from ..services.database_service import DatabaseService
from ..database.models import TaskStatus as DBTaskStatus

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
        # Step timeouts based on depth
        timeouts = {
            "quick": {"analysis": 30, "search": 60, "fetch": 120, "synthesis": 300},
            "standard": {"analysis": 60, "search": 120, "fetch": 300, "synthesis": 600},
            "comprehensive": {"analysis": 120, "search": 180, "fetch": 600, "synthesis": 900}
        }
        step_timeouts = timeouts.get(depth, timeouts["standard"])

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
                "current_step": "initializing",
                "errors": [],
                "warnings": []
            }

        query_analysis = None
        all_search_results = {}
        unique_urls = []
        prioritized_contents = []

        try:
            logger.info("Starting research", task_id=task_id, query=query, depth=depth)

            # Step 1: Analyze query with timeout and retry
            await self.update_task_status(task_id, ResearchStatus.ANALYZING, 10, "query_analysis")
            try:
                async with self.ollama_client as ollama:
                    query_analysis = await asyncio.wait_for(
                        ollama.analyze_query(query),
                        timeout=step_timeouts["analysis"]
                    )
                logger.info("Query analyzed", task_id=task_id, strategies=len(query_analysis.get("search_strategies", [])))
                self.tasks[task_id]["steps_completed"].append("query_analysis")
            except asyncio.TimeoutError:
                error_msg = f"Query analysis timed out after {step_timeouts['analysis']}s"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                # Fallback to simple query
                query_analysis = {"search_strategies": [query], "query_type": "simple"}
            except Exception as e:
                error_msg = f"Query analysis failed: {str(e)}"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                # Fallback to simple query
                query_analysis = {"search_strategies": [query], "query_type": "simple"}

            # Step 2: Execute searches with timeout and error handling
            await self.update_task_status(task_id, ResearchStatus.SEARCHING, 25, "search_execution")
            search_strategies = query_analysis.get("search_strategies", [query])[:3]

            try:
                all_search_results = await asyncio.wait_for(
                    self.search_client.batch_search(
                        queries=search_strategies,
                        limit_per_query=10
                    ),
                    timeout=step_timeouts["search"]
                )

                # Collect all URLs
                all_urls = []
                for query_results in all_search_results.values():
                    urls = self.search_client.extract_urls_from_results({"results": query_results})
                    all_urls.extend(urls)

                # Deduplicate URLs
                unique_urls = list(dict.fromkeys(all_urls))[:max_sources]
                logger.info("URLs collected", task_id=task_id, total_urls=len(all_urls), unique_urls=len(unique_urls))

                if unique_urls:
                    self.tasks[task_id]["steps_completed"].append("search")
                else:
                    raise ValueError("No URLs found from search results")

            except asyncio.TimeoutError:
                error_msg = f"Search timed out after {step_timeouts['search']}s"
                logger.error(error_msg, task_id=task_id)
                self.tasks[task_id]["errors"].append(error_msg)
                raise ValueError(f"Search operation failed: {error_msg}")
            except Exception as e:
                error_msg = f"Search failed: {str(e)}"
                logger.error(error_msg, task_id=task_id)
                self.tasks[task_id]["errors"].append(error_msg)
                raise ValueError(f"Search operation failed: {error_msg}")

            # Step 3: Fetch content with timeout and graceful degradation
            await self.update_task_status(task_id, ResearchStatus.FETCHING, 50, "content_fetching")
            contents = []
            valid_contents = []

            try:
                async with self.content_fetcher as fetcher:
                    contents = await asyncio.wait_for(
                        fetcher.batch_fetch(unique_urls),
                        timeout=step_timeouts["fetch"]
                    )

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

                if prioritized_contents:
                    self.tasks[task_id]["steps_completed"].append("content_fetch")
                else:
                    logger.warning("No valid content fetched", task_id=task_id)

            except asyncio.TimeoutError:
                error_msg = f"Content fetching timed out after {step_timeouts['fetch']}s"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                prioritized_contents = []
            except Exception as e:
                error_msg = f"Content fetching failed: {str(e)}"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                prioritized_contents = []

            # If no content could be fetched, use search snippets as fallback
            if not prioritized_contents:
                logger.warning("No content fetched, using search snippets as fallback", task_id=task_id)
                prioritized_contents = self._create_content_from_search_results(
                    all_search_results, unique_urls, max_sources
                )
                if not prioritized_contents:
                    raise ValueError("No content available from either fetching or search snippets")

            # Step 4: Summarize individual sources and collect media
            await self.update_task_status(task_id, ResearchStatus.SYNTHESIZING, 70, "content_synthesis")
            summaries = []
            all_media = []  # Collect all media items

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

                    # Collect media from this source
                    if content.get("media"):
                        for media_item in content["media"]:
                            media_item["source_index"] = i + 1  # Track which source it came from
                            all_media.append(media_item)

                    summaries.append({
                        "url": content["url"],
                        "title": content.get("title", ""),
                        "summary": summary,
                        "word_count": content.get("word_count", 0),
                        "extraction_method": content.get("method", ""),
                        "media": content.get("media", [])[:2]  # Keep first 2 media items per source
                    })

            # Step 5: Synthesize research with timeout and error handling
            await self.update_task_status(task_id, ResearchStatus.SYNTHESIZING, 85, "research_synthesis")
            synthesis = None

            try:
                async with self.ollama_client as ollama:
                    synthesis = await asyncio.wait_for(
                        ollama.synthesize_research(summaries, query),
                        timeout=step_timeouts["synthesis"]
                    )

                    # Validate and repair the synthesis
                    synthesis = self._validate_and_repair_synthesis(synthesis, summaries, query)

                    # Debug logging
                    logger.info(f"Synthesis type: {type(synthesis)}, has executive_summary: {'executive_summary' in synthesis}")
                    if "executive_summary" in synthesis:
                        logger.info(f"Executive summary type: {type(synthesis['executive_summary'])}, length: {len(str(synthesis['executive_summary']))}")

                    # Reformat executive summary if it's a plain string
                    if isinstance(synthesis.get("executive_summary"), str) and synthesis["executive_summary"]:
                        logger.info("Reformatting executive summary for better readability")
                        try:
                            # Get markdown formatted text with paragraph breaks
                            formatted_text = await asyncio.wait_for(
                                ollama.reformat_executive_summary(synthesis["executive_summary"]),
                                timeout=60  # Short timeout for reformatting
                            )

                            # Replace the executive summary with formatted version
                            synthesis["executive_summary"] = formatted_text
                            logger.info("Executive summary reformatted successfully")
                        except Exception as e:
                            logger.warning("Failed to reformat executive summary", error=str(e))
                            # Keep original if reformatting fails

                self.tasks[task_id]["steps_completed"].append("synthesis")

            except asyncio.TimeoutError:
                error_msg = f"Synthesis timed out after {step_timeouts['synthesis']}s"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                # Create minimal synthesis as fallback
                synthesis = self._create_fallback_synthesis(summaries, query)
            except Exception as e:
                error_msg = f"Synthesis failed: {str(e)}"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                # Create minimal synthesis as fallback
                synthesis = self._create_fallback_synthesis(summaries, query)

            # Generate detailed analysis using multi-step approach with timeout
            logger.info("Starting multi-step detailed analysis generation")

            # Create progress callback for detailed analysis
            async def analysis_progress(progress: int, step: str):
                await self.update_task_status(task_id, ResearchStatus.SYNTHESIZING, progress, step)

            try:
                # Call multi-step analysis with timeout
                detailed_analysis = await asyncio.wait_for(
                    self.ollama_client.generate_detailed_analysis_multistep(
                        summaries=summaries,
                        query=query,
                        progress_callback=analysis_progress
                    ),
                    timeout=step_timeouts["synthesis"] // 2  # Half the synthesis timeout for detailed analysis
                )
                synthesis["detailed_analysis"] = detailed_analysis
                logger.info(f"Generated detailed analysis with {len(detailed_analysis.get('sections', []))} sections")
                self.tasks[task_id]["steps_completed"].append("detailed_analysis")
            except asyncio.TimeoutError:
                error_msg = f"Detailed analysis timed out after {step_timeouts['synthesis'] // 2}s"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                # Synthesis continues without detailed analysis
            except Exception as e:
                error_msg = f"Failed to generate detailed analysis: {str(e)}"
                logger.warning(error_msg, task_id=task_id)
                self.tasks[task_id]["warnings"].append(error_msg)
                # Synthesis continues without detailed analysis

            # Select featured media (top 5 unique items, prioritizing images)
            featured_media = []
            seen_urls = set()

            # First, add images
            for media in all_media:
                if media.get("type") == "image" and media.get("url") not in seen_urls:
                    featured_media.append(media)
                    seen_urls.add(media["url"])
                    if len(featured_media) >= 5:
                        break

            # Then add videos if we have space
            if len(featured_media) < 5:
                for media in all_media:
                    if media.get("type") in ["video", "youtube"] and media.get("url") not in seen_urls:
                        featured_media.append(media)
                        seen_urls.add(media["url"])
                        if len(featured_media) >= 5:
                            break

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
                "featured_media": featured_media,  # Add featured media
                "metadata": {
                    "depth": depth,
                    "max_sources": max_sources,
                    "search_strategies": search_strategies,
                    "total_urls_found": len(all_urls),
                    "unique_urls": len(unique_urls),
                    "content_fetched": len(contents),
                    "valid_content": len(valid_contents),
                    "total_media_found": len(all_media)
                },
                "completed_at": datetime.utcnow().isoformat()
            }

            self.tasks[task_id]["results"] = results
            return results

        except Exception as e:
            # Enhanced error logging with context
            error_context = {
                "task_id": task_id,
                "error": str(e),
                "completed_steps": self.tasks[task_id].get("steps_completed", []),
                "warnings": self.tasks[task_id].get("warnings", []),
                "errors": self.tasks[task_id].get("errors", []),
                "progress": self.tasks[task_id].get("progress", 0)
            }
            logger.error("Research failed", **error_context)

            await self.update_task_status(task_id, ResearchStatus.FAILED, self.tasks[task_id]["progress"], "error")
            self.tasks[task_id]["error"] = str(e)
            self.tasks[task_id]["errors"].append(f"Fatal error: {str(e)}")
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

            # Also update in database
            asyncio.create_task(self._update_database_task_status(task_id, status, progress))

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

    def _validate_and_repair_synthesis(
        self,
        synthesis: Dict[str, Any],
        summaries: List[Dict[str, str]],
        query: str
    ) -> Dict[str, Any]:
        """Validate and repair synthesis data to ensure all required fields exist

        Args:
            synthesis: The synthesis dictionary to validate
            summaries: List of source summaries for fallback generation
            query: Original research query

        Returns:
            Repaired synthesis dictionary
        """
        # Ensure synthesis is a dictionary
        if not isinstance(synthesis, dict):
            logger.warning("Synthesis is not a dictionary, creating new one")
            synthesis = {}

        # Validate and repair executive summary
        exec_summary = synthesis.get("executive_summary", "")
        if not exec_summary or len(str(exec_summary)) < 100:
            logger.warning(f"Executive summary too short ({len(str(exec_summary))} chars), generating from summaries")
            # Generate from first 3 summaries
            summary_texts = []
            for i, summary in enumerate(summaries[:3]):
                if summary.get("summary"):
                    summary_texts.append(summary["summary"][:200])

            if summary_texts:
                synthesis["executive_summary"] = " ".join(summary_texts)
            else:
                synthesis["executive_summary"] = f"Research conducted on: {query}. Analysis of {len(summaries)} sources completed."

        # Validate and repair key findings
        key_findings = synthesis.get("key_findings", [])
        if not key_findings or len(key_findings) < 3:
            logger.warning(f"Insufficient key findings ({len(key_findings)}), generating from summaries")
            # Generate findings from summaries
            new_findings = []
            for i, summary in enumerate(summaries[:6]):
                if summary.get("summary"):
                    # Extract first sentence as a finding
                    sentences = summary["summary"].split('.')
                    if sentences and sentences[0]:
                        new_findings.append({
                            "headline": f"Finding from {summary.get('title', f'Source {i+1}')[:30]}",
                            "finding": sentences[0].strip() + ".",
                            "category": "primary" if i < 3 else "secondary",
                            "impact_score": 0.7 - (i * 0.05),
                            "confidence": 0.7 - (i * 0.05),
                            "supporting_sources": [i + 1],
                            "statistics": {},
                            "keywords": []
                        })

            # Ensure we have at least 3 findings
            while len(new_findings) < 3:
                new_findings.append({
                    "headline": f"Additional Research Finding {len(new_findings) + 1}",
                    "finding": f"Analysis of source materials revealed insights related to {query}.",
                    "category": "secondary",
                    "impact_score": 0.5,
                    "confidence": 0.5,
                    "supporting_sources": [1],
                    "statistics": {},
                    "keywords": []
                })

            synthesis["key_findings"] = new_findings[:6]  # Limit to 6 findings

        else:
            # Repair existing findings to ensure they have all required fields
            for finding in key_findings:
                if not finding.get("headline"):
                    finding["headline"] = "Research Finding"
                if not finding.get("finding"):
                    finding["finding"] = "Analysis revealed relevant insights."
                if not finding.get("category"):
                    finding["category"] = "secondary"
                if not finding.get("impact_score"):
                    finding["impact_score"] = 0.5
                if not finding.get("confidence"):
                    finding["confidence"] = 0.5
                if not finding.get("supporting_sources"):
                    finding["supporting_sources"] = [1]
                if not finding.get("statistics"):
                    finding["statistics"] = {}
                if not finding.get("keywords"):
                    finding["keywords"] = []

        # Ensure other required fields exist
        if "themes" not in synthesis:
            synthesis["themes"] = []
        if "contradictions" not in synthesis:
            synthesis["contradictions"] = []
        if "knowledge_gaps" not in synthesis:
            synthesis["knowledge_gaps"] = []
        if "recommendations" not in synthesis:
            synthesis["recommendations"] = []
        if "further_research" not in synthesis:
            synthesis["further_research"] = []
        if "pull_quote" not in synthesis:
            synthesis["pull_quote"] = synthesis.get("executive_summary", "")[:100] if synthesis.get("executive_summary") else f"Research on {query}"

        # Ensure detailed_analysis has at least basic structure
        if not synthesis.get("detailed_analysis") or not synthesis["detailed_analysis"].get("sections"):
            synthesis["detailed_analysis"] = {
                "sections": [
                    {
                        "title": "Research Overview",
                        "content": synthesis.get("executive_summary", "Research overview not available."),
                        "sources": list(range(1, min(4, len(summaries) + 1)))
                    }
                ]
            }

        logger.info("Synthesis validation and repair completed")
        return synthesis

    def _create_fallback_synthesis(self, summaries: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Create a fallback synthesis when AI synthesis fails

        Args:
            summaries: List of source summaries
            query: Original research query

        Returns:
            Basic synthesis structure
        """
        logger.info("Creating fallback synthesis", query=query, sources=len(summaries))

        # Create basic executive summary from source summaries
        if summaries:
            key_points = []
            for i, summary in enumerate(summaries[:5]):  # Use top 5 sources
                if summary.get("summary"):
                    key_points.append(f"{i+1}. {summary['summary'][:200]}...")

            executive_summary = (
                f"Research on '{query}' reveals the following key findings:\n\n" +
                "\n".join(key_points) +
                "\n\nThis analysis is based on available sources and may be incomplete due to processing limitations."
            )
        else:
            executive_summary = f"Unable to generate comprehensive analysis for '{query}' due to limited source availability."

        # Create basic fallback synthesis
        fallback_synthesis = {
            "executive_summary": executive_summary,
            "key_findings": [
                f"Analysis of {len(summaries)} sources related to '{query}'",
                "Findings may be limited due to processing constraints",
                "Further research recommended for comprehensive understanding"
            ],
            "implications": [
                "Results should be verified with additional sources",
                "Professional consultation recommended for critical decisions"
            ],
            "further_research": [
                f"Expand search scope for '{query}'",
                "Consult domain experts",
                "Review additional academic sources"
            ],
            "pull_quote": executive_summary[:150] + "..." if len(executive_summary) > 150 else executive_summary,
            "detailed_analysis": {
                "sections": [
                    {
                        "title": "Research Summary",
                        "content": executive_summary,
                        "sources": list(range(1, min(len(summaries) + 1, 6)))
                    }
                ]
            }
        }

        logger.info("Fallback synthesis created successfully")
        return fallback_synthesis

    async def _update_database_task_status(self, task_id: str, status: ResearchStatus, progress: int) -> None:
        """Update task status in database if available"""
        try:
            # Map internal status to database status
            db_status_map = {
                ResearchStatus.PENDING: DBTaskStatus.PENDING,
                ResearchStatus.ANALYZING: DBTaskStatus.ANALYZING,
                ResearchStatus.SEARCHING: DBTaskStatus.SEARCHING,
                ResearchStatus.FETCHING: DBTaskStatus.FETCHING,
                ResearchStatus.SYNTHESIZING: DBTaskStatus.SYNTHESIZING,
                ResearchStatus.GENERATING: DBTaskStatus.GENERATING,
                ResearchStatus.COMPLETED: DBTaskStatus.COMPLETED,
                ResearchStatus.FAILED: DBTaskStatus.FAILED,
                ResearchStatus.CANCELLED: DBTaskStatus.CANCELLED,
            }

            db_status = db_status_map.get(status)
            if not db_status:
                return

            async with db_manager.get_session() as session:
                db_service = DatabaseService(session)
                await db_service.tasks.update_status(
                    task_id=task_id,
                    status=db_status,
                    progress=progress
                )
                await db_service.commit()

        except Exception as e:
            # Log but don't fail if database update fails
            logger.warning("Failed to update database task status", task_id=task_id, error=str(e))