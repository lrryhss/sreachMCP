"""Authentication service for Research Agent"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets

from jose import jwt, JWTError
from passlib.context import CryptContext
from structlog import get_logger

from ..config import settings
from ..database.models import User, UserSession
from ..services.database_service import DatabaseService

logger = get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service handling user auth and sessions"""

    def __init__(self):
        """Initialize authentication service"""
        self.secret_key = settings.auth.secret_key
        self.algorithm = settings.auth.algorithm
        self.access_token_expire = timedelta(minutes=settings.auth.access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=settings.auth.refresh_token_expire_days)

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + self.access_token_expire

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + self.refresh_token_expire
        to_encode.update({"exp": expire, "type": "refresh", "jti": secrets.token_hex(16)})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning("JWT decode error", error=str(e))
            return None

    async def authenticate_user(self, db_service: DatabaseService,
                               username_or_email: str, password: str) -> Optional[User]:
        """Authenticate a user with username/email and password"""
        # Try to get user by email first
        user = await db_service.users.get_by_email(username_or_email)

        # If not found, try username
        if not user:
            user = await db_service.users.get_by_username(username_or_email)

        # Verify password
        if not user or not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        await db_service.users.update_last_login(user.id)
        await db_service.commit()

        return user

    async def create_user_session(self, db_service: DatabaseService, user: User,
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None) -> Dict[str, str]:
        """Create a new user session with tokens"""
        # Create tokens
        access_token = self.create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id)}
        )

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + self.access_token_expire

        # Store session in database
        await db_service.sessions.create(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        await db_service.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(self.access_token_expire.total_seconds())
        }

    async def validate_session(self, db_service: DatabaseService, token: str) -> Optional[User]:
        """Validate a session token and return the user"""
        # Decode token
        payload = self.decode_token(token)
        if not payload:
            return None

        # Check token type
        if payload.get("type") != "access":
            return None

        # Get session from database
        session = await db_service.sessions.get_by_token(token)
        if not session:
            return None

        # Check if session is expired
        if session.expires_at < datetime.now(timezone.utc):
            return None

        return session.user

    async def refresh_session(self, db_service: DatabaseService,
                             refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh a user session with a refresh token"""
        # Decode refresh token
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        # Get session by refresh token
        session = await db_service.sessions.get_by_refresh_token(refresh_token)
        if not session:
            return None

        # Get user
        user = session.user
        if not user or not user.is_active:
            return None

        # Delete old session
        await db_service.sessions.delete_by_user(user.id)

        # Create new session
        return await self.create_user_session(db_service, user)

    async def logout_user(self, db_service: DatabaseService, token: str) -> bool:
        """Logout a user by invalidating their session"""
        session = await db_service.sessions.get_by_token(token)
        if not session:
            return False

        # Delete the session
        await db_service.session.delete(UserSession).where(UserSession.token == token)
        await db_service.commit()

        return True

    async def register_user(self, db_service: DatabaseService,
                          email: str, username: str, password: str,
                          full_name: Optional[str] = None) -> User:
        """Register a new user"""
        # Check if user exists
        existing = await db_service.users.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        existing = await db_service.users.get_by_username(username)
        if existing:
            raise ValueError("Username already taken")

        # Hash password
        password_hash = self.hash_password(password)

        # Create user
        user = await db_service.users.create(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name
        )
        await db_service.commit()

        return user


# Global auth service instance
auth_service = AuthService()