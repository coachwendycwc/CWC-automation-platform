import os
import secrets
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from app.database import get_db
from app.services.auth_service import (
    verify_google_token,
    get_or_create_user,
    create_access_token,
    get_current_user,
    require_admin,
    hash_password,
    verify_password,
    generate_reset_token,
    hash_token,
)
from app.services.email_service import email_service
from app.models.user import User
from app.models.user_invite import UserInvite
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleAuthRequest(BaseModel):
    access_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    invite_token: str


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: Literal["admin", "assistant", "user"] = "user"


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    token: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with Google OAuth.

    Pass the access_token from Google OAuth flow.
    Returns a JWT token for subsequent API requests.
    """
    # Verify Google token and get user info
    google_user = await verify_google_token(request.access_token)

    # Get or create user in our database
    user = await get_or_create_user(db, google_user)

    # Create our own JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return UserResponse.model_validate(current_user)


# ============ Email/Password Authentication ============

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user. Invite-only: requires a valid, unused, unexpired
    invite whose email matches; the new user's role comes from the invite."""
    result = await db.execute(
        select(UserInvite).where(UserInvite.token == request.invite_token)
    )
    invite = result.scalar_one_or_none()

    if (
        invite is None
        or invite.used_at is not None
        or invite.expires_at < datetime.utcnow()
        or invite.email.lower() != request.email.lower()
    ):
        # One generic message: don't let callers probe which check failed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid invite is required to register",
        )

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user with the role the invite grants
    user = User(
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password),
        role=invite.role,
    )
    invite.used_at = datetime.utcnow()
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/invites", response_model=InviteResponse, status_code=201)
async def create_invite(
    request: InviteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a registration invite and email the link (admin only)."""
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    invite = UserInvite(
        email=request.email,
        role=request.role,
        token=secrets.token_urlsafe(32),
        invited_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    invite_link = f"{frontend_url}/register?invite={invite.token}"
    await email_service.send_user_invite(
        to_email=invite.email,
        invite_link=invite_link,
        role=invite.role,
    )

    return InviteResponse.model_validate(invite)


@router.get("/invites", response_model=list[InviteResponse])
async def list_invites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all invites, newest first (admin only)."""
    result = await db.execute(
        select(UserInvite).order_by(UserInvite.created_at.desc())
    )
    return [InviteResponse.model_validate(i) for i in result.scalars().all()]


@router.delete("/invites/{invite_id}", status_code=204)
async def revoke_invite(
    invite_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Revoke an invite so it can no longer be used (admin only)."""
    result = await db.execute(
        select(UserInvite).where(UserInvite.id == invite_id)
    )
    invite = result.scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found")

    await db.delete(invite)
    await db.commit()


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset email."""
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user and user.password_hash:
        # Generate reset token
        token = generate_reset_token()
        # Only the hash is stored; the raw token exists solely in the email.
        user.password_reset_token = hash_token(token)
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()

        # Build reset link
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        reset_link = f"{frontend_url}/reset-password/{token}"

        # Send password reset email
        await email_service.send_password_reset(
            to_email=user.email,
            reset_link=reset_link,
        )

    return MessageResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using token from email."""
    result = await db.execute(
        select(User).where(User.password_reset_token == hash_token(request.token))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Fail closed: a token with no recorded expiry is treated as expired, not
    # as one that never expires.
    if (
        user.password_reset_expires is None
        or user.password_reset_expires < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Update password
    user.password_hash = hash_password(request.password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()

    return MessageResponse(message="Password has been reset successfully")
