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


def _is_truthy(value) -> bool:
    """Google returns email_verified as a JSON bool or the string "true"."""
    return value is True or (isinstance(value, str) and value.lower() == "true")


async def verify_google_token(access_token: str) -> dict:
    """Verify a Google OAuth token belongs to THIS app, then get user info.

    The audience check is what stops a confused-deputy attack: without it, an
    access token minted for any other Google OAuth client would authenticate
    here as that token's user. email_verified must also hold before the email
    is trusted, because get_or_create_user links accounts by email.
    """
    async with httpx.AsyncClient() as client:
        # 1. Token introspection: who issued this token, and for which client?
        token_info_response = await client.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"access_token": access_token},
        )
        if token_info_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            )
        token_info = token_info_response.json()

        expected_client_id = settings.google_client_id
        if token_info.get("aud") != expected_client_id and token_info.get(
            "azp"
        ) != expected_client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            )

        if not _is_truthy(token_info.get("email_verified")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account email is not verified",
            )

        # 2. Profile details for the account record
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            )
        google_user = response.json()
        # Carry the introspected verification forward so account linking can
        # re-check it independently of which endpoint supplied the profile.
        google_user["email_verified"] = True
        return google_user


async def get_or_create_user(db: AsyncSession, google_user: dict) -> User:
    """Get existing user or create new one from Google OAuth data."""
    google_id = google_user.get("id")
    email = google_user.get("email")

    # Defense in depth: the email drives account lookup and linking below, so
    # refuse to act on one Google never confirmed the user owns.
    if not _is_truthy(google_user.get("email_verified")) and not _is_truthy(
        google_user.get("verified_email")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified",
        )

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
        role="user",  # Google self-sign-in must not grant admin; promote deliberately
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

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that authorizes admin-only endpoints. Authenticates via
    get_current_user, then requires role == 'admin'. Non-admins get 403.

    This is the authorization tier: get_current_user proves *who* you are,
    require_admin proves you're *allowed* to mutate privileged data."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
