"""Authentication API endpoints"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..database.models import User
from ..services.database_service import DatabaseService
from ..services.auth_service import auth_service
from structlog import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Security scheme
security = HTTPBearer()


# Request/Response models
class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    """User login request"""
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response"""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    db_service = DatabaseService(session)

    user = await auth_service.validate_session(db_service, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    db_service = DatabaseService(session)

    try:
        user = await auth_service.register_user(
            db_service,
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )

        logger.info("User registered", user_id=str(user.id), username=user.username)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    req: Request,
    session: AsyncSession = Depends(get_db)
):
    """Login and receive access tokens"""
    db_service = DatabaseService(session)

    # Authenticate user
    user = await auth_service.authenticate_user(
        db_service,
        request.username_or_email,
        request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get client info
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    # Create session
    tokens = await auth_service.create_user_session(
        db_service,
        user,
        ip_address=ip_address,
        user_agent=user_agent
    )

    logger.info("User logged in", user_id=str(user.id), username=user.username)

    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    session: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    db_service = DatabaseService(session)

    tokens = await auth_service.refresh_session(db_service, request.refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(**tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
):
    """Logout and invalidate session"""
    token = credentials.credentials
    db_service = DatabaseService(session)

    success = await auth_service.logout_user(db_service, token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )

    logger.info("User logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    full_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    db_service = DatabaseService(session)

    updates = {}
    if full_name is not None:
        updates["full_name"] = full_name

    if updates:
        user = await db_service.users.update(current_user.id, **updates)
        await db_service.commit()
    else:
        user = current_user

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    current_password: str,
    new_password: str = Field(..., min_length=8, max_length=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Change user password"""
    db_service = DatabaseService(session)

    # Verify current password
    if not auth_service.verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password
    new_password_hash = auth_service.hash_password(new_password)

    # Update password
    await db_service.users.update(
        current_user.id,
        password_hash=new_password_hash
    )

    # Invalidate all sessions
    await db_service.sessions.delete_by_user(current_user.id)
    await db_service.commit()

    logger.info("Password changed", user_id=str(current_user.id))