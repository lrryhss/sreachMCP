"""Admin API endpoints for user management"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..database.models import User, UserRole, ResearchTask
from ..services.database_service import DatabaseService
from ..services.auth_service import auth_service
from .auth import get_admin_user, UserResponse
from structlog import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserUpdateRequest(BaseModel):
    """User update request"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern="^(user|admin)$")
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_users: int
    active_users: int
    verified_users: int
    admin_users: int
    total_research_tasks: int
    research_by_status: dict


class CreateAdminRequest(BaseModel):
    """Create admin user request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    role: Optional[str] = Query(None, pattern="^(user|admin)$", description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """List all users with pagination and filters"""
    db_service = DatabaseService(session)

    # Build query
    query = select(User)

    # Apply filters
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    if role:
        query = query.where(User.role == UserRole(role))

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    query = query.order_by(User.created_at.desc())

    # Execute query
    result = await session.execute(query)
    users = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # Convert to response
    user_responses = [
        UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role.value if hasattr(user, 'role') else "user",
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        for user in users
    ]

    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID"""
    db_service = DatabaseService(session)

    user = await db_service.users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value if hasattr(user, 'role') else "user",
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Update a user's information"""
    db_service = DatabaseService(session)

    # Get user
    user = await db_service.users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prepare updates
    updates = {}
    if request.email is not None:
        # Check if email is already in use
        existing = await db_service.users.get_by_email(request.email)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        updates["email"] = request.email

    if request.username is not None:
        # Check if username is already in use
        existing = await db_service.users.get_by_username(request.username)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        updates["username"] = request.username

    if request.full_name is not None:
        updates["full_name"] = request.full_name

    if request.role is not None:
        updates["role"] = UserRole(request.role)

    if request.is_active is not None:
        updates["is_active"] = request.is_active

    if request.is_verified is not None:
        updates["is_verified"] = request.is_verified

    # Update user
    if updates:
        user = await db_service.users.update(user_id, **updates)
        await db_service.commit()

    logger.info("User updated by admin", user_id=str(user_id), admin_id=str(admin.id))

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.value if hasattr(user, 'role') else "user",
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Delete a user account"""
    db_service = DatabaseService(session)

    # Prevent self-deletion
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account"
        )

    # Get user
    user = await db_service.users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete user
    await db_service.session.delete(user)
    await db_service.commit()

    logger.info("User deleted by admin", user_id=str(user_id), admin_id=str(admin.id))


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    new_password: str = Field(..., min_length=8, max_length=100)


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(
    user_id: UUID,
    request: ResetPasswordRequest,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Reset a user's password"""
    db_service = DatabaseService(session)

    # Get user
    user = await db_service.users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Hash new password
    password_hash = auth_service.hash_password(request.new_password)

    # Update password
    await db_service.users.update(user_id, password_hash=password_hash)

    # Invalidate all user sessions
    await db_service.sessions.delete_by_user(user_id)
    await db_service.commit()

    logger.info("User password reset by admin", user_id=str(user_id), admin_id=str(admin.id))


@router.post("/create-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    request: CreateAdminRequest,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Create a new admin user"""
    db_service = DatabaseService(session)

    try:
        # Register user normally
        user = await auth_service.register_user(
            db_service,
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )

        # Update role to admin
        user = await db_service.users.update(user.id, role=UserRole.ADMIN)
        await db_service.commit()

        logger.info("Admin user created", user_id=str(user.id), created_by=str(admin.id))

        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user and system statistics"""
    # Get user counts
    total_users = await session.scalar(
        select(func.count()).select_from(User)
    )

    active_users = await session.scalar(
        select(func.count()).select_from(User).where(User.is_active == True)
    )

    verified_users = await session.scalar(
        select(func.count()).select_from(User).where(User.is_verified == True)
    )

    admin_users = await session.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
    ) if hasattr(User, 'role') else 1

    # Get research task counts
    total_research = await session.scalar(
        select(func.count()).select_from(ResearchTask)
    )

    # Get research by status
    status_results = await session.execute(
        select(ResearchTask.status, func.count(ResearchTask.id))
        .group_by(ResearchTask.status)
    )

    research_by_status = {
        status.value: count for status, count in status_results
    }

    return UserStatsResponse(
        total_users=total_users or 0,
        active_users=active_users or 0,
        verified_users=verified_users or 0,
        admin_users=admin_users or 0,
        total_research_tasks=total_research or 0,
        research_by_status=research_by_status
    )