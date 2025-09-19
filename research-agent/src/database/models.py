"""SQLAlchemy database models for Research Agent"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, JSON, UniqueConstraint, CheckConstraint, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

Base = declarative_base()


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    SEARCHING = "searching"
    FETCHING = "fetching"
    SYNTHESIZING = "synthesizing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchDepth(str, enum.Enum):
    """Research depth enumeration"""
    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class SharePermission(str, enum.Enum):
    """Share permission levels"""
    READ = "read"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    last_login = Column(TIMESTAMP(timezone=True))
    preferences = Column(JSONB, default={})

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="user")
    shared_by = relationship("ResearchShare", foreign_keys="ResearchShare.shared_by_id",
                           back_populates="sharer", cascade="all, delete-orphan")
    shared_with = relationship("ResearchShare", foreign_keys="ResearchShare.shared_with_id",
                             back_populates="recipient")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class UserSession(Base):
    """User session model for JWT tracking"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, index=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', expires_at='{self.expires_at}')>"


class ResearchTask(Base):
    """Research task model"""
    __tablename__ = "research_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    query = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.PENDING, index=True)
    depth = Column(SQLEnum(ResearchDepth, name="research_depth"), default=ResearchDepth.STANDARD)
    max_sources = Column(Integer, default=20)
    options = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    progress = Column(Integer, default=0)
    error_message = Column(Text)

    # Constraints
    __table_args__ = (
        CheckConstraint('max_sources > 0 AND max_sources <= 100', name='check_max_sources'),
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress'),
    )

    # Relationships
    user = relationship("User", back_populates="research_tasks")
    result = relationship("ResearchResult", back_populates="task", uselist=False, cascade="all, delete-orphan")
    artifacts = relationship("ResearchArtifact", back_populates="task", cascade="all, delete-orphan")
    shares = relationship("ResearchShare", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ResearchTask(task_id='{self.task_id}', status='{self.status}')>"


class ResearchResult(Base):
    """Research result model"""
    __tablename__ = "research_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"),
                    unique=True, nullable=False, index=True)
    synthesis = Column(JSONB, nullable=False)
    sources = Column(JSONB, nullable=False)
    query_analysis = Column(JSONB)
    detailed_analysis = Column(JSONB)
    result_metadata = Column("metadata", JSONB)
    featured_media = Column(JSONB)
    sources_used = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    task = relationship("ResearchTask", back_populates="result")

    def __repr__(self):
        return f"<ResearchResult(task_id='{self.task_id}', sources_used={self.sources_used})>"


class ResearchArtifact(Base):
    """Research artifact model for storing individual pieces of research"""
    __tablename__ = "research_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    artifact_type = Column(String(50), nullable=False, index=True)
    artifact_name = Column(String(255))
    content = Column(Text)
    artifact_metadata = Column("metadata", JSONB)
    size_bytes = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    task = relationship("ResearchTask", back_populates="artifacts")

    def __repr__(self):
        return f"<ResearchArtifact(type='{self.artifact_type}', name='{self.artifact_name}')>"


class ResearchShare(Base):
    """Research sharing model"""
    __tablename__ = "research_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    shared_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    share_token = Column(String(100), unique=True, index=True)
    permission_level = Column(SQLEnum(SharePermission, name="share_permission"), default=SharePermission.READ)
    expires_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_public = Column(Boolean, default=False)

    # Relationships
    task = relationship("ResearchTask", back_populates="shares")
    sharer = relationship("User", foreign_keys=[shared_by_id], back_populates="shared_by")
    recipient = relationship("User", foreign_keys=[shared_with_id], back_populates="shared_with")

    def __repr__(self):
        return f"<ResearchShare(token='{self.share_token}', permission='{self.permission_level}')>"