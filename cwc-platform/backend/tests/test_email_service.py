"""
Tests for Email service with Gmail SMTP integration.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.models.invoice import Invoice
from app.models.contact import Contact
from app.services.email_service import EmailService, _create_html_email


class TestEmailServiceConfiguration:
    """Tests for email service configuration."""

    def test_service_not_configured(self):
        """Test service initializes in stub mode without credentials."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            assert service.is_configured is False

    def test_service_configured(self):
        """Test service initializes with credentials."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = "test@gmail.com"
            mock_settings.return_value.gmail_app_password = "app-password"

            service = EmailService()
            assert service.is_configured is True


class TestCreateHtmlEmail:
    """Tests for HTML email template generation."""

    def test_create_html_email_basic(self):
        """Test basic HTML email creation."""
        html = _create_html_email(
            title="Test Email",
            greeting="Hi John,",
            content="<p>This is a test.</p>",
        )

        assert "Test Email" in html
        assert "Hi John," in html
        assert "This is a test." in html
        assert "CWC Coaching" in html

    def test_create_html_email_with_cta(self):
        """Test HTML email with call-to-action button."""
        html = _create_html_email(
            title="Test Email",
            greeting="Hi,",
            content="<p>Content</p>",
            cta_text="Click Here",
            cta_url="https://example.com/action",
        )

        assert "Click Here" in html
        assert "https://example.com/action" in html

    def test_create_html_email_custom_footer(self):
        """Test HTML email with custom footer."""
        html = _create_html_email(
            title="Test",
            greeting="Hi,",
            content="<p>Content</p>",
            footer_text="Custom Footer Text",
        )

        assert "Custom Footer Text" in html


class TestSendEmail:
    """Tests for email sending functionality."""

    @pytest.mark.asyncio
    async def test_send_email_stub_mode(self):
        """Test email logging in stub mode."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service._send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test body",
            )

            assert result is True  # Stub mode always returns True

    @pytest.mark.asyncio
    async def test_send_email_with_smtp(self):
        """Test email sending via SMTP."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = "test@gmail.com"
            mock_settings.return_value.gmail_app_password = "app-password"

            service = EmailService()

            with patch("smtplib.SMTP") as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
                mock_smtp.return_value.__exit__ = Mock(return_value=False)

                result = await service._send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="Test body",
                    html_body="<p>Test body</p>",
                )

                assert result is True
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once()
                mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_failure(self):
        """Test email sending failure handling."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = "test@gmail.com"
            mock_settings.return_value.gmail_app_password = "app-password"

            service = EmailService()

            with patch("smtplib.SMTP") as mock_smtp:
                mock_smtp.return_value.__enter__ = Mock(
                    side_effect=Exception("SMTP error")
                )

                result = await service._send_email(
                    to="recipient@example.com",
                    subject="Test",
                    body="Test",
                )

                assert result is False


class TestInvoiceEmails:
    """Tests for invoice-related emails."""

    @pytest.mark.asyncio
    async def test_send_invoice_no_email(self, test_contact: Contact, test_invoice: Invoice):
        """Test invoice email skipped when contact has no email."""
        test_contact.email = None

        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_invoice(
                invoice=test_invoice,
                contact=test_contact,
                base_url="https://app.example.com",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_invoice_success(self, test_contact: Contact, test_invoice: Invoice):
        """Test sending invoice email."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_invoice(
                invoice=test_invoice,
                contact=test_contact,
                base_url="https://app.example.com",
                custom_message="Please review attached invoice.",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_payment_confirmation(self, test_contact: Contact, test_invoice: Invoice):
        """Test sending payment confirmation email."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_payment_confirmation(
                invoice=test_invoice,
                contact=test_contact,
                amount_paid=100.00,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_reminder_due_soon(self, test_contact: Contact, test_invoice: Invoice):
        """Test sending due soon reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_reminder_due_soon(
                invoice=test_invoice,
                contact=test_contact,
                base_url="https://app.example.com",
                days_until_due=3,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_reminder_overdue(self, test_contact: Contact, test_invoice: Invoice):
        """Test sending overdue reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_reminder_overdue(
                invoice=test_invoice,
                contact=test_contact,
                base_url="https://app.example.com",
                days_overdue=5,
            )

            assert result is True


class TestContractEmails:
    """Tests for contract-related emails."""

    @pytest.mark.asyncio
    async def test_send_contract_notification(self):
        """Test sending contract signing notification."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_contract_notification(
                to_email="client@example.com",
                contact_name="John Doe",
                contract_title="Coaching Agreement",
                signing_link="https://app.example.com/sign/abc123",
                expires_at=datetime.now() + timedelta(days=7),
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_contract_signed_confirmation(self):
        """Test sending contract signed confirmation."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_contract_signed_confirmation(
                to_email="client@example.com",
                contact_name="John Doe",
                contract_title="Coaching Agreement",
                contract_number="CON-001",
                signed_at=datetime.now(),
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_contract_reminder(self):
        """Test sending contract reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_contract_reminder(
                to_email="client@example.com",
                contact_name="John Doe",
                contract_title="Coaching Agreement",
                signing_link="https://app.example.com/sign/abc123",
            )

            assert result is True


class TestBookingEmails:
    """Tests for booking-related emails."""

    @pytest.mark.asyncio
    async def test_send_booking_confirmation(self):
        """Test sending booking confirmation."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_booking_confirmation(
                to_email="client@example.com",
                contact_name="Jane Smith",
                booking_type="Discovery Call",
                booking_date=datetime.now() + timedelta(days=3),
                booking_duration=30,
                meeting_link="https://zoom.us/j/123456",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_booking_reminder(self):
        """Test sending booking reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_booking_reminder(
                to_email="client@example.com",
                contact_name="Jane Smith",
                booking_type="Coaching Session",
                booking_date=datetime.now() + timedelta(hours=24),
                meeting_link="https://zoom.us/j/123456",
                hours_until=24,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_booking_cancelled(self):
        """Test sending booking cancellation notice."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_booking_cancelled(
                to_email="client@example.com",
                contact_name="Jane Smith",
                booking_type="Coaching Session",
                booking_date=datetime.now() + timedelta(days=1),
            )

            assert result is True


