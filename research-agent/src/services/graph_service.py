"""Knowledge graph service for building and querying research graphs"""

import json
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from structlog import get_logger

from ..database.models import (
    ResearchTask, ResearchResult, ResearchArtifact,
    Base
)
from .embedding_service import get_embedding_service

logger = get_logger()


# Define new SQLAlchemy models for graph tables
from sqlalchemy import Column, String, Float, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector


class GraphNode(Base):
    """Graph node model"""
    __tablename__ = "graph_nodes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    research_task_id = Column(PGUUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"))
    node_type = Column(String(50), nullable=False)
    node_value = Column(Text, nullable=False)
    properties = Column(JSONB, default={})
    embedding = Column(Vector(384))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class GraphEdge(Base):
    """Graph edge model"""
    __tablename__ = "graph_edges"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source_node_id = Column(PGUUID(as_uuid=True), ForeignKey("graph_nodes.id", ondelete="CASCADE"))
    target_node_id = Column(PGUUID(as_uuid=True), ForeignKey("graph_nodes.id", ondelete="CASCADE"))
    edge_type = Column(String(50), nullable=False)
    weight = Column(Float, default=1.0)
    properties = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class KnowledgeGraphService:
    """Service for managing knowledge graphs from research data"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.graph = nx.DiGraph()

    async def build_graph_from_research(self, task_id: UUID) -> nx.DiGraph:
        """
        Build a knowledge graph from research results

        Args:
            task_id: Research task ID

        Returns:
            NetworkX directed graph
        """
        # Get research task and results
        result = await self.session.execute(
            select(ResearchTask).where(ResearchTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task or not task.result:
            logger.warning("No research results found", task_id=str(task_id))
            return self.graph

        # Extract entities and relationships from synthesis
        synthesis = task.result.synthesis
        sources = task.result.sources

        # Get embedding service
        embedding_service = await get_embedding_service()

        # Create nodes for main concepts
        await self._extract_entities_from_synthesis(
            task_id,
            synthesis,
            embedding_service
        )

        # Create nodes from sources
        await self._extract_entities_from_sources(
            task_id,
            sources,
            embedding_service
        )

        # Build relationships
        await self._build_relationships(task_id)

        logger.info(
            "Knowledge graph built",
            task_id=str(task_id),
            nodes=len(self.graph.nodes()),
            edges=len(self.graph.edges())
        )

        return self.graph

    async def _extract_entities_from_synthesis(
        self,
        task_id: UUID,
        synthesis: Dict[str, Any],
        embedding_service
    ):
        """Extract entities from synthesis data"""
        # Extract from executive summary
        if "executive_summary" in synthesis:
            summary = synthesis["executive_summary"]
            if isinstance(summary, dict) and "content" in summary:
                content = summary["content"]

                # Create main topic node
                topic_text = f"Research: {content[:200]}"
                topic_embedding = await embedding_service.embed_text(topic_text)

                topic_node = GraphNode(
                    research_task_id=task_id,
                    node_type="topic",
                    node_value=topic_text,
                    properties={"source": "executive_summary"},
                    embedding=topic_embedding.tolist()
                )
                self.session.add(topic_node)

        # Extract from key findings
        if "key_findings" in synthesis:
            findings = synthesis["key_findings"]
            if isinstance(findings, list):
                for idx, finding in enumerate(findings):
                    if isinstance(finding, dict) and "finding" in finding:
                        finding_text = finding["finding"]
                        finding_embedding = await embedding_service.embed_text(finding_text)

                        finding_node = GraphNode(
                            research_task_id=task_id,
                            node_type="finding",
                            node_value=finding_text,
                            properties={
                                "importance": finding.get("importance", "medium"),
                                "index": idx
                            },
                            embedding=finding_embedding.tolist()
                        )
                        self.session.add(finding_node)

    async def _extract_entities_from_sources(
        self,
        task_id: UUID,
        sources: List[Dict[str, Any]],
        embedding_service
    ):
        """Extract entities from source documents"""
        for source in sources[:10]:  # Limit to top 10 sources
            if not isinstance(source, dict):
                continue

            # Create source node
            title = source.get("title", "Unknown")
            content = source.get("relevant_content", "")[:500]

            source_text = f"{title}: {content}"
            source_embedding = await embedding_service.embed_text(source_text)

            source_node = GraphNode(
                research_task_id=task_id,
                node_type="source",
                node_value=title,
                properties={
                    "url": source.get("url", ""),
                    "relevance": source.get("relevance_score", 0),
                    "content_preview": content[:200]
                },
                embedding=source_embedding.tolist()
            )
            self.session.add(source_node)

    async def _build_relationships(self, task_id: UUID):
        """Build relationships between nodes"""
        # Get all nodes for this task
        result = await self.session.execute(
            select(GraphNode).where(GraphNode.research_task_id == task_id)
        )
        nodes = result.scalars().all()

        # Build graph in memory
        node_map = {}
        for node in nodes:
            self.graph.add_node(
                str(node.id),
                type=node.node_type,
                value=node.node_value,
                properties=node.properties
            )
            node_map[str(node.id)] = node

        # Create relationships based on similarity
        embedding_service = await get_embedding_service()

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1:]:
                if node1.embedding and node2.embedding:
                    similarity = embedding_service.compute_similarity(
                        np.array(node1.embedding),
                        np.array(node2.embedding)
                    )

                    # Create edge if similarity is high enough
                    if similarity > 0.5:
                        edge = GraphEdge(
                            source_node_id=node1.id,
                            target_node_id=node2.id,
                            edge_type="related_to",
                            weight=float(similarity),
                            properties={"similarity_score": float(similarity)}
                        )
                        self.session.add(edge)

                        self.graph.add_edge(
                            str(node1.id),
                            str(node2.id),
                            type="related_to",
                            weight=similarity
                        )

    async def query_graph(
        self,
        query: str,
        task_ids: Optional[List[UUID]] = None,
        max_hops: int = 2,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph

        Args:
            query: Query text
            task_ids: Optional list of task IDs to search within
            max_hops: Maximum graph traversal hops
            top_k: Number of top results

        Returns:
            List of relevant nodes and their context
        """
        # Get embedding for query
        embedding_service = await get_embedding_service()
        query_embedding = await embedding_service.embed_text(query)

        # Find similar nodes using vector search
        query_filter = []
        if task_ids:
            query_filter.append(GraphNode.research_task_id.in_(task_ids))

        # Build vector similarity query
        from pgvector.sqlalchemy import Vector
        similarity_query = select(
            GraphNode,
            GraphNode.embedding.cosine_distance(query_embedding.tolist()).label("distance")
        )

        if query_filter:
            similarity_query = similarity_query.where(and_(*query_filter))

        similarity_query = similarity_query.order_by("distance").limit(top_k)

        result = await self.session.execute(similarity_query)
        similar_nodes = result.all()

        # Expand context using graph traversal
        expanded_results = []
        for node, distance in similar_nodes:
            context = await self._expand_node_context(node, max_hops)
            expanded_results.append({
                "node": {
                    "id": str(node.id),
                    "type": node.node_type,
                    "value": node.node_value,
                    "properties": node.properties
                },
                "similarity": 1.0 - distance,  # Convert distance to similarity
                "context": context
            })

        return expanded_results

    async def _expand_node_context(
        self,
        node: GraphNode,
        max_hops: int
    ) -> Dict[str, Any]:
        """Expand context around a node using graph traversal"""
        context = {
            "related_nodes": [],
            "paths": []
        }

        # Get edges from this node
        edges_result = await self.session.execute(
            select(GraphEdge, GraphNode)
            .join(GraphNode, GraphEdge.target_node_id == GraphNode.id)
            .where(GraphEdge.source_node_id == node.id)
            .order_by(GraphEdge.weight.desc())
            .limit(5)
        )

        for edge, related_node in edges_result:
            context["related_nodes"].append({
                "id": str(related_node.id),
                "type": related_node.node_type,
                "value": related_node.node_value[:200],
                "relation": edge.edge_type,
                "weight": edge.weight
            })

        return context

    async def get_subgraph(
        self,
        node_ids: List[UUID],
        depth: int = 1
    ) -> nx.DiGraph:
        """
        Get a subgraph around specified nodes

        Args:
            node_ids: List of node IDs
            depth: Depth of traversal

        Returns:
            NetworkX subgraph
        """
        subgraph = nx.DiGraph()

        # Convert UUIDs to strings
        node_ids_str = [str(nid) for nid in node_ids]

        # Load nodes
        nodes_result = await self.session.execute(
            select(GraphNode).where(GraphNode.id.in_(node_ids))
        )
        nodes = nodes_result.scalars().all()

        for node in nodes:
            subgraph.add_node(
                str(node.id),
                type=node.node_type,
                value=node.node_value,
                properties=node.properties
            )

        # Load edges
        edges_result = await self.session.execute(
            select(GraphEdge).where(
                or_(
                    GraphEdge.source_node_id.in_(node_ids),
                    GraphEdge.target_node_id.in_(node_ids)
                )
            )
        )
        edges = edges_result.scalars().all()

        for edge in edges:
            if str(edge.source_node_id) in node_ids_str and str(edge.target_node_id) in node_ids_str:
                subgraph.add_edge(
                    str(edge.source_node_id),
                    str(edge.target_node_id),
                    type=edge.edge_type,
                    weight=edge.weight
                )

        return subgraph


import numpy as np  # Import at the end to avoid circular imports