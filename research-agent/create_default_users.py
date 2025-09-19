#!/usr/bin/env python3
"""
Create default users for the Research Agent application.
Creates an admin user (admin/admin123) and a test user (testuser/test123).
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from src.config import settings
from src.database.models import User, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_users():
    """Create default admin and test users"""
    # Create database connection
    # Replace postgresql:// with postgresql+asyncpg:// for async support
    db_url = settings.database.url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(
        db_url,
        echo=True
    )

    # Create session maker
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("Creating default users...")

        # Create admin user
        admin_user = User(
            id=uuid4(),
            email="admin@example.com",
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN.value,  # Use the string value
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            preferences={}
        )

        # Create test user
        test_user = User(
            id=uuid4(),
            email="testuser@example.com",
            username="testuser",
            password_hash=pwd_context.hash("test123"),
            full_name="Test User",
            role=UserRole.USER.value,  # Use the string value
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            preferences={}
        )

        # Add users to session
        session.add(admin_user)
        session.add(test_user)

        # Commit the transaction
        await session.commit()

        print("✓ Created admin user:")
        print(f"  Username: admin")
        print(f"  Email: admin@example.com")
        print(f"  Password: admin123")
        print(f"  Role: ADMIN")
        print()

        print("✓ Created test user:")
        print(f"  Username: testuser")
        print(f"  Email: testuser@example.com")
        print(f"  Password: test123")
        print(f"  Role: USER")
        print()

        print("Users created successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_users())