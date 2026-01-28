import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.services.auth_service import (
    verify_google_token,
    get_or_create_user,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    generate_reset_token,
)
from app.services.email_service import email_service
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleAuthRequest(BaseModel):
    access_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


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
    """Register a new user with email and password."""
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

    # Create new user
    user = User(
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password),
        role="admin",  # First user is admin, subsequent could be different
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


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
        user.password_reset_token = token
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
        select(User).where(User.password_reset_token == request.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
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


# Dev-only endpoint for testing without Google OAuth
@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(
    email: str = "dev@cwcplatform.com",
    db: AsyncSession = Depends(get_db),
):
    """
    Development-only login endpoint.
    Creates or gets a dev user without Google OAuth.
    Remove in production!
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            name="Development User",
            password_hash=hash_password("dev123"),
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
