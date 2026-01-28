"""
Client Portal Authentication Service.
Handles magic link authentication for clients accessing their portal.
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.contact import Contact
from app.models.client_session import ClientSession
from app.models.portal_audit_log import PortalAuditLog
from app.services.email_service import email_service, _create_html_email

logger = logging.getLogger(__name__)
settings = get_settings()

# Magic link token expiry (15 minutes)
MAGIC_LINK_EXPIRY_MINUTES = 15

# Session expiry (7 days)
SESSION_EXPIRY_DAYS = 7

# Rate limiting: max magic link requests per hour per email
MAX_MAGIC_LINKS_PER_HOUR = 3


class ClientAuthService:
    """Handles client portal authentication via magic links."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_magic_link(
        self,
        email: str,
        base_url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Request a magic link for client login.

        Args:
            email: Client's email address
            base_url: Frontend base URL for magic link
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            Dict with success message

        Raises:
            HTTPException: If contact not found or rate limited
        """
        # Find contact by email
        result = await self.db.execute(
            select(Contact).where(Contact.email == email)
        )
        contact = result.scalar_one_or_none()

        if not contact:
            # Don't reveal if email exists for security
            logger.info(f"Magic link requested for unknown email: {email}")
            return {"message": "If an account exists with this email, you will receive a login link."}

        if not contact.portal_enabled:
            logger.info(f"Magic link requested for disabled portal: {contact.id}")
            return {"message": "If an account exists with this email, you will receive a login link."}

        # Check rate limiting
        rate_limit_check = await self._check_rate_limit(contact.id)
        if not rate_limit_check:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login requests. Please try again later.",
            )

        # Generate magic link token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

        # Create session record with magic link token
        session = ClientSession(
            contact_id=contact.id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            email_sent_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.commit()

        # Send magic link email
        magic_link = f"{base_url}/client/verify/{token}"
        await self._send_magic_link_email(contact, magic_link)

        logger.info(f"Magic link sent to contact {contact.id}")
        return {"message": "If an account exists with this email, you will receive a login link."}

    async def verify_token(
        self,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Verify magic link token and create session.

        Args:
            token: Magic link token
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            Dict with session_token and contact info

        Raises:
            HTTPException: If token invalid or expired
        """
        # Find session by token
        result = await self.db.execute(
            select(ClientSession).where(
                ClientSession.token == token,
                ClientSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired login link.",
            )

        # Check if token already used
        if session.token_used_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This login link has already been used.",
            )

        # Check if token expired
        if datetime.utcnow() > session.expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This login link has expired. Please request a new one.",
            )

        # Mark token as used
        session.token_used_at = datetime.utcnow()

        # Create JWT session token
        session_expires = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)
        session_token = jwt.encode(
            {
                "sub": session.contact_id,
                "session_id": session.id,
                "exp": session_expires,
                "type": "client",
            },
            settings.secret_key,
            algorithm="HS256",
        )

        # Update session with JWT
        session.session_token = session_token
        session.expires_at = session_expires
        session.ip_address = ip_address or session.ip_address
        session.user_agent = user_agent or session.user_agent

        await self.db.commit()

        # Get contact info with organization
        result = await self.db.execute(
            select(Contact).where(Contact.id == session.contact_id)
        )
        contact = result.scalar_one()

        # Get organization info if contact belongs to one
        org_name = None
        org_logo_url = None
        if contact.organization_id:
            from app.models.organization import Organization
            org_result = await self.db.execute(
                select(Organization).where(Organization.id == contact.organization_id)
            )
            org = org_result.scalar_one_or_none()
            if org:
                org_name = org.name
                org_logo_url = org.logo_url

        # Log successful login
        audit_log = PortalAuditLog.log_action(
            contact_id=contact.id,
            action="login",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)
        await self.db.commit()

        logger.info(f"Client session created for contact {contact.id}")

        return {
            "session_token": session_token,
            "contact": {
                "id": contact.id,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "organization_id": contact.organization_id,
                "organization_name": org_name,
                "organization_logo_url": org_logo_url,
                "is_org_admin": contact.is_org_admin,
            },
        }

    async def get_current_client(self, session_token: str) -> Contact:
        """
        Get current client from session token.

        Args:
            session_token: JWT session token

        Returns:
            Contact object

        Raises:
            HTTPException: If session invalid
        """
        try:
            payload = jwt.decode(
                session_token,
                settings.secret_key,
                algorithms=["HS256"],
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session. Please log in again.",
            )

        if payload.get("type") != "client":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session type.",
            )

        contact_id = payload.get("sub")
        session_id = payload.get("session_id")

        # Verify session is still active
        result = await self.db.execute(
            select(ClientSession).where(
                ClientSession.id == session_id,
                ClientSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please log in again.",
            )

        # Get contact
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()

        if not contact or not contact.portal_enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access denied.",
            )

        return contact

    async def logout(self, session_token: str) -> dict:
        """
        End client session.

        Args:
            session_token: JWT session token

        Returns:
            Dict with success message
        """
        try:
            payload = jwt.decode(
                session_token,
                settings.secret_key,
                algorithms=["HS256"],
            )
            session_id = payload.get("session_id")

            if session_id:
                result = await self.db.execute(
                    select(ClientSession).where(ClientSession.id == session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    session.is_active = False

                    # Log logout
                    audit_log = PortalAuditLog.log_action(
                        contact_id=session.contact_id,
                        action="logout",
                    )
                    self.db.add(audit_log)
                    await self.db.commit()

        except JWTError:
            pass  # Token already invalid, that's fine

        return {"message": "Logged out successfully"}

    async def _check_rate_limit(self, contact_id: str) -> bool:
        """Check if contact has exceeded magic link rate limit."""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await self.db.execute(
            select(ClientSession).where(
                ClientSession.contact_id == contact_id,
                ClientSession.email_sent_at > one_hour_ago,
            )
        )
        recent_sessions = result.scalars().all()

        return len(recent_sessions) < MAX_MAGIC_LINKS_PER_HOUR

    async def _send_magic_link_email(self, contact: Contact, magic_link: str) -> bool:
        """Send magic link email to contact."""
        if not contact.email:
            return False

        subject = "Your CWC Portal Login Link"
        first_name = contact.first_name or "there"

        body = f"""
Hi {first_name},

Click below to access your Client Portal:

{magic_link}

This link expires in {MAGIC_LINK_EXPIRY_MINUTES} minutes and can only be used once.

If you didn't request this, you can ignore this email.

- Coaching Women of Color
"""

        html_content = f'''
            <p>Click below to access your Client Portal:</p>
            <div style="background-color: #f3f4f6; border-radius: 8px; padding: 16px; margin: 20px 0; text-align: center;">
                <p style="margin: 0; color: #6b7280; font-size: 13px;">
                    This link expires in {MAGIC_LINK_EXPIRY_MINUTES} minutes and can only be used once.
                </p>
            </div>
            <p style="font-size: 13px; color: #9ca3af;">
                If you didn't request this, you can safely ignore this email.
            </p>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {first_name},",
            content=html_content,
            cta_text="Access Portal",
            cta_url=magic_link,
            footer_text="- Coaching Women of Color",
        )

        return await email_service._send_email(contact.email, subject, body, html_body)
