#!/usr/bin/env python3
"""
Script to clean up corrupted user data and create fresh demo user.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import hashlib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings


async def cleanup_users():
    """Clean up corrupted user data and create fresh demo user"""
    # Create database connection with async driver
    db_url = settings.database.url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        db_url,
        echo=True
    )

    async with engine.begin() as conn:
        print("Cleaning up user data...")

        # Delete all users to avoid enum issues
        result = await conn.execute(text("DELETE FROM users"))
        print(f"✓ Deleted {result.rowcount} users with potential enum issues")

        # Hash the password (simple approach for demo)
        password = "demo123456"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Create demo user with proper enum value and UUID
        await conn.execute(
            text("""
                INSERT INTO users (id, email, username, password_hash, full_name, role, is_active, is_verified)
                VALUES (gen_random_uuid(), 'demo@example.com', 'demo', :password_hash, 'Demo User', 'USER', true, true)
            """),
            {"password_hash": password_hash}
        )
        print("✓ Created clean demo user with credentials: demo@example.com / demo123456")

        print("\nUser cleanup completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(cleanup_users())