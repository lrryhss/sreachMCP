#!/usr/bin/env python3
"""Create an admin user for the Research Agent"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.models import User
from src.services.auth_service import AuthService
from src.config import settings
import uuid
from datetime import datetime

async def create_admin_user():
    """Create an admin user account"""

    # Create database engine
    engine = create_async_engine(
        settings.database.url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Initialize auth service
    auth_service = AuthService()

    async with async_session() as session:
        try:
            # Check if admin user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("Admin user already exists!")
                print(f"Username: admin")
                print(f"Email: {existing_user.email}")
                return

            # Create admin user
            admin_user = User(
                id=uuid.uuid4(),
                email="admin@research-agent.local",
                username="admin",
                password_hash=auth_service.hash_password("admin123"),
                full_name="System Administrator",
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            session.add(admin_user)
            await session.commit()

            print("✅ Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@research-agent.local")
            print("\nYou can now login with these credentials.")

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin_user())