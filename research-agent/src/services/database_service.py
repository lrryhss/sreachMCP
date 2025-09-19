"""Database service layer for Research Agent"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import secrets

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog import get_logger

from ..database.models import (
    User, UserSession, ResearchTask, ResearchResult,
    ResearchArtifact, ResearchShare, TaskStatus, SharePermission
)

logger = get_logger()


class UserRepository:
    """Repository for user operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, username: str, password_hash: str,
                    full_name: Optional[str] = None) -> User:
        """Create a new user"""
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update user details"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )

    async def delete(self, user_id: UUID) -> bool:
        """Delete a user"""
        result = await self.session.execute(
            delete(User).where(User.id == user_id)
        )
        return result.rowcount > 0


class SessionRepository:
    """Repository for session operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, token: str, refresh_token: str,
                    expires_at: datetime, ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None) -> UserSession:
        """Create a new session"""
        session = UserSession(
            user_id=user_id,
            token=token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_by_token(self, token: str) -> Optional[UserSession]:
        """Get session by access token"""
        result = await self.session.execute(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(UserSession.token == token)
        )
        return result.scalar_one_or_none()

    async def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token"""
        result = await self.session.execute(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(UserSession.refresh_token == refresh_token)
        )
        return result.scalar_one_or_none()

    async def delete_expired(self) -> int:
        """Delete expired sessions"""
        result = await self.session.execute(
            delete(UserSession)
            .where(UserSession.expires_at < datetime.utcnow())
        )
        return result.rowcount

    async def delete_by_user(self, user_id: UUID) -> int:
        """Delete all sessions for a user"""
        result = await self.session.execute(
            delete(UserSession).where(UserSession.user_id == user_id)
        )
        return result.rowcount


class ResearchTaskRepository:
    """Repository for research task operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_id: str, query: str, user_id: Optional[UUID] = None,
                    depth: str = "standard", max_sources: int = 20,
                    options: Optional[Dict[str, Any]] = None) -> ResearchTask:
        """Create a new research task"""
        task = ResearchTask(
            task_id=task_id,
            query=query,
            user_id=user_id,
            depth=depth,
            max_sources=max_sources,
            options=options or {}
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: UUID) -> Optional[ResearchTask]:
        """Get task by ID"""
        result = await self.session.execute(
            select(ResearchTask)
            .options(
                selectinload(ResearchTask.result),
                selectinload(ResearchTask.artifacts)
            )
            .where(ResearchTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_by_task_id(self, task_id: str) -> Optional[ResearchTask]:
        """Get task by external task ID"""
        result = await self.session.execute(
            select(ResearchTask)
            .options(
                selectinload(ResearchTask.result),
                selectinload(ResearchTask.artifacts)
            )
            .where(ResearchTask.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_user_tasks(self, user_id: UUID, limit: int = 10,
                            offset: int = 0) -> List[ResearchTask]:
        """Get tasks for a user"""
        result = await self.session.execute(
            select(ResearchTask)
            .where(ResearchTask.user_id == user_id)
            .order_by(ResearchTask.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update_status(self, task_id: str, status: TaskStatus,
                          progress: Optional[int] = None,
                          error_message: Optional[str] = None) -> Optional[ResearchTask]:
        """Update task status and progress"""
        values = {"status": status}

        if progress is not None:
            values["progress"] = progress

        if status == TaskStatus.ANALYZING and "started_at" not in values:
            values["started_at"] = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            values["completed_at"] = datetime.utcnow()

        if error_message:
            values["error_message"] = error_message

        stmt = (
            update(ResearchTask)
            .where(ResearchTask.task_id == task_id)
            .values(**values)
            .returning(ResearchTask)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, query: str, user_id: Optional[UUID] = None,
                    limit: int = 10) -> List[ResearchTask]:
        """Search tasks by query"""
        stmt = select(ResearchTask)

        if user_id:
            stmt = stmt.where(ResearchTask.user_id == user_id)

        stmt = stmt.where(
            func.to_tsvector('english', ResearchTask.query).match(query)
        ).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()


class ResearchResultRepository:
    """Repository for research result operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_id: UUID, synthesis: Dict[str, Any],
                    sources: List[Dict[str, Any]], query_analysis: Optional[Dict[str, Any]] = None,
                    detailed_analysis: Optional[Dict[str, Any]] = None,
                    metadata: Optional[Dict[str, Any]] = None,
                    featured_media: Optional[Dict[str, Any]] = None,
                    sources_used: Optional[int] = None,
                    synthesis_embedding: Optional[List[float]] = None,
                    query_embedding: Optional[List[float]] = None) -> ResearchResult:
        """Create research result"""
        result = ResearchResult(
            task_id=task_id,
            synthesis=synthesis,
            sources=sources,
            query_analysis=query_analysis,
            detailed_analysis=detailed_analysis,
            result_metadata=metadata,
            featured_media=featured_media,
            sources_used=sources_used or len(sources),
            synthesis_embedding=synthesis_embedding,
            query_embedding=query_embedding
        )
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_by_task_id(self, task_id: UUID) -> Optional[ResearchResult]:
        """Get result by task ID"""
        result = await self.session.execute(
            select(ResearchResult).where(ResearchResult.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def update(self, task_id: UUID, **kwargs) -> Optional[ResearchResult]:
        """Update research result"""
        stmt = (
            update(ResearchResult)
            .where(ResearchResult.task_id == task_id)
            .values(**kwargs)
            .returning(ResearchResult)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ResearchShareRepository:
    """Repository for research sharing operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_id: UUID, shared_by_id: UUID,
                    shared_with_id: Optional[UUID] = None,
                    permission: SharePermission = SharePermission.READ,
                    expires_in_days: Optional[int] = None,
                    is_public: bool = False) -> ResearchShare:
        """Create a share link"""
        share_token = secrets.token_urlsafe(32)
        expires_at = None

        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        share = ResearchShare(
            task_id=task_id,
            shared_by_id=shared_by_id,
            shared_with_id=shared_with_id,
            share_token=share_token,
            permission_level=permission,
            expires_at=expires_at,
            is_public=is_public
        )
        self.session.add(share)
        await self.session.flush()
        return share

    async def get_by_token(self, token: str) -> Optional[ResearchShare]:
        """Get share by token"""
        result = await self.session.execute(
            select(ResearchShare)
            .options(
                selectinload(ResearchShare.task).selectinload(ResearchTask.result),
                selectinload(ResearchShare.sharer)
            )
            .where(ResearchShare.share_token == token)
        )
        return result.scalar_one_or_none()

    async def get_user_shares(self, user_id: UUID) -> List[ResearchShare]:
        """Get shares created by a user"""
        result = await self.session.execute(
            select(ResearchShare)
            .options(selectinload(ResearchShare.task))
            .where(ResearchShare.shared_by_id == user_id)
            .order_by(ResearchShare.created_at.desc())
        )
        return result.scalars().all()

    async def delete(self, share_id: UUID) -> bool:
        """Delete a share"""
        result = await self.session.execute(
            delete(ResearchShare).where(ResearchShare.id == share_id)
        )
        return result.rowcount > 0


class DatabaseService:
    """Main database service aggregating all repositories"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.sessions = SessionRepository(session)
        self.tasks = ResearchTaskRepository(session)
        self.results = ResearchResultRepository(session)
        self.shares = ResearchShareRepository(session)

    async def commit(self):
        """Commit the current transaction"""
        await self.session.commit()

    async def rollback(self):
        """Rollback the current transaction"""
        await self.session.rollback()

    async def close(self):
        """Close the session"""
        await self.session.close()