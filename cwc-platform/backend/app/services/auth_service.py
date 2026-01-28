from datetime import datetime, timedelta
import secrets
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from passlib.context import CryptContext

from app.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_reset_token() -> str:
    """Generate a secure password reset token."""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def verify_google_token(access_token: str) -> dict:
    """Verify Google OAuth token and get user info."""
    async with httpx.AsyncClient() as client:
        # Get user info from Google
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            )
        return response.json()


async def get_or_create_user(db: AsyncSession, google_user: dict) -> User:
    """Get existing user or create new one from Google OAuth data."""
    google_id = google_user.get("id")
    email = google_user.get("email")

    # Try to find by google_id first
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user:
        return user

    # Try to find by email (for linking existing accounts)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Link Google account to existing user
        user.google_id = google_id
        user.avatar_url = google_user.get("picture")
        await db.commit()
        await db.refresh(user)
        return user

    # Create new user
    user = User(
        email=email,
        name=google_user.get("name"),
        google_id=google_id,
        avatar_url=google_user.get("picture"),
        role="admin",  # First user is admin
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
