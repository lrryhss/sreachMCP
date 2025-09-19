#!/usr/bin/env python3
"""Test script to debug user creation"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext

from src.config import settings
from src.database.models import User, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def test_creation():
    """Test user creation with debug output"""
    # Create database connection
    db_url = settings.database.url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url, echo=False)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print(f"UserRole.ADMIN = {UserRole.ADMIN}")
        print(f"UserRole.ADMIN.value = {UserRole.ADMIN.value}")
        print(f"UserRole.USER = {UserRole.USER}")
        print(f"UserRole.USER.value = {UserRole.USER.value}")

        # Try direct SQL insert first
        admin_id = uuid4()
        test_id = uuid4()
        admin_hash = pwd_context.hash("admin123")
        test_hash = pwd_context.hash("test123")

        print("\nAttempting direct SQL insert...")
        try:
            await session.execute(
                text("""
                    INSERT INTO users (id, email, username, password_hash, full_name, role, is_active, is_verified, created_at, preferences)
                    VALUES (:id, :email, :username, :password_hash, :full_name, CAST(:role AS user_role), :is_active, :is_verified, :created_at, CAST(:preferences AS jsonb))
                """),
                {
                    "id": admin_id,
                    "email": "admin@example.com",
                    "username": "admin",
                    "password_hash": admin_hash,
                    "full_name": "Administrator",
                    "role": "admin",  # Direct lowercase string
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow(),
                    "preferences": "{}"
                }
            )

            await session.execute(
                text("""
                    INSERT INTO users (id, email, username, password_hash, full_name, role, is_active, is_verified, created_at, preferences)
                    VALUES (:id, :email, :username, :password_hash, :full_name, CAST(:role AS user_role), :is_active, :is_verified, :created_at, CAST(:preferences AS jsonb))
                """),
                {
                    "id": test_id,
                    "email": "testuser@example.com",
                    "username": "testuser",
                    "password_hash": test_hash,
                    "full_name": "Test User",
                    "role": "user",  # Direct lowercase string
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow(),
                    "preferences": "{}"
                }
            )

            await session.commit()
            print("✓ Direct SQL insert successful!")

            # Verify users were created
            result = await session.execute(
                text("SELECT username, email, role FROM users WHERE username IN ('admin', 'testuser')")
            )
            users = result.fetchall()
            print("\nCreated users:")
            for user in users:
                print(f"  {user.username} ({user.email}): role={user.role}")

            print("\nDefault users created successfully!")
            print("\nCredentials:")
            print("  Admin: admin / admin123")
            print("  Test User: testuser / test123")

        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_creation())