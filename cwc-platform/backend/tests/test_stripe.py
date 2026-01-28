"""
Tests for Stripe payment integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
import uuid

from httpx import AsyncClient

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.contact import Contact


class TestStripeConfig:
    """Tests for Stripe configuration endpoint."""

    @pytest.mark.asyncio
    async def test_get_stripe_config_unconfigured(self, client: AsyncClient):
        """Test getting Stripe config when not configured."""
        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.get_public_key.return_value = None
            mock_service.is_configured.return_value = False

            response = await client.get("/api/stripe/config")
            assert response.status_code == 200
            data = response.json()
            assert data["is_configured"] is False
            assert data["public_key"] is None

    @pytest.mark.asyncio
    async def test_get_stripe_config_configured(self, client: AsyncClient):
        """Test getting Stripe config when configured."""
        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.get_public_key.return_value = "pk_test_1234567890"
            mock_service.is_configured.return_value = True

            response = await client.get("/api/stripe/config")
            assert response.status_code == 200
            data = response.json()
            assert data["is_configured"] is True
            assert data["public_key"] == "pk_test_1234567890"


class TestStripeCheckout:
    """Tests for Stripe checkout session creation."""

    @pytest.mark.asyncio
    async def test_create_checkout_stripe_not_configured(
        self, client: AsyncClient, test_invoice: Invoice
    ):
        """Test checkout fails when Stripe not configured."""
        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = False

            response = await client.post(
                "/api/stripe/checkout",
                json={"invoice_id": test_invoice.id}
            )
            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_checkout_no_invoice_or_token(self, client: AsyncClient):
        """Test checkout fails without invoice_id or view_token."""
        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = True

            response = await client.post(
                "/api/stripe/checkout",
                json={}
            )
            assert response.status_code == 400
            assert "required" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_checkout_invoice_not_found(self, client: AsyncClient):
        """Test checkout fails with non-existent invoice."""
        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = True

            response = await client.post(
                "/api/stripe/checkout",
                json={"invoice_id": str(uuid.uuid4())}
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_checkout_invoice_already_paid(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test checkout fails for already paid invoice."""
        # Create a paid invoice
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-PAID-001",
            status="paid",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 100.0}],
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            amount_paid=Decimal("100.00"),
            balance_due=Decimal("0.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        await db_session.commit()

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = True

            response = await client.post(
                "/api/stripe/checkout",
                json={"invoice_id": invoice.id}
            )
            assert response.status_code == 400
            assert "already paid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_checkout_invoice_cancelled(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test checkout fails for cancelled invoice."""
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-CANCEL-001",
            status="cancelled",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 100.0}],
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        await db_session.commit()

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = True

            response = await client.post(
                "/api/stripe/checkout",
                json={"invoice_id": invoice.id}
            )
            assert response.status_code == 400
            assert "cancelled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_checkout_success(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test successful checkout session creation."""
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-CHECKOUT-001",
            status="sent",
            line_items=[{"description": "Coaching Session", "quantity": 1, "unit_price": 200.0}],
            subtotal=Decimal("200.00"),
            total=Decimal("200.00"),
            balance_due=Decimal("200.00"),
            due_date=datetime.utcnow().date(),
            view_token="test-view-token-123",
        )
        db_session.add(invoice)
        await db_session.commit()
        await db_session.refresh(invoice)

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.create_checkout_session.return_value = {
                "session_id": "cs_test_session_id",
                "url": "https://checkout.stripe.com/pay/cs_test_session_id"
            }

            response = await client.post(
                "/api/stripe/checkout",
                json={"invoice_id": invoice.id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "cs_test_session_id"
            assert "stripe.com" in data["url"]

    @pytest.mark.asyncio
    async def test_create_checkout_with_view_token(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test checkout with view_token instead of invoice_id."""
        view_token = "public-view-token-456"
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-TOKEN-001",
            status="sent",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 150.0}],
            subtotal=Decimal("150.00"),
            total=Decimal("150.00"),
            balance_due=Decimal("150.00"),
            due_date=datetime.utcnow().date(),
            view_token=view_token,
        )
        db_session.add(invoice)
        await db_session.commit()

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.create_checkout_session.return_value = {
                "session_id": "cs_test_token_session",
                "url": "https://checkout.stripe.com/pay/cs_test_token_session"
            }

            response = await client.post(
                "/api/stripe/checkout",
                json={"view_token": view_token}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "cs_test_token_session"


class TestStripeWebhook:
    """Tests for Stripe webhook handling."""

    @pytest.mark.asyncio
    async def test_webhook_missing_signature(self, client: AsyncClient):
        """Test webhook fails without signature header."""
        response = await client.post(
            "/api/stripe/webhook",
            content=b'{"type": "test"}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self, client: AsyncClient):
        """Test webhook fails with invalid signature."""
        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.side_effect = ValueError("Invalid signature")

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{"type": "test"}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "invalid_signature"
                }
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_checkout_completed(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test handling checkout.session.completed webhook."""
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-WEBHOOK-001",
            status="sent",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 100.0}],
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            balance_due=Decimal("100.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        await db_session.commit()

        webhook_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "metadata": {"invoice_id": invoice.id},
                    "amount_total": 10000,  # $100 in cents
                    "payment_intent": "pi_test_123",
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_webhook_payment_intent_succeeded(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test handling payment_intent.succeeded webhook."""
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-PI-001",
            status="sent",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 200.0}],
            subtotal=Decimal("200.00"),
            total=Decimal("200.00"),
            balance_due=Decimal("200.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        await db_session.commit()

        webhook_event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_456",
                    "metadata": {"invoice_id": invoice.id},
                    "amount_received": 20000,  # $200 in cents
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_payment_failed(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test handling payment_intent.payment_failed webhook."""
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-FAIL-001",
            status="sent",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 100.0}],
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            balance_due=Decimal("100.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        await db_session.commit()

        webhook_event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_fail_789",
                    "metadata": {"invoice_id": invoice.id},
                    "amount": 10000,
                    "last_payment_error": {"message": "Card declined"}
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_refund(
        self, db_session, client: AsyncClient, test_contact: Contact
    ):
        """Test handling charge.refunded webhook."""
        # Create invoice and payment
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-REFUND-001",
            status="paid",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 100.0}],
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            amount_paid=Decimal("100.00"),
            balance_due=Decimal("0.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        await db_session.flush()

        payment = Payment(
            id=str(uuid.uuid4()),
            invoice_id=invoice.id,
            amount=Decimal("100.00"),
            payment_method="stripe",
            transaction_id="pi_test_refund_123",
            status="completed",
        )
        db_session.add(payment)
        await db_session.commit()

        webhook_event = {
            "type": "charge.refunded",
            "data": {
                "object": {
                    "id": "ch_test_refund",
                    "payment_intent": "pi_test_refund_123",
                    "amount_refunded": 5000,  # $50 partial refund
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_subscription_created(self, client: AsyncClient):
        """Test handling customer.subscription.created webhook."""
        webhook_event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_456",
                    "status": "active",
                    "current_period_start": 1700000000,
                    "current_period_end": 1702592000,
                    "cancel_at_period_end": False,
                    "items": {
                        "data": [{
                            "price": {"id": "price_test_789"}
                        }]
                    }
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_subscription_updated(self, client: AsyncClient):
        """Test handling customer.subscription.updated webhook."""
        webhook_event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_update_123",
                    "status": "past_due",
                    "current_period_start": 1700000000,
                    "current_period_end": 1702592000,
                    "cancel_at_period_end": False,
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_subscription_deleted(self, client: AsyncClient):
        """Test handling customer.subscription.deleted webhook."""
        webhook_event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_delete_123",
                }
            }
        }

        with patch("app.routers.stripe.stripe_service") as mock_service:
            mock_service.verify_webhook_signature.return_value = webhook_event

            response = await client.post(
                "/api/stripe/webhook",
                content=b'{}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "valid_signature"
                }
            )
            assert response.status_code == 200


class TestStripeService:
    """Unit tests for StripeService class."""

    def test_service_not_configured(self):
        """Test service reports not configured without API key."""
        with patch.dict("os.environ", {}, clear=True):
            from app.services.stripe_service import StripeService
            service = StripeService()
            assert service.is_configured() is False

    def test_service_configured(self):
        """Test service reports configured with API key."""
        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123"}):
            from app.services.stripe_service import StripeService
            service = StripeService()
            assert service.is_configured() is True

    def test_create_checkout_session_not_configured(self):
        """Test checkout fails when not configured."""
        from app.services.stripe_service import StripeService
        service = StripeService()
        service.api_key = None

        mock_invoice = Mock()
        mock_invoice.id = "inv_123"

        with pytest.raises(ValueError, match="not configured"):
            service.create_checkout_session(
                invoice=mock_invoice,
                success_url="http://test.com/success",
                cancel_url="http://test.com/cancel"
            )

    def test_verify_webhook_no_secret(self):
        """Test webhook verification fails without secret."""
        from app.services.stripe_service import StripeService
        service = StripeService()
        service.webhook_secret = None

        with pytest.raises(ValueError, match="not configured"):
            service.verify_webhook_signature(b"payload", "signature")
