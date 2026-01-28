"""
Stripe payment integration service.
Handles checkout sessions, webhooks, and payment processing.
"""
import os
import logging
from decimal import Decimal
from typing import Optional

import stripe

from app.models.invoice import Invoice

logger = logging.getLogger(__name__)


class StripeService:
    """Service for Stripe payment integration."""

    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.public_key = os.getenv("STRIPE_PUBLIC_KEY")

        if self.api_key:
            stripe.api_key = self.api_key
            logger.info("Stripe service initialized")
        else:
            logger.warning("Stripe not configured. Set STRIPE_SECRET_KEY.")

    def is_configured(self) -> bool:
        """Check if Stripe is configured."""
        return bool(self.api_key)

    def get_public_key(self) -> Optional[str]:
        """Get the Stripe publishable key for frontend."""
        return self.public_key

    def create_checkout_session(
        self,
        invoice: Invoice,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
    ) -> dict:
        """
        Create a Stripe Checkout session for an invoice.

        Args:
            invoice: The invoice to pay
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            customer_email: Optional customer email for Stripe

        Returns:
            Checkout session data including URL
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        # Check if this is a partial payment (previous payments made)
        if invoice.amount_paid and invoice.amount_paid > 0:
            # Partial payment - just charge the balance due
            line_items = [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(invoice.balance_due * 100),  # Stripe uses cents
                    "product_data": {
                        "name": f"Invoice {invoice.invoice_number} - Remaining Balance",
                    },
                },
                "quantity": 1,
            }]
            discounts = []
        else:
            # Full payment - include all line items
            line_items = []
            for item in invoice.line_items:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(Decimal(str(item["unit_price"])) * 100),  # Stripe uses cents
                        "product_data": {
                            "name": item["description"],
                        },
                    },
                    "quantity": int(item["quantity"]),
                })

            # Add tax if applicable
            if invoice.tax_amount and invoice.tax_amount > 0:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(invoice.tax_amount * 100),
                        "product_data": {
                            "name": f"Tax ({invoice.tax_rate}%)",
                        },
                    },
                    "quantity": 1,
                })

            # Apply discount if applicable
            discounts = []
            if invoice.discount_amount and invoice.discount_amount > 0:
                # Create a coupon for the discount
                coupon = stripe.Coupon.create(
                    amount_off=int(invoice.discount_amount * 100),
                    currency="usd",
                    duration="once",
                    name=f"Discount for Invoice #{invoice.invoice_number}",
                )
                discounts.append({"coupon": coupon.id})

        # Create checkout session
        session_params = {
            "payment_method_types": ["card"],
            "line_items": line_items,
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
            },
            "payment_intent_data": {
                "metadata": {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                },
            },
        }

        if customer_email:
            session_params["customer_email"] = customer_email

        if discounts:
            session_params["discounts"] = discounts

        session = stripe.checkout.Session.create(**session_params)

        logger.info(f"Created Stripe checkout session for invoice {invoice.invoice_number}")

        return {
            "session_id": session.id,
            "url": session.url,
            "payment_intent": session.payment_intent,
        }

    def create_payment_link(
        self,
        invoice: Invoice,
    ) -> dict:
        """
        Create a reusable Stripe Payment Link for an invoice.

        Args:
            invoice: The invoice to create payment link for

        Returns:
            Payment link data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        # Create a product for the invoice
        product = stripe.Product.create(
            name=f"Invoice #{invoice.invoice_number}",
            metadata={
                "invoice_id": invoice.id,
            },
        )

        # Create a price for the product
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(invoice.balance_due * 100),
            currency="usd",
        )

        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata={
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
            },
            after_completion={
                "type": "redirect",
                "redirect": {
                    "url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3001')}/pay/{invoice.view_token}/success",
                },
            },
        )

        logger.info(f"Created Stripe payment link for invoice {invoice.invoice_number}")

        return {
            "payment_link_id": payment_link.id,
            "url": payment_link.url,
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """
        Verify and parse a Stripe webhook event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header value

        Returns:
            Parsed event data
        """
        if not self.webhook_secret:
            raise ValueError("Stripe webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError("Invalid webhook signature")

    def retrieve_payment_intent(self, payment_intent_id: str) -> dict:
        """Retrieve a payment intent by ID."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        return stripe.PaymentIntent.retrieve(payment_intent_id)

    def retrieve_checkout_session(self, session_id: str) -> dict:
        """Retrieve a checkout session by ID."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        return stripe.checkout.Session.retrieve(session_id)

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> dict:
        """
        Create a refund for a payment.

        Args:
            payment_intent_id: The payment intent to refund
            amount: Optional amount in cents (full refund if not specified)
            reason: Optional reason for refund

        Returns:
            Refund data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        refund_params = {"payment_intent": payment_intent_id}

        if amount:
            refund_params["amount"] = amount

        if reason:
            refund_params["reason"] = reason

        refund = stripe.Refund.create(**refund_params)

        logger.info(f"Created refund for payment intent {payment_intent_id}")

        return {
            "refund_id": refund.id,
            "amount": refund.amount,
            "status": refund.status,
        }

    # ==================== Customer Management ====================

    def create_customer(
        self,
        email: str,
        name: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Create a Stripe Customer object.

        Args:
            email: Customer email address
            name: Customer full name
            metadata: Optional metadata (e.g., contact_id)

        Returns:
            Customer data including stripe customer ID
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        customer_params = {
            "email": email,
            "name": name,
        }

        if metadata:
            customer_params["metadata"] = metadata

        customer = stripe.Customer.create(**customer_params)

        logger.info(f"Created Stripe customer {customer.id} for {email}")

        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
        }

    def get_customer(self, customer_id: str) -> dict:
        """Retrieve a Stripe customer by ID."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        customer = stripe.Customer.retrieve(customer_id)
        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "default_source": customer.default_source,
            "invoice_settings": customer.invoice_settings,
        }

    def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Update a Stripe customer."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        update_params = {}
        if email:
            update_params["email"] = email
        if name:
            update_params["name"] = name
        if metadata:
            update_params["metadata"] = metadata

        customer = stripe.Customer.modify(customer_id, **update_params)

        logger.info(f"Updated Stripe customer {customer_id}")

        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
        }

    def create_setup_intent(self, customer_id: str) -> dict:
        """
        Create a SetupIntent for collecting payment method without charging.

        Args:
            customer_id: Stripe customer ID

        Returns:
            SetupIntent data including client_secret for frontend
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        setup_intent = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=["card"],
        )

        logger.info(f"Created SetupIntent for customer {customer_id}")

        return {
            "setup_intent_id": setup_intent.id,
            "client_secret": setup_intent.client_secret,
            "status": setup_intent.status,
        }

    def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str,
        set_default: bool = True,
    ) -> dict:
        """
        Attach a payment method to a customer.

        Args:
            customer_id: Stripe customer ID
            payment_method_id: Payment method ID (pm_xxx)
            set_default: Whether to set as default payment method

        Returns:
            Payment method data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        # Attach payment method to customer
        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )

        # Set as default if requested
        if set_default:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

        logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")

        return {
            "payment_method_id": payment_method.id,
            "type": payment_method.type,
            "card": {
                "brand": payment_method.card.brand,
                "last4": payment_method.card.last4,
                "exp_month": payment_method.card.exp_month,
                "exp_year": payment_method.card.exp_year,
            } if payment_method.card else None,
        }

    def list_payment_methods(self, customer_id: str) -> list:
        """List all payment methods for a customer."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card",
        )

        return [
            {
                "payment_method_id": pm.id,
                "type": pm.type,
                "card": {
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year,
                } if pm.card else None,
            }
            for pm in payment_methods.data
        ]

    def detach_payment_method(self, payment_method_id: str) -> dict:
        """Detach a payment method from its customer."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        payment_method = stripe.PaymentMethod.detach(payment_method_id)

        logger.info(f"Detached payment method {payment_method_id}")

        return {"payment_method_id": payment_method.id, "detached": True}

    # ==================== Product & Price Management ====================

    def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Create a Stripe Product for subscription services.

        Args:
            name: Product name
            description: Product description
            metadata: Optional metadata

        Returns:
            Product data including stripe product ID
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        product_params = {
            "name": name,
            "type": "service",
        }

        if description:
            product_params["description"] = description
        if metadata:
            product_params["metadata"] = metadata

        product = stripe.Product.create(**product_params)

        logger.info(f"Created Stripe product {product.id}: {name}")

        return {
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "active": product.active,
        }

    def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> dict:
        """Update a Stripe product."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        update_params = {}
        if name:
            update_params["name"] = name
        if description is not None:
            update_params["description"] = description
        if active is not None:
            update_params["active"] = active

        product = stripe.Product.modify(product_id, **update_params)

        logger.info(f"Updated Stripe product {product_id}")

        return {
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "active": product.active,
        }

    def create_price(
        self,
        product_id: str,
        amount: int,
        currency: str = "usd",
        interval: str = "month",
        interval_count: int = 1,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Create a recurring Stripe Price for a product.

        Args:
            product_id: Stripe product ID
            amount: Amount in cents
            currency: Currency code (e.g., 'usd')
            interval: Billing interval: 'day', 'week', 'month', 'year'
            interval_count: Number of intervals between billings
            metadata: Optional metadata

        Returns:
            Price data including stripe price ID
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        price_params = {
            "product": product_id,
            "unit_amount": amount,
            "currency": currency,
            "recurring": {
                "interval": interval,
                "interval_count": interval_count,
            },
        }

        if metadata:
            price_params["metadata"] = metadata

        price = stripe.Price.create(**price_params)

        logger.info(f"Created Stripe price {price.id} for product {product_id}")

        return {
            "price_id": price.id,
            "product_id": price.product,
            "unit_amount": price.unit_amount,
            "currency": price.currency,
            "interval": price.recurring.interval if price.recurring else None,
            "interval_count": price.recurring.interval_count if price.recurring else None,
            "active": price.active,
        }

    def list_prices(
        self,
        product_id: Optional[str] = None,
        active: bool = True,
    ) -> list:
        """List prices, optionally filtered by product."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        params = {"active": active}
        if product_id:
            params["product"] = product_id

        prices = stripe.Price.list(**params)

        return [
            {
                "price_id": p.id,
                "product_id": p.product,
                "unit_amount": p.unit_amount,
                "currency": p.currency,
                "interval": p.recurring.interval if p.recurring else None,
                "interval_count": p.recurring.interval_count if p.recurring else None,
                "active": p.active,
            }
            for p in prices.data
        ]

    def deactivate_price(self, price_id: str) -> dict:
        """Deactivate a price (cannot delete prices in Stripe)."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        price = stripe.Price.modify(price_id, active=False)

        logger.info(f"Deactivated Stripe price {price_id}")

        return {"price_id": price.id, "active": price.active}

    # ==================== Subscription Management ====================

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None,
        metadata: Optional[dict] = None,
        default_payment_method: Optional[str] = None,
    ) -> dict:
        """
        Create a new subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Optional trial period in days
            metadata: Optional metadata (e.g., contact_id, subscription_id)
            default_payment_method: Optional payment method to use

        Returns:
            Subscription data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        sub_params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "default_incomplete",
            "payment_settings": {
                "save_default_payment_method": "on_subscription",
            },
            "expand": ["latest_invoice.payment_intent"],
        }

        if trial_days:
            sub_params["trial_period_days"] = trial_days

        if metadata:
            sub_params["metadata"] = metadata

        if default_payment_method:
            sub_params["default_payment_method"] = default_payment_method

        subscription = stripe.Subscription.create(**sub_params)

        logger.info(f"Created Stripe subscription {subscription.id} for customer {customer_id}")

        return self._format_subscription(subscription)

    def get_subscription(self, subscription_id: str) -> dict:
        """Retrieve a subscription by ID."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        subscription = stripe.Subscription.retrieve(
            subscription_id,
            expand=["latest_invoice.payment_intent", "default_payment_method"],
        )

        return self._format_subscription(subscription)

    def update_subscription(
        self,
        subscription_id: str,
        price_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        proration_behavior: str = "create_prorations",
    ) -> dict:
        """
        Update a subscription (e.g., change plan).

        Args:
            subscription_id: Stripe subscription ID
            price_id: New price ID (to change plan)
            metadata: Updated metadata
            proration_behavior: How to handle prorations

        Returns:
            Updated subscription data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        update_params = {}

        if price_id:
            # Get current subscription to find item ID
            sub = stripe.Subscription.retrieve(subscription_id)
            item_id = sub["items"]["data"][0]["id"]
            update_params["items"] = [{"id": item_id, "price": price_id}]
            update_params["proration_behavior"] = proration_behavior

        if metadata:
            update_params["metadata"] = metadata

        subscription = stripe.Subscription.modify(subscription_id, **update_params)

        logger.info(f"Updated Stripe subscription {subscription_id}")

        return self._format_subscription(subscription)

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> dict:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period

        Returns:
            Cancelled subscription data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
        else:
            subscription = stripe.Subscription.cancel(subscription_id)

        logger.info(f"Cancelled Stripe subscription {subscription_id} (at_period_end={at_period_end})")

        return self._format_subscription(subscription)

    def pause_subscription(self, subscription_id: str) -> dict:
        """
        Pause collection on a subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Paused subscription data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        subscription = stripe.Subscription.modify(
            subscription_id,
            pause_collection={"behavior": "mark_uncollectible"},
        )

        logger.info(f"Paused Stripe subscription {subscription_id}")

        return self._format_subscription(subscription)

    def resume_subscription(self, subscription_id: str) -> dict:
        """
        Resume a paused subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Resumed subscription data
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        subscription = stripe.Subscription.modify(
            subscription_id,
            pause_collection="",  # Empty string to resume
        )

        logger.info(f"Resumed Stripe subscription {subscription_id}")

        return self._format_subscription(subscription)

    def list_subscriptions(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        List subscriptions, optionally filtered.

        Args:
            customer_id: Filter by customer
            status: Filter by status (active, past_due, canceled, etc.)
            limit: Maximum results

        Returns:
            List of subscriptions
        """
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        if status:
            params["status"] = status

        subscriptions = stripe.Subscription.list(**params)

        return [self._format_subscription(sub) for sub in subscriptions.data]

    def _format_subscription(self, subscription) -> dict:
        """Format a Stripe subscription object for our API."""
        from datetime import datetime

        result = {
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
            "trial_start": datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
            "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
            "metadata": subscription.metadata,
        }

        # Add price info
        if subscription.items and subscription.items.data:
            item = subscription.items.data[0]
            result["price_id"] = item.price.id
            result["product_id"] = item.price.product
            result["unit_amount"] = item.price.unit_amount
            result["interval"] = item.price.recurring.interval if item.price.recurring else None

        # Add latest invoice info if expanded
        if hasattr(subscription, "latest_invoice") and subscription.latest_invoice:
            invoice = subscription.latest_invoice
            if isinstance(invoice, str):
                result["latest_invoice_id"] = invoice
            else:
                result["latest_invoice_id"] = invoice.id
                result["latest_invoice_status"] = invoice.status
                if hasattr(invoice, "payment_intent") and invoice.payment_intent:
                    pi = invoice.payment_intent
                    if isinstance(pi, str):
                        result["payment_intent_id"] = pi
                    else:
                        result["payment_intent_id"] = pi.id
                        result["payment_intent_status"] = pi.status
                        result["client_secret"] = pi.client_secret

        return result

    # ==================== Stripe Invoice Management ====================

    def get_stripe_invoice(self, invoice_id: str) -> dict:
        """Retrieve a Stripe invoice by ID."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        invoice = stripe.Invoice.retrieve(invoice_id)

        return {
            "invoice_id": invoice.id,
            "customer_id": invoice.customer,
            "subscription_id": invoice.subscription,
            "status": invoice.status,
            "amount_due": invoice.amount_due,
            "amount_paid": invoice.amount_paid,
            "currency": invoice.currency,
            "hosted_invoice_url": invoice.hosted_invoice_url,
            "invoice_pdf": invoice.invoice_pdf,
        }

    def list_subscription_invoices(
        self,
        subscription_id: str,
        limit: int = 10,
    ) -> list:
        """List invoices for a subscription."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")

        invoices = stripe.Invoice.list(
            subscription=subscription_id,
            limit=limit,
        )

        return [
            {
                "invoice_id": inv.id,
                "status": inv.status,
                "amount_due": inv.amount_due,
                "amount_paid": inv.amount_paid,
                "currency": inv.currency,
                "created": inv.created,
                "hosted_invoice_url": inv.hosted_invoice_url,
            }
            for inv in invoices.data
        ]


# Singleton instance
stripe_service = StripeService()
