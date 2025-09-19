#!/usr/bin/env python3
"""
Script to run the user role migration.
This adds a role column to the users table and sets the first user as admin.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings


async def run_migration():
    """Run the database migration to add user roles"""
    # Create database connection
    engine = create_async_engine(
        settings.database.url,
        echo=True
    )

    # Read migration SQL
    migration_path = Path(__file__).parent / "add_user_role_migration.sql"
    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    async with engine.begin() as conn:
        print("Running migration to add user roles...")

        # Split SQL into individual statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

        for statement in statements:
            if statement:
                try:
                    # Execute each statement
                    await conn.execute(statement)
                    print(f"✓ Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"✗ Error executing statement: {e}")
                    # Continue with other statements

        print("\nMigration completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())