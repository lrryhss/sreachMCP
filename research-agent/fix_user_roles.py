#!/usr/bin/env python3
"""
Script to fix user role enum values by converting lowercase to uppercase.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings


async def fix_user_roles():
    """Fix user role enum values by converting to uppercase"""
    # Create database connection with async driver
    db_url = settings.database.url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        db_url,
        echo=True
    )

    async with engine.begin() as conn:
        print("Fixing user role enum values...")

        # Update lowercase 'admin' to uppercase 'ADMIN'
        result = await conn.execute(
            text("UPDATE users SET role = 'ADMIN' WHERE role = 'admin'")
        )
        print(f"✓ Updated {result.rowcount} admin users")

        # Update lowercase 'user' to uppercase 'USER'
        result = await conn.execute(
            text("UPDATE users SET role = 'USER' WHERE role = 'user'")
        )
        print(f"✓ Updated {result.rowcount} regular users")

        print("\nUser role fix completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_user_roles())