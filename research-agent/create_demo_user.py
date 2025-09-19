#!/usr/bin/env python3
"""
Script to create a demo user for testing.
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


async def create_demo_user():
    """Create a demo user for testing"""
    # Create database connection with async driver
    db_url = settings.database.url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        db_url,
        echo=True
    )

    async with engine.begin() as conn:
        print("Creating demo user...")

        # First, delete any existing demo user
        result = await conn.execute(
            text("DELETE FROM users WHERE email = 'demo@example.com' OR username = 'demo'")
        )
        if result.rowcount > 0:
            print(f"✓ Deleted {result.rowcount} existing demo users")

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
        print("✓ Created demo user with credentials: demo@example.com / demo123456")

        print("\nDemo user creation completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_demo_user())