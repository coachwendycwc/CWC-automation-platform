"""
Tests for Portal Audit service.
"""
import pytest
import uuid

from app.services.portal_audit_service import PortalAuditService, portal_audit_service
from app.models.portal_audit_log import PortalAuditLog
from app.models.contact import Contact


@pytest.fixture
async def audit_service():
    """Create portal audit service instance."""
    return PortalAuditService()


class TestPortalAuditServiceConstants:
    """Tests for audit service constants."""

    def test_action_constants_exist(self):
        """Test all action constants are defined."""
        service = PortalAuditService()

        assert service.ACTION_LOGIN == "login"
        assert service.ACTION_LOGOUT == "logout"
        assert service.ACTION_LOGIN_FAILED == "login_failed"
        assert service.ACTION_VIEW_DASHBOARD == "view_dashboard"
        assert service.ACTION_VIEW_INVOICE == "view_invoice"
        assert service.ACTION_VIEW_CONTRACT == "view_contract"
        assert service.ACTION_DOWNLOAD_CONTRACT_PDF == "download_contract_pdf"
        assert service.ACTION_VIEW_BOOKING == "view_booking"
        assert service.ACTION_CANCEL_BOOKING == "cancel_booking"
        assert service.ACTION_VIEW_PROJECT == "view_project"
        assert service.ACTION_VIEW_SESSION == "view_session"
        assert service.ACTION_UPDATE_PROFILE == "update_profile"
        assert service.ACTION_VIEW_ORG_DASHBOARD == "view_org_dashboard"
        assert service.ACTION_VIEW_ORG_TEAM == "view_org_team"
        assert service.ACTION_VIEW_ORG_BILLING == "view_org_billing"


class TestPortalAuditServiceLog:
    """Tests for general logging."""

    @pytest.mark.asyncio
    async def test_log_basic(self, db_session, audit_service, test_contact: Contact):
        """Test basic log creation."""
        result = await audit_service.log(
            db=db_session,
            contact_id=test_contact.id,
            action="test_action",
        )

        assert result is not None
        assert result.contact_id == test_contact.id
        assert result.action == "test_action"

    @pytest.mark.asyncio
    async def test_log_with_resource(self, db_session, audit_service, test_contact: Contact):
        """Test log with resource details."""
        resource_id = str(uuid.uuid4())

        result = await audit_service.log(
            db=db_session,
            contact_id=test_contact.id,
            action="view_invoice",
            resource_type="invoice",
            resource_id=resource_id,
        )

        assert result.resource_type == "invoice"
        assert result.resource_id == resource_id

    @pytest.mark.asyncio
    async def test_log_with_ip_and_agent(self, db_session, audit_service, test_contact: Contact):
        """Test log with IP and user agent."""
        result = await audit_service.log(
            db=db_session,
            contact_id=test_contact.id,
            action="login",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Chrome/120",
        )

        assert result.ip_address == "192.168.1.100"
        assert result.user_agent == "Mozilla/5.0 Chrome/120"

    @pytest.mark.asyncio
    async def test_log_with_details(self, db_session, audit_service, test_contact: Contact):
        """Test log with additional details."""
        result = await audit_service.log(
            db=db_session,
            contact_id=test_contact.id,
            action="update_profile",
            details={"field_changed": "phone", "old_value": "555-1234"},
        )

        assert result.details is not None
        assert result.details["field_changed"] == "phone"


class TestPortalAuditServiceLogin:
    """Tests for login logging."""

    @pytest.mark.asyncio
    async def test_log_login(self, db_session, audit_service, test_contact: Contact):
        """Test login event logging."""
        result = await audit_service.log_login(
            db=db_session,
            contact_id=test_contact.id,
            ip_address="10.0.0.1",
            user_agent="Safari/17.0",
        )

        assert result.action == "login"
        assert result.ip_address == "10.0.0.1"
        assert result.user_agent == "Safari/17.0"

    @pytest.mark.asyncio
    async def test_log_login_minimal(self, db_session, audit_service, test_contact: Contact):
        """Test login with minimal info."""
        result = await audit_service.log_login(
            db=db_session,
            contact_id=test_contact.id,
        )

        assert result.action == "login"
        assert result.ip_address is None


class TestPortalAuditServiceLogout:
    """Tests for logout logging."""

    @pytest.mark.asyncio
    async def test_log_logout(self, db_session, audit_service, test_contact: Contact):
        """Test logout event logging."""
        result = await audit_service.log_logout(
            db=db_session,
            contact_id=test_contact.id,
            ip_address="10.0.0.1",
        )

        assert result.action == "logout"
        assert result.ip_address == "10.0.0.1"


class TestPortalAuditServiceResourceAccess:
    """Tests for resource access logging."""

    @pytest.mark.asyncio
    async def test_log_invoice_view(self, db_session, audit_service, test_contact: Contact):
        """Test invoice view logging."""
        invoice_id = str(uuid.uuid4())

        result = await audit_service.log_resource_access(
            db=db_session,
            contact_id=test_contact.id,
            action=PortalAuditService.ACTION_VIEW_INVOICE,
            resource_type="invoice",
            resource_id=invoice_id,
            ip_address="192.168.1.1",
        )

        assert result.action == "view_invoice"
        assert result.resource_type == "invoice"
        assert result.resource_id == invoice_id

    @pytest.mark.asyncio
    async def test_log_contract_view(self, db_session, audit_service, test_contact: Contact):
        """Test contract view logging."""
        contract_id = str(uuid.uuid4())

        result = await audit_service.log_resource_access(
            db=db_session,
            contact_id=test_contact.id,
            action=PortalAuditService.ACTION_VIEW_CONTRACT,
            resource_type="contract",
            resource_id=contract_id,
        )

        assert result.action == "view_contract"
        assert result.resource_type == "contract"

    @pytest.mark.asyncio
    async def test_log_contract_download(self, db_session, audit_service, test_contact: Contact):
        """Test contract PDF download logging."""
        contract_id = str(uuid.uuid4())

        result = await audit_service.log_resource_access(
            db=db_session,
            contact_id=test_contact.id,
            action=PortalAuditService.ACTION_DOWNLOAD_CONTRACT_PDF,
            resource_type="contract",
            resource_id=contract_id,
        )

        assert result.action == "download_contract_pdf"

    @pytest.mark.asyncio
    async def test_log_booking_cancel(self, db_session, audit_service, test_contact: Contact):
        """Test booking cancellation logging."""
        booking_id = str(uuid.uuid4())

        result = await audit_service.log_resource_access(
            db=db_session,
            contact_id=test_contact.id,
            action=PortalAuditService.ACTION_CANCEL_BOOKING,
            resource_type="booking",
            resource_id=booking_id,
        )

        assert result.action == "cancel_booking"


class TestPortalAuditServiceSingleton:
    """Tests for singleton instance."""

    def test_singleton_exists(self):
        """Test singleton instance is available."""
        assert portal_audit_service is not None
        assert isinstance(portal_audit_service, PortalAuditService)

    def test_singleton_has_methods(self):
        """Test singleton has all required methods."""
        assert hasattr(portal_audit_service, "log")
        assert hasattr(portal_audit_service, "log_login")
        assert hasattr(portal_audit_service, "log_logout")
        assert hasattr(portal_audit_service, "log_resource_access")
