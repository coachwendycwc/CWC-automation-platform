"""
Tests for Subscriptions endpoints.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import uuid

from httpx import AsyncClient
from sqlalchemy import select

from app.models.contact import Contact
from app.models.stripe_customer import StripeCustomer
from app.models.stripe_product import StripeProduct
from app.models.stripe_price import StripePrice
from app.models.subscription import Subscription


@pytest.fixture
async def test_stripe_product(db_session) -> StripeProduct:
    """Create a test Stripe product."""
    product = StripeProduct(
        id=str(uuid.uuid4()),
        name="Test Coaching Package",
        description="Monthly coaching sessions",
        stripe_product_id="prod_test123",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def test_stripe_price(db_session, test_stripe_product: StripeProduct) -> StripePrice:
    """Create a test Stripe price."""
    price = StripePrice(
        id=str(uuid.uuid4()),
        product_id=test_stripe_product.id,
        stripe_price_id="price_test123",
        amount=299.00,
        currency="usd",
        interval="monthly",
        interval_count=1,
        is_active=True,
    )
    db_session.add(price)
    await db_session.commit()
    await db_session.refresh(price)
    return price


@pytest.fixture
async def test_stripe_customer(db_session, test_contact: Contact) -> StripeCustomer:
    """Create a test Stripe customer."""
    customer = StripeCustomer(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        stripe_customer_id="cus_test123",
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest.fixture
async def test_subscription(
    db_session,
    test_contact: Contact,
    test_stripe_customer: StripeCustomer,
    test_stripe_price: StripePrice,
) -> Subscription:
    """Create a test subscription."""
    subscription = Subscription(
        id=str(uuid.uuid4()),
        contact_id=test_contact.id,
        stripe_customer_id=test_stripe_customer.id,
        stripe_price_id=test_stripe_price.id,
        stripe_subscription_id="sub_test123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


class TestListProducts:
    """Tests for listing products."""

    @pytest.mark.asyncio
    async def test_list_products_empty(self, auth_client: AsyncClient):
        """Test listing products when none exist."""
        response = await auth_client.get("/api/subscriptions/products")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_products_with_data(
        self, auth_client: AsyncClient, test_stripe_product: StripeProduct
    ):
        """Test listing products with existing data."""
        response = await auth_client.get("/api/subscriptions/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["name"] == "Test Coaching Package" for p in data)

    @pytest.mark.asyncio
    async def test_list_inactive_products(
        self, db_session, auth_client: AsyncClient, test_stripe_product: StripeProduct
    ):
        """Test listing includes inactive products when specified."""
        test_stripe_product.is_active = False
        await db_session.commit()

        response = await auth_client.get(
            "/api/subscriptions/products",
            params={"active_only": False},
        )
        assert response.status_code == 200


class TestCreateProduct:
    """Tests for creating products."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.create_product")
    async def test_create_product_success(
        self, mock_create, mock_is_configured, auth_client: AsyncClient
    ):
        """Test successful product creation."""
        mock_is_configured.return_value = True
        mock_create.return_value = {"id": "prod_new123"}

        response = await auth_client.post(
            "/api/subscriptions/products",
            json={
                "name": "New Product",
                "description": "A new coaching product",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Product"

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    async def test_create_product_stripe_not_configured(
        self, mock_is_configured, auth_client: AsyncClient
    ):
        """Test product creation when Stripe not configured."""
        mock_is_configured.return_value = False

        response = await auth_client.post(
            "/api/subscriptions/products",
            json={
                "name": "New Product",
                "description": "A new coaching product",
            },
        )
        assert response.status_code == 503


class TestUpdateProduct:
    """Tests for updating products."""

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, auth_client: AsyncClient):
        """Test updating non-existent product."""
        response = await auth_client.put(
            f"/api/subscriptions/products/{uuid.uuid4()}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404


class TestProductPrices:
    """Tests for product prices."""

    @pytest.mark.asyncio
    async def test_list_product_prices(
        self, auth_client: AsyncClient, test_stripe_product: StripeProduct, test_stripe_price: StripePrice
    ):
        """Test listing prices for a product."""
        response = await auth_client.get(
            f"/api/subscriptions/products/{test_stripe_product.id}/prices"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.create_price")
    async def test_create_price_success(
        self, mock_create, mock_is_configured, auth_client: AsyncClient, test_stripe_product: StripeProduct
    ):
        """Test successful price creation."""
        mock_is_configured.return_value = True
        mock_create.return_value = {"id": "price_new123"}

        response = await auth_client.post(
            f"/api/subscriptions/products/{test_stripe_product.id}/prices",
            json={
                "amount": 199.00,
                "currency": "usd",
                "interval": "monthly",
                "interval_count": 1,
            },
        )
        assert response.status_code == 200


class TestCustomers:
    """Tests for customer management."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.create_customer")
    async def test_create_customer_success(
        self, mock_create, mock_is_configured, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test successful customer creation."""
        mock_is_configured.return_value = True
        mock_create.return_value = {"id": "cus_new123"}

        response = await auth_client.post(
            "/api/subscriptions/customers",
            json={"contact_id": test_contact.id},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    async def test_create_customer_returns_existing(
        self, mock_is_configured, auth_client: AsyncClient, test_stripe_customer: StripeCustomer
    ):
        """Test creating customer returns existing one."""
        mock_is_configured.return_value = True

        response = await auth_client.post(
            "/api/subscriptions/customers",
            json={"contact_id": test_stripe_customer.contact_id},
        )
        assert response.status_code == 200
        assert response.json()["id"] == test_stripe_customer.id

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    async def test_create_customer_contact_not_found(
        self, mock_is_configured, auth_client: AsyncClient
    ):
        """Test creating customer for non-existent contact."""
        mock_is_configured.return_value = True

        response = await auth_client.post(
            "/api/subscriptions/customers",
            json={"contact_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404


class TestSetupIntent:
    """Tests for setup intents."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.create_setup_intent")
    async def test_create_setup_intent_success(
        self, mock_create, mock_is_configured, auth_client: AsyncClient, test_stripe_customer: StripeCustomer
    ):
        """Test successful setup intent creation."""
        mock_is_configured.return_value = True
        mock_create.return_value = {
            "id": "seti_test123",
            "client_secret": "seti_secret",
            "status": "requires_payment_method",
        }

        response = await auth_client.post(
            f"/api/subscriptions/customers/{test_stripe_customer.id}/setup-intent"
        )
        assert response.status_code == 200
        data = response.json()
        assert "client_secret" in data

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    async def test_create_setup_intent_customer_not_found(
        self, mock_is_configured, auth_client: AsyncClient
    ):
        """Test setup intent for non-existent customer."""
        mock_is_configured.return_value = True

        response = await auth_client.post(
            f"/api/subscriptions/customers/{uuid.uuid4()}/setup-intent"
        )
        assert response.status_code == 404


class TestPaymentMethods:
    """Tests for payment methods."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.list_payment_methods")
    async def test_list_payment_methods_success(
        self, mock_list, mock_is_configured, auth_client: AsyncClient, test_stripe_customer: StripeCustomer
    ):
        """Test listing payment methods."""
        mock_is_configured.return_value = True
        mock_list.return_value = [
            {
                "id": "pm_test123",
                "type": "card",
                "card": {
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 12,
                    "exp_year": 2025,
                },
            }
        ]

        response = await auth_client.get(
            f"/api/subscriptions/customers/{test_stripe_customer.id}/payment-methods"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["card"]["last4"] == "4242"


class TestListSubscriptions:
    """Tests for listing subscriptions."""

    @pytest.mark.asyncio
    async def test_list_subscriptions_empty(self, auth_client: AsyncClient):
        """Test listing subscriptions when none exist."""
        response = await auth_client.get("/api/subscriptions")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_subscriptions_with_data(
        self, auth_client: AsyncClient, test_subscription: Subscription
    ):
        """Test listing subscriptions with existing data."""
        response = await auth_client.get("/api/subscriptions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_subscriptions_filter_by_status(
        self, auth_client: AsyncClient, test_subscription: Subscription
    ):
        """Test filtering subscriptions by status."""
        response = await auth_client.get(
            "/api/subscriptions",
            params={"status": "active"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_subscriptions_filter_by_contact(
        self, auth_client: AsyncClient, test_subscription: Subscription, test_contact: Contact
    ):
        """Test filtering subscriptions by contact."""
        response = await auth_client.get(
            "/api/subscriptions",
            params={"contact_id": test_contact.id},
        )
        assert response.status_code == 200


class TestCreateSubscription:
    """Tests for creating subscriptions."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.create_subscription")
    @patch("app.services.stripe_service.stripe_service.create_customer")
    async def test_create_subscription_success(
        self,
        mock_create_customer,
        mock_create_sub,
        mock_is_configured,
        auth_client: AsyncClient,
        test_contact: Contact,
        test_stripe_price: StripePrice,
    ):
        """Test successful subscription creation."""
        mock_is_configured.return_value = True
        mock_create_customer.return_value = {"id": "cus_new123"}
        mock_create_sub.return_value = {
            "id": "sub_new123",
            "status": "active",
            "current_period_start": int(datetime.utcnow().timestamp()),
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            "cancel_at_period_end": False,
        }

        response = await auth_client.post(
            "/api/subscriptions",
            json={
                "contact_id": test_contact.id,
                "price_id": test_stripe_price.id,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    async def test_create_subscription_price_not_found(
        self, mock_is_configured, auth_client: AsyncClient, test_contact: Contact
    ):
        """Test subscription creation with invalid price."""
        mock_is_configured.return_value = True

        response = await auth_client.post(
            "/api/subscriptions",
            json={
                "contact_id": test_contact.id,
                "price_id": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 404


class TestSubscriptionStats:
    """Tests for subscription statistics."""

    @pytest.mark.asyncio
    async def test_get_subscription_stats(self, auth_client: AsyncClient):
        """Test getting subscription stats."""
        response = await auth_client.get("/api/subscriptions/stats")
        assert response.status_code == 200
        data = response.json()
        assert "active_count" in data
        assert "monthly_recurring_revenue" in data
        assert "annual_recurring_revenue" in data


class TestGetSubscription:
    """Tests for getting subscription details."""

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, auth_client: AsyncClient):
        """Test getting non-existent subscription."""
        response = await auth_client.get(f"/api/subscriptions/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.list_subscription_invoices")
    @patch("app.services.stripe_service.stripe_service.list_payment_methods")
    async def test_get_subscription_success(
        self,
        mock_methods,
        mock_invoices,
        mock_is_configured,
        auth_client: AsyncClient,
        test_subscription: Subscription,
    ):
        """Test getting subscription details."""
        mock_is_configured.return_value = True
        mock_invoices.return_value = []
        mock_methods.return_value = []

        response = await auth_client.get(f"/api/subscriptions/{test_subscription.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_subscription.id


class TestCancelSubscription:
    """Tests for cancelling subscriptions."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    async def test_cancel_subscription_not_found(
        self, mock_is_configured, auth_client: AsyncClient
    ):
        """Test cancelling non-existent subscription."""
        mock_is_configured.return_value = True

        response = await auth_client.post(f"/api/subscriptions/{uuid.uuid4()}/cancel")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.cancel_subscription")
    async def test_cancel_subscription_at_period_end(
        self, mock_cancel, mock_is_configured, auth_client: AsyncClient, test_subscription: Subscription
    ):
        """Test cancelling subscription at period end."""
        mock_is_configured.return_value = True
        mock_cancel.return_value = None

        response = await auth_client.post(
            f"/api/subscriptions/{test_subscription.id}/cancel",
            params={"at_period_end": True},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.cancel_subscription")
    async def test_cancel_subscription_immediately(
        self, mock_cancel, mock_is_configured, auth_client: AsyncClient, test_subscription: Subscription
    ):
        """Test cancelling subscription immediately."""
        mock_is_configured.return_value = True
        mock_cancel.return_value = None

        response = await auth_client.post(
            f"/api/subscriptions/{test_subscription.id}/cancel",
            params={"at_period_end": False},
        )
        assert response.status_code == 200


class TestPauseResumeSubscription:
    """Tests for pausing and resuming subscriptions."""

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.pause_subscription")
    async def test_pause_subscription(
        self, mock_pause, mock_is_configured, auth_client: AsyncClient, test_subscription: Subscription
    ):
        """Test pausing a subscription."""
        mock_is_configured.return_value = True
        mock_pause.return_value = None

        response = await auth_client.post(f"/api/subscriptions/{test_subscription.id}/pause")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("app.services.stripe_service.stripe_service.is_configured")
    @patch("app.services.stripe_service.stripe_service.resume_subscription")
    async def test_resume_subscription(
        self, mock_resume, mock_is_configured, db_session, auth_client: AsyncClient, test_subscription: Subscription
    ):
        """Test resuming a subscription."""
        mock_is_configured.return_value = True
        mock_resume.return_value = None

        test_subscription.status = "paused"
        await db_session.commit()

        response = await auth_client.post(f"/api/subscriptions/{test_subscription.id}/resume")
        assert response.status_code == 200
