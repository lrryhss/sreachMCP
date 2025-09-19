#!/usr/bin/env python3
"""
Script to create a demo user with proper bcrypt password hashing.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings

# Password hashing (same as auth service)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_proper_demo_user():
    """Create a demo user with proper bcrypt password hashing"""
    # Create database connection with async driver
    db_url = settings.database.url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        db_url,
        echo=True
    )

    async with engine.begin() as conn:
        print("Creating demo user with proper bcrypt password...")

        # Delete any existing demo user
        result = await conn.execute(
            text("DELETE FROM users WHERE email = 'demo@example.com' OR username = 'demo'")
        )
        if result.rowcount > 0:
            print(f"✓ Deleted {result.rowcount} existing demo users")

        # Hash the password using bcrypt (same as auth service)
        password = "demo123456"
        password_hash = pwd_context.hash(password)
        print(f"✓ Generated bcrypt hash: {password_hash[:60]}...")

        # Create demo user with proper bcrypt hash
        await conn.execute(
            text("""
                INSERT INTO users (id, email, username, password_hash, full_name, role, is_active, is_verified)
                VALUES (gen_random_uuid(), 'demo@example.com', 'demo', :password_hash, 'Demo User', 'USER', true, true)
            """),
            {"password_hash": password_hash}
        )
        print("✓ Created demo user with credentials: demo@example.com / demo123456")

        print("\nDemo user creation with proper bcrypt hashing completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_proper_demo_user())