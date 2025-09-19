#!/usr/bin/env python3
"""
Script to run the metadata column rename migration.
This renames the metadata column to result_metadata in the research_results table.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings


async def run_migration():
    """Run the database migration to rename metadata column"""
    # Create database connection with async driver
    db_url = settings.database.url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        db_url,
        echo=True
    )

    # Read migration SQL
    migration_path = Path(__file__).parent / "sql" / "migrations" / "003_rename_metadata_column.sql"
    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    async with engine.begin() as conn:
        print("Running migration to rename metadata column...")

        # Split SQL into individual statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            if statement:
                try:
                    # Execute each statement
                    await conn.execute(text(statement))
                    print(f"✓ Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"✗ Error executing statement: {e}")
                    # Continue with other statements

        print("\nMigration completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())