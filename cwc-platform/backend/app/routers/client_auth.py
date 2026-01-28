"""
Client Portal Authentication Router.
Handles magic link login for clients.
"""
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.client import (
    MagicLinkRequest,
    MagicLinkResponse,
    VerifyTokenRequest,
    ClientSession,
    ClientContact,
)
from app.services.client_auth_service import ClientAuthService
from app.config import get_settings

router = APIRouter(prefix="/api/client/auth", tags=["Client Auth"])
settings = get_settings()


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/request-login", response_model=MagicLinkResponse)
async def request_magic_link(
    data: MagicLinkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a magic link login email.

    The email will contain a one-time link valid for 15 minutes.
    For security, this always returns success even if email not found.
    """
    service = ClientAuthService(db)

    result = await service.request_magic_link(
        email=data.email,
        base_url=settings.frontend_url,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return MagicLinkResponse(**result)


@router.post("/verify-token", response_model=ClientSession)
async def verify_token(
    data: VerifyTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify magic link token and create session.

    Returns a session token that should be stored and used for subsequent requests.
    """
    service = ClientAuthService(db)

    result = await service.verify_token(
        token=data.token,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return ClientSession(
        session_token=result["session_token"],
        contact=ClientContact(**result["contact"]),
    )


@router.get("/me", response_model=ClientContact)
async def get_current_client(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current logged-in client info.

    Requires Authorization header with session token.
    """
    from sqlalchemy import select
    from app.models.organization import Organization

    # Extract token from "Bearer <token>" format
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    service = ClientAuthService(db)
    contact = await service.get_current_client(token)

    # Get organization info if contact belongs to one
    org_name = None
    org_logo_url = None
    if contact.organization_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == contact.organization_id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            org_name = org.name
            org_logo_url = org.logo_url

    return ClientContact(
        id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        organization_id=contact.organization_id,
        organization_name=org_name,
        organization_logo_url=org_logo_url,
        is_org_admin=contact.is_org_admin,
    )


@router.post("/logout", response_model=MagicLinkResponse)
async def logout(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """
    End client session.
    """
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    service = ClientAuthService(db)
    result = await service.logout(token)

    return MagicLinkResponse(**result)
