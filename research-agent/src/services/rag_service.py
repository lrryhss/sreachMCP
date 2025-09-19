"""RAG (Retrieval-Augmented Generation) service for chat functionality"""

import json
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from structlog import get_logger

from ..database.models import (
    ResearchTask, ResearchResult, ResearchArtifact, User
)
from .embedding_service import get_embedding_service
from .graph_service import KnowledgeGraphService, GraphNode
from ..clients.ollama_client import OllamaClient

logger = get_logger()


class RAGService:
    """Service for Retrieval-Augmented Generation with hybrid search"""

    def __init__(self, session: AsyncSession, ollama_client: Optional[OllamaClient] = None):
        self.session = session
        self.ollama_client = ollama_client or OllamaClient()
        self.graph_service = KnowledgeGraphService(session)

    async def retrieve_context(
        self,
        query: str,
        user_id: UUID,
        top_k: int = 5,
        use_graph: bool = True,
        use_vector: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context using hybrid search

        Args:
            query: User query
            user_id: User ID for filtering results
            top_k: Number of top results to retrieve
            use_graph: Whether to use graph-based retrieval
            use_vector: Whether to use vector-based retrieval

        Returns:
            Retrieved context with sources
        """
        context = {
            "vector_results": [],
            "graph_results": [],
            "combined_results": [],
            "sources": []
        }

        # Get user's research tasks
        user_tasks = await self._get_user_tasks(user_id)
        task_ids = [task.id for task in user_tasks]

        if not task_ids:
            logger.info("No research tasks found for user", user_id=str(user_id))
            return context

        # Parallel retrieval
        tasks = []
        if use_vector:
            tasks.append(self._vector_search(query, task_ids, top_k))
        if use_graph:
            tasks.append(self._graph_search(query, task_ids, top_k))

        results = await asyncio.gather(*tasks)

        if use_vector:
            context["vector_results"] = results[0] if tasks else []
        if use_graph:
            idx = 1 if use_vector else 0
            context["graph_results"] = results[idx] if len(results) > idx else []

        # Combine and rank results
        context["combined_results"] = await self._combine_results(
            context["vector_results"],
            context["graph_results"]
        )

        # Extract unique sources
        seen_sources = set()
        for result in context["combined_results"][:top_k]:
            source = result.get("source")
            if source and source["id"] not in seen_sources:
                seen_sources.add(source["id"])
                context["sources"].append(source)

        logger.info(
            "Context retrieved",
            query=query[:100],
            vector_results=len(context["vector_results"]),
            graph_results=len(context["graph_results"]),
            sources=len(context["sources"])
        )

        return context

    async def _get_user_tasks(self, user_id: UUID) -> List[ResearchTask]:
        """Get user's research tasks"""
        result = await self.session.execute(
            select(ResearchTask)
            .where(ResearchTask.user_id == user_id)
            .order_by(ResearchTask.created_at.desc())
            .limit(50)
        )
        return result.scalars().all()

    async def _vector_search(
        self,
        query: str,
        task_ids: List[UUID],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        embedding_service = await get_embedding_service()
        query_embedding = await embedding_service.embed_text(query)

        # Search in research results
        from pgvector.sqlalchemy import Vector

        # Query for similar synthesis embeddings
        synthesis_query = select(
            ResearchResult,
            ResearchTask,
            ResearchResult.synthesis_embedding.cosine_distance(
                query_embedding.tolist()
            ).label("distance")
        ).join(
            ResearchTask,
            ResearchResult.task_id == ResearchTask.id
        ).where(
            and_(
                ResearchTask.id.in_(task_ids),
                ResearchResult.synthesis_embedding.isnot(None)
            )
        ).order_by("distance").limit(top_k)

        result = await self.session.execute(synthesis_query)
        vector_results = []

        for res_result, task, distance in result:
            similarity = 1.0 - distance  # Convert distance to similarity

            # Extract relevant content
            synthesis = res_result.synthesis
            executive_summary = ""
            if "executive_summary" in synthesis:
                summary = synthesis["executive_summary"]
                if isinstance(summary, dict) and "content" in summary:
                    executive_summary = summary["content"]

            vector_results.append({
                "type": "synthesis",
                "content": executive_summary[:500],
                "similarity": float(similarity),
                "source": {
                    "id": str(task.id),
                    "task_id": task.task_id,
                    "query": task.query,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                },
                "metadata": {
                    "sources_used": res_result.sources_used,
                    "has_detailed_analysis": bool(res_result.detailed_analysis)
                }
            })

        return vector_results

    async def _graph_search(
        self,
        query: str,
        task_ids: List[UUID],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform graph-based search"""
        graph_results = await self.graph_service.query_graph(
            query=query,
            task_ids=task_ids,
            max_hops=2,
            top_k=top_k
        )

        formatted_results = []
        for result in graph_results:
            node = result["node"]
            formatted_results.append({
                "type": "graph",
                "content": node["value"][:500],
                "similarity": result["similarity"],
                "source": {
                    "id": node["id"],
                    "type": node["type"],
                    "properties": node["properties"]
                },
                "context": result["context"]
            })

        return formatted_results

    async def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and rank results from different sources"""
        # Simple combination strategy: merge and sort by similarity
        all_results = []

        # Add vector results with boost
        for result in vector_results:
            result["final_score"] = result["similarity"] * 1.1  # Slight boost for direct matches
            all_results.append(result)

        # Add graph results
        for result in graph_results:
            result["final_score"] = result["similarity"]
            all_results.append(result)

        # Sort by final score
        all_results.sort(key=lambda x: x["final_score"], reverse=True)

        # Remove duplicates based on content similarity
        unique_results = []
        seen_content = set()

        for result in all_results:
            content_key = result["content"][:100]  # Use first 100 chars as key
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)

        return unique_results

    async def generate_response(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate response using retrieved context

        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous conversation messages
            stream: Whether to stream the response

        Returns:
            Generated response with metadata
        """
        # Build prompt with context
        prompt = await self._build_prompt(query, context, conversation_history)

        # Generate response
        if stream:
            # Return generator for streaming
            return {
                "type": "stream",
                "generator": self._stream_response(prompt),
                "sources": context["sources"]
            }
        else:
            # Generate complete response
            response = await self.ollama_client.generate(
                prompt=prompt,
                system="You are a helpful research assistant with access to a knowledge base. "
                       "Answer questions based on the provided context and conversation history. "
                       "IMPORTANT: When creating diagrams, ALWAYS use proper markdown code blocks with triple backticks. "
                       "For Mermaid diagrams: ```mermaid\n[diagram code]\n``` "
                       "For other code: ```python\n[code]\n``` or ```javascript\n[code]\n``` etc. "
                       "Format tables using markdown pipe syntax: | Header | Header |\n|--------|--------|\n| Data | Data | "
                       "Cite sources when relevant using [Source: X] notation.",
                max_tokens=1000,
                temperature=0.7
            )

            return {
                "type": "complete",
                "content": response,
                "sources": context["sources"],
                "metadata": {
                    "context_items": len(context["combined_results"]),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

    async def _build_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Build prompt with context and history"""
        prompt_parts = []

        # Add context
        if context["combined_results"]:
            prompt_parts.append("## Relevant Context:\n")
            for idx, result in enumerate(context["combined_results"][:5], 1):
                prompt_parts.append(f"\n### Context {idx}:")
                prompt_parts.append(f"Type: {result['type']}")
                prompt_parts.append(f"Content: {result['content']}")
                if result.get("source", {}).get("query"):
                    prompt_parts.append(f"From research: {result['source']['query']}")
                prompt_parts.append("")

        # Add conversation history
        if conversation_history:
            prompt_parts.append("\n## Conversation History:")
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role.capitalize()}: {content}")
            prompt_parts.append("")

        # Add current query
        prompt_parts.append(f"\n## Current Question:\n{query}")
        prompt_parts.append("\n## Your Response:")

        return "\n".join(prompt_parts)

    async def _stream_response(self, prompt: str):
        """Stream response generation"""
        async for chunk in self.ollama_client.stream_generate(
            prompt=prompt,
            system="You are a helpful research assistant with access to a knowledge base. "
                   "Answer questions based on the provided context and conversation history. "
                   "IMPORTANT: When creating diagrams, ALWAYS use proper markdown code blocks with triple backticks. "
                   "For Mermaid diagrams: ```mermaid\n[diagram code]\n``` "
                   "For other code: ```python\n[code]\n``` or ```javascript\n[code]\n``` etc. "
                   "Format tables using markdown pipe syntax: | Header | Header |\n|--------|--------|\n| Data | Data | "
                   "Cite sources when relevant using [Source: X] notation.",
            max_tokens=1000,
            temperature=0.7
        ):
            yield chunk

    async def process_chat_message(
        self,
        message: str,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a chat message end-to-end

        Args:
            message: User message
            user_id: User ID
            session_id: Optional chat session ID
            stream: Whether to stream response

        Returns:
            Complete response with context and sources
        """
        # Retrieve context
        context = await self.retrieve_context(
            query=message,
            user_id=user_id,
            top_k=5,
            use_graph=True,
            use_vector=True
        )

        # Get conversation history if session_id provided
        conversation_history = []
        if session_id:
            # TODO: Implement conversation history retrieval
            pass

        # Generate response
        response = await self.generate_response(
            query=message,
            context=context,
            conversation_history=conversation_history,
            stream=stream
        )

        return {
            "response": response,
            "context": {
                "retrieved_items": len(context["combined_results"]),
                "sources": context["sources"]
            },
            "session_id": session_id
        }