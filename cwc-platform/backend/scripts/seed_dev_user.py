"""Seed a local development/test admin account.

Creates (or resets the password of) test@cwcplatform.com / TestPass123 so a
developer — and the Playwright e2e suite — can log in through the normal
POST /api/auth/login flow. This replaces the removed /api/auth/dev-login
backdoor: it goes through the real password path, it does not skip auth.

Idempotent: safe to run repeatedly. If the user already exists its password is
reset to the known value and it is ensured active.

Run from backend/:
    python -m scripts.seed_dev_user
Override the defaults with env vars:
    SEED_EMAIL=me@example.com SEED_PASSWORD=secret SEED_ROLE=user \
        python -m scripts.seed_dev_user
"""
import asyncio
import os

from sqlalchemy import select

from app.database import async_session_maker
from app.models.user import User
from app.services.auth_service import hash_password

DEFAULT_EMAIL = "test@cwcplatform.com"
DEFAULT_PASSWORD = "TestPass123"
DEFAULT_NAME = "Test User"
DEFAULT_ROLE = "admin"  # admin so it can exercise the auth-gated admin routes


async def seed_user() -> None:
    email = os.getenv("SEED_EMAIL", DEFAULT_EMAIL)
    password = os.getenv("SEED_PASSWORD", DEFAULT_PASSWORD)
    name = os.getenv("SEED_NAME", DEFAULT_NAME)
    role = os.getenv("SEED_ROLE", DEFAULT_ROLE)

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.password_hash = hash_password(password)
            user.is_active = True
            action = "updated (password reset)"
        else:
            user = User(
                email=email,
                name=name,
                password_hash=hash_password(password),
                role=role,
                is_active=True,
            )
            session.add(user)
            action = "created"

        await session.commit()

    print(f"Seed user {action}: {email} / {password} (role={role})")


if __name__ == "__main__":
    asyncio.run(seed_user())
