"""
Client Portal Audit Logging Service.
Logs all portal access events for security and compliance.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal_audit_log import PortalAuditLog


class PortalAuditService:
    """Service for logging client portal access events."""

    # Action constants
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_LOGIN_FAILED = "login_failed"
    ACTION_VIEW_DASHBOARD = "view_dashboard"
    ACTION_VIEW_INVOICE = "view_invoice"
    ACTION_VIEW_CONTRACT = "view_contract"
    ACTION_DOWNLOAD_CONTRACT_PDF = "download_contract_pdf"
    ACTION_VIEW_BOOKING = "view_booking"
    ACTION_CANCEL_BOOKING = "cancel_booking"
    ACTION_VIEW_PROJECT = "view_project"
    ACTION_VIEW_SESSION = "view_session"
    ACTION_UPDATE_PROFILE = "update_profile"
    ACTION_VIEW_ORG_DASHBOARD = "view_org_dashboard"
    ACTION_VIEW_ORG_TEAM = "view_org_team"
    ACTION_VIEW_ORG_BILLING = "view_org_billing"

    async def log(
        self,
        db: AsyncSession,
        contact_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> PortalAuditLog:
        """Log a portal access event."""
        log_entry = PortalAuditLog.log_action(
            contact_id=contact_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        db.add(log_entry)
        # Note: Caller should handle commit
        return log_entry

    async def log_login(
        self,
        db: AsyncSession,
        contact_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PortalAuditLog:
        """Log a successful login."""
        return await self.log(
            db=db,
            contact_id=contact_id,
            action=self.ACTION_LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_logout(
        self,
        db: AsyncSession,
        contact_id: str,
        ip_address: Optional[str] = None,
    ) -> PortalAuditLog:
        """Log a logout."""
        return await self.log(
            db=db,
            contact_id=contact_id,
            action=self.ACTION_LOGOUT,
            ip_address=ip_address,
        )

    async def log_resource_access(
        self,
        db: AsyncSession,
        contact_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
    ) -> PortalAuditLog:
        """Log access to a resource (invoice, contract, etc.)."""
        return await self.log(
            db=db,
            contact_id=contact_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
        )


# Singleton instance
portal_audit_service = PortalAuditService()
