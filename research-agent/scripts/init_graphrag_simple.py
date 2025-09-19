#!/usr/bin/env python
"""Simple GraphRAG database initialization"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from structlog import get_logger

logger = get_logger()


async def init_graphrag_database():
    """Initialize GraphRAG database schema"""

    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://research_user:research_pass_2024@localhost:5432/research_agent"
    )

    # Convert to async URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    # Create engine
    engine = create_async_engine(database_url, echo=True)

    try:
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")

            # Create graph nodes table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    research_task_id UUID REFERENCES research_tasks(id) ON DELETE CASCADE,
                    node_type VARCHAR(50) NOT NULL,
                    node_value TEXT NOT NULL,
                    properties JSONB DEFAULT '{}',
                    embedding vector(384),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            logger.info("Created graph_nodes table")

            # Create graph edges table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_node_id UUID REFERENCES graph_nodes(id) ON DELETE CASCADE,
                    target_node_id UUID REFERENCES graph_nodes(id) ON DELETE CASCADE,
                    edge_type VARCHAR(50) NOT NULL,
                    weight FLOAT DEFAULT 1.0,
                    properties JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(source_node_id, target_node_id, edge_type)
                )
            """))
            logger.info("Created graph_edges table")

            # Create chat sessions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    context JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            logger.info("Created chat_sessions table")

            # Create chat messages table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    retrieved_context JSONB DEFAULT '{}',
                    sources JSONB DEFAULT '[]',
                    message_metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            logger.info("Created chat_messages table")

            # Add embedding columns to existing tables
            await conn.execute(text("""
                ALTER TABLE research_results
                ADD COLUMN IF NOT EXISTS synthesis_embedding vector(384),
                ADD COLUMN IF NOT EXISTS query_embedding vector(384)
            """))
            logger.info("Added embedding columns to research_results")

            await conn.execute(text("""
                ALTER TABLE research_artifacts
                ADD COLUMN IF NOT EXISTS content_embedding vector(384)
            """))
            logger.info("Added embedding column to research_artifacts")

            # Create indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_graph_nodes_embedding ON graph_nodes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_graph_nodes_task ON graph_nodes(research_task_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_node_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_node_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(edge_type)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_activity ON chat_sessions(last_activity DESC)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_research_results_synthesis_embedding ON research_results USING ivfflat (synthesis_embedding vector_cosine_ops) WITH (lists = 100)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_research_artifacts_content_embedding ON research_artifacts USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100)"))
            logger.info("Created all indexes")

            logger.info("GraphRAG database schema initialized successfully")
            return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """Main initialization function"""
    print("Initializing GraphRAG Chat System...")
    print("-" * 50)

    if await init_graphrag_database():
        print("✓ GraphRAG database initialized successfully!")
        print("\nYou can now:")
        print("1. Access the chat interface at: http://localhost:3002/chat")
        print("2. Start chatting with your research database")
        return 0
    else:
        print("✗ Database initialization failed")
        print("Please check the logs above for details")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)