class TestOffboardingEmails:
    """Tests for offboarding-related emails."""

    @pytest.mark.asyncio
    async def test_send_offboarding_completion(self):
        """Test sending offboarding completion email."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_offboarding_completion(
                to_email="client@example.com",
                contact_name="John Doe",
                workflow_type="client",
                custom_message="It was a pleasure working with you!",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_survey_request(self):
        """Test sending survey request email."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_survey_request(
                to_email="client@example.com",
                contact_name="John Doe",
                survey_url="https://app.example.com/feedback/abc123",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_testimonial_request(self):
        """Test sending testimonial request email."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_testimonial_request(
                to_email="client@example.com",
                contact_name="John Doe",
                testimonial_url="https://app.example.com/record/xyz789",
            )

            assert result is True


class TestNoteEmails:
    """Tests for note notification emails."""

    @pytest.mark.asyncio
    async def test_send_note_to_coach_notification(self):
        """Test sending notification to coach when client sends note."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_note_to_coach_notification(
                coach_email="coach@example.com",
                client_name="Jane Client",
                note_content="Hi Coach, I wanted to share some progress with you...",
                notes_url="https://app.example.com/notes/client123",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_note_to_client_notification(self):
        """Test sending notification to client when coach sends note."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_note_to_client_notification(
                client_email="client@example.com",
                client_name="Jane Client",
                note_content="Great progress this week! Keep it up...",
                portal_url="https://app.example.com/client/notes",
            )

            assert result is True


class TestPasswordResetEmail:
    """Tests for password reset emails."""

    @pytest.mark.asyncio
    async def test_send_password_reset(self):
        """Test sending password reset email."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_password_reset(
                to_email="user@example.com",
                reset_link="https://app.example.com/reset/token123",
            )

            assert result is True


class TestWorkflowAutomationEmails:
    """Tests for workflow automation emails."""

    @pytest.mark.asyncio
    async def test_send_assessment_reminder(self, test_contact: Contact):
        """Test sending assessment reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None

            service = EmailService()
            result = await service.send_assessment_reminder(
                contact=test_contact,
                assessment_url="https://app.example.com/onboarding/token",
                day=1,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_welcome_series(self, test_contact: Contact):
        """Test sending welcome series emails."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None
            mock_settings.return_value.frontend_url = "https://app.example.com"

            service = EmailService()

            # Test day 0
            result = await service.send_welcome_series(test_contact, day=0)
            assert result is True

            # Test day 3
            result = await service.send_welcome_series(test_contact, day=3)
            assert result is True

            # Test day 7
            result = await service.send_welcome_series(test_contact, day=7)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_action_item_reminder(self, test_contact: Contact, test_action_item):
        """Test sending action item reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None
            mock_settings.return_value.frontend_url = "https://app.example.com"

            service = EmailService()
            result = await service.send_action_item_reminder(
                contact=test_contact,
                action_item=test_action_item,
                days_until=2,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_action_item_overdue(self, test_contact: Contact, test_action_item):
        """Test sending overdue action item reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None
            mock_settings.return_value.frontend_url = "https://app.example.com"

            service = EmailService()
            result = await service.send_action_item_overdue(
                contact=test_contact,
                action_item=test_action_item,
                days_overdue=3,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_goal_reminder(self, test_contact: Contact, test_goal):
        """Test sending goal reminder."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None
            mock_settings.return_value.frontend_url = "https://app.example.com"

            service = EmailService()
            result = await service.send_goal_reminder(
                contact=test_contact,
                goal=test_goal,
                days_until=7,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_weekly_summary(self, test_contact: Contact):
        """Test sending weekly summary."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None
            mock_settings.return_value.frontend_url = "https://app.example.com"

            service = EmailService()
            summary = {
                "completed_this_week": 3,
                "pending_action_items": 2,
                "overdue_items": 1,
                "active_goals": 2,
            }
            result = await service.send_weekly_summary(
                contact=test_contact,
                summary=summary,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_monthly_summary(self, test_contact: Contact):
        """Test sending monthly summary."""
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value.gmail_email = None
            mock_settings.return_value.gmail_app_password = None
            mock_settings.return_value.frontend_url = "https://app.example.com"

            service = EmailService()
            summary = {
                "sessions_this_month": 4,
                "action_items_completed": 12,
                "goals_completed": 1,
                "active_goals": 3,
            }
            result = await service.send_monthly_summary(
                contact=test_contact,
                summary=summary,
            )

            assert result is True
