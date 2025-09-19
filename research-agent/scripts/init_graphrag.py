#!/usr/bin/env python
"""Initialize GraphRAG database schema and dependencies"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
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
            # Read migration file
            migration_path = Path(__file__).parent.parent / "sql" / "migrations" / "002_add_graphrag_chat.sql"

            if not migration_path.exists():
                logger.error(f"Migration file not found: {migration_path}")
                return False

            with open(migration_path, 'r') as f:
                migration_sql = f.read()

            # Split into individual statements (PostgreSQL doesn't like multiple statements in one execute)
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

            for statement in statements:
                if statement:
                    logger.info(f"Executing: {statement[:50]}...")
                    await conn.execute(text(statement))

            logger.info("GraphRAG database schema initialized successfully")

            # Verify pgvector extension
            result = await conn.execute(text(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            ))
            if result.scalar():
                logger.info("pgvector extension is installed and ready")
            else:
                logger.warning("pgvector extension not found - installing...")
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector extension installed")

            return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
    finally:
        await engine.dispose()


async def verify_installation():
    """Verify all components are installed correctly"""

    checks = {
        "Database Schema": False,
        "Embedding Service": False,
        "Graph Service": False,
        "RAG Service": False
    }

    # Check database schema
    try:
        from src.database import db_manager
        await db_manager.initialize()

        async with db_manager.get_session() as session:
            # Check if tables exist
            result = await session.execute(text(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('graph_nodes', 'graph_edges', 'chat_sessions', 'chat_messages')
                """
            ))
            count = result.scalar()
            checks["Database Schema"] = count == 4
    except Exception as e:
        logger.error(f"Database check failed: {e}")

    # Check embedding service
    try:
        from src.services.embedding_service import get_embedding_service
        service = await get_embedding_service()
        test_embedding = await service.embed_text("test")
        checks["Embedding Service"] = test_embedding is not None
    except Exception as e:
        logger.error(f"Embedding service check failed: {e}")

    # Check graph service
    try:
        from src.services.graph_service import KnowledgeGraphService
        # Just check if it imports correctly
        checks["Graph Service"] = True
    except Exception as e:
        logger.error(f"Graph service check failed: {e}")

    # Check RAG service
    try:
        from src.services.rag_service import RAGService
        # Just check if it imports correctly
        checks["RAG Service"] = True
    except Exception as e:
        logger.error(f"RAG service check failed: {e}")

    # Print results
    print("\n" + "="*50)
    print("GraphRAG Installation Verification")
    print("="*50)
    for component, status in checks.items():
        status_str = "✓ OK" if status else "✗ FAILED"
        print(f"{component:.<30} {status_str}")
    print("="*50)

    return all(checks.values())


async def main():
    """Main initialization function"""

    print("Initializing GraphRAG Chat System...")
    print("-" * 50)

    # Initialize database
    print("Step 1: Initializing database schema...")
    if await init_graphrag_database():
        print("✓ Database initialized successfully")
    else:
        print("✗ Database initialization failed")
        return 1

    # Verify installation
    print("\nStep 2: Verifying installation...")
    if await verify_installation():
        print("\n✓ GraphRAG system is ready!")
        print("\nYou can now:")
        print("1. Start the backend: docker-compose up --build -d")
        print("2. Access the chat interface at: http://localhost:3001/chat")
        return 0
    else:
        print("\n✗ Some components failed verification")
        print("Please check the logs above for details")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)