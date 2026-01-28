"""
Stripe payment router.
Handles checkout sessions, webhooks, and payment processing.
"""
import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.database import get_db
from app.services.stripe_service import stripe_service
from app.services.email_service import email_service
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.contact import Contact
from app.models.stripe_customer import StripeCustomer
from app.models.subscription import Subscription
from app.models.stripe_price import StripePrice
from app.models.onboarding_assessment import OnboardingAssessment
from app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    invoice_id: Optional[str] = None
    view_token: Optional[str] = None  # Alternative to invoice_id for public payments


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    session_id: str
    url: str


class StripeConfigResponse(BaseModel):
    """Stripe configuration for frontend."""
    public_key: Optional[str]
    is_configured: bool


@router.get("/config", response_model=StripeConfigResponse)
async def get_stripe_config() -> StripeConfigResponse:
    """Get Stripe configuration for frontend."""
    return StripeConfigResponse(
        public_key=stripe_service.get_public_key(),
        is_configured=stripe_service.is_configured(),
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for an invoice."""
    if not stripe_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Stripe is not configured. Set STRIPE_SECRET_KEY.",
        )

    # Require either invoice_id or view_token
    if not request.invoice_id and not request.view_token:
        raise HTTPException(
            status_code=400,
            detail="Either invoice_id or view_token is required",
        )

    # Get invoice with contact - support both ID and view_token lookup
    query = select(Invoice).options(selectinload(Invoice.contact))
    if request.invoice_id:
        query = query.where(Invoice.id == request.invoice_id)
    else:
        query = query.where(Invoice.view_token == request.view_token)

    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Invoice is already paid")

    if invoice.status == "cancelled":
        raise HTTPException(status_code=400, detail="Invoice is cancelled")

    # Build URLs
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    success_url = f"{frontend_url}/pay/{invoice.view_token}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{frontend_url}/pay/{invoice.view_token}"

    try:
        session = stripe_service.create_checkout_session(
            invoice=invoice,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=invoice.contact.email if invoice.contact else None,
        )

        return CheckoutResponse(
            session_id=session["session_id"],
            url=session["url"],
        )
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Get raw body
    payload = await request.body()

    try:
        event = stripe_service.verify_webhook_signature(payload, stripe_signature)
    except ValueError as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    # Handle different event types
    if event_type == "checkout.session.completed":
        await handle_checkout_completed(db, data)
    elif event_type == "payment_intent.succeeded":
        await handle_payment_succeeded(db, data)
    elif event_type == "payment_intent.payment_failed":
        await handle_payment_failed(db, data)
    elif event_type == "charge.refunded":
        await handle_refund(db, data)
    # Subscription events
    elif event_type == "customer.subscription.created":
        await handle_subscription_created(db, data)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(db, data)
    elif event_type == "invoice.paid":
        await handle_stripe_invoice_paid(db, data)
    elif event_type == "invoice.payment_failed":
        await handle_stripe_invoice_failed(db, data)
    elif event_type == "setup_intent.succeeded":
        await handle_setup_intent_succeeded(db, data)

    return {"status": "ok"}


async def handle_checkout_completed(db: AsyncSession, session: dict):
    """Handle successful checkout session."""
    invoice_id = session.get("metadata", {}).get("invoice_id")
    if not invoice_id:
        logger.warning("Checkout completed without invoice_id in metadata")
        return

    # Get invoice
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.contact))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        logger.error(f"Invoice not found for checkout: {invoice_id}")
        return

    # Calculate amount paid (Stripe returns in cents)
    amount_paid = session.get("amount_total", 0) / 100

    # Create payment record
    payment = Payment(
        invoice_id=invoice.id,
        amount=amount_paid,
        payment_method="stripe",
        transaction_id=session.get("payment_intent"),
        status="completed",
        notes=f"Paid via Stripe Checkout (Session: {session.get('id')})",
    )
    db.add(payment)

    # Update invoice
    invoice.amount_paid += amount_paid
    invoice.balance_due = invoice.total - invoice.amount_paid

    if invoice.balance_due <= 0:
        invoice.status = "paid"
        invoice.paid_at = datetime.now()

    await db.commit()

    logger.info(f"Recorded payment of ${amount_paid} for invoice {invoice.invoice_number}")

    # Send receipt email
    if invoice.contact and invoice.contact.email:
        await email_service.send_payment_confirmation(
            invoice=invoice,
            contact=invoice.contact,
            amount_paid=amount_paid,
        )

        # Create and send onboarding assessment if not already exists
        try:
            existing_assessment = await db.execute(
                select(OnboardingAssessment).where(
                    OnboardingAssessment.contact_id == invoice.contact.id
                )
            )
            assessment = existing_assessment.scalar_one_or_none()

            if not assessment:
                # Create new assessment
                assessment = OnboardingAssessment(contact_id=invoice.contact.id)
                db.add(assessment)
                await db.commit()
                await db.refresh(assessment)

            # Send assessment email if not already completed
            if not assessment.completed_at:
                assessment_url = f"{settings.frontend_url}/onboarding/{assessment.token}"
                await email_service.send_onboarding_assessment(
                    contact=invoice.contact,
                    assessment_url=assessment_url,
                )
                assessment.email_sent_at = datetime.now()
                await db.commit()
                logger.info(f"Sent onboarding assessment to {invoice.contact.email}")
        except Exception as e:
            logger.error(f"Failed to send onboarding assessment: {e}")


async def handle_payment_succeeded(db: AsyncSession, payment_intent: dict):
    """Handle successful payment intent (backup for checkout.session.completed)."""
    invoice_id = payment_intent.get("metadata", {}).get("invoice_id")
    if not invoice_id:
        return  # Not an invoice payment

    # Check if already processed
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == payment_intent.get("id"))
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"Payment already recorded: {payment_intent.get('id')}")
        return

    # Get invoice
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.contact))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        return

    # Calculate amount
    amount_paid = payment_intent.get("amount_received", 0) / 100

    # Create payment record
    payment = Payment(
        invoice_id=invoice.id,
        amount=amount_paid,
        payment_method="stripe",
        transaction_id=payment_intent.get("id"),
        status="completed",
        notes=f"Paid via Stripe (Payment Intent: {payment_intent.get('id')})",
    )
    db.add(payment)

    # Update invoice
    invoice.amount_paid += amount_paid
    invoice.balance_due = invoice.total - invoice.amount_paid

    if invoice.balance_due <= 0:
        invoice.status = "paid"
        invoice.paid_at = datetime.now()

    await db.commit()

    logger.info(f"Recorded payment of ${amount_paid} for invoice {invoice.invoice_number}")


async def handle_payment_failed(db: AsyncSession, payment_intent: dict):
    """Handle failed payment."""
    invoice_id = payment_intent.get("metadata", {}).get("invoice_id")
    if not invoice_id:
        return

    logger.warning(f"Payment failed for invoice {invoice_id}: {payment_intent.get('last_payment_error', {}).get('message')}")

    # Optionally create a failed payment record
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if invoice:
        payment = Payment(
            invoice_id=invoice.id,
            amount=payment_intent.get("amount", 0) / 100,
            payment_method="stripe",
            transaction_id=payment_intent.get("id"),
            status="failed",
            notes=f"Payment failed: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}",
        )
        db.add(payment)
        await db.commit()


async def handle_refund(db: AsyncSession, charge: dict):
    """Handle refund event."""
    payment_intent_id = charge.get("payment_intent")
    if not payment_intent_id:
        return

    # Find the original payment
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.invoice))
        .where(Payment.transaction_id == payment_intent_id)
    )
    original_payment = result.scalar_one_or_none()

    if not original_payment:
        logger.warning(f"Original payment not found for refund: {payment_intent_id}")
        return

    # Calculate refund amount
    refund_amount = charge.get("amount_refunded", 0) / 100

    # Create refund payment record (negative amount)
    refund_payment = Payment(
        invoice_id=original_payment.invoice_id,
        amount=-refund_amount,
        payment_method="stripe_refund",
        transaction_id=f"refund_{charge.get('id')}",
        status="completed",
        notes=f"Refund for payment {payment_intent_id}",
    )
    db.add(refund_payment)

    # Update invoice
    invoice = original_payment.invoice
    if invoice:
        invoice.amount_paid -= refund_amount
        invoice.balance_due = invoice.total - invoice.amount_paid

        if invoice.balance_due > 0 and invoice.status == "paid":
            invoice.status = "sent"  # Revert to sent if balance due

    await db.commit()

    logger.info(f"Recorded refund of ${refund_amount} for invoice {invoice.invoice_number if invoice else 'unknown'}")


# ==================== Subscription Webhook Handlers ====================


async def handle_subscription_created(db: AsyncSession, subscription_data: dict):
    """Handle new subscription created in Stripe."""
    stripe_subscription_id = subscription_data.get("id")
    stripe_customer_id = subscription_data.get("customer")

    if not stripe_subscription_id or not stripe_customer_id:
        logger.warning("Subscription created without required IDs")
        return

    # Check if we already have this subscription
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"Subscription already exists: {stripe_subscription_id}")
        return

    # Find our StripeCustomer record
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.stripe_customer_id == stripe_customer_id)
    )
    stripe_customer = result.scalar_one_or_none()

    if not stripe_customer:
        logger.warning(f"StripeCustomer not found for Stripe customer: {stripe_customer_id}")
        return

    # Get the price ID from subscription items
    items = subscription_data.get("items", {}).get("data", [])
    if not items:
        logger.warning(f"No items in subscription: {stripe_subscription_id}")
        return

    stripe_price_id = items[0].get("price", {}).get("id")

    # Find our StripePrice record
    result = await db.execute(
        select(StripePrice).where(StripePrice.stripe_price_id == stripe_price_id)
    )
    stripe_price = result.scalar_one_or_none()

    if not stripe_price:
        logger.warning(f"StripePrice not found for Stripe price: {stripe_price_id}")
        return

    # Create subscription record
    subscription = Subscription(
        contact_id=stripe_customer.contact_id,
        stripe_customer_id=stripe_customer.id,
        stripe_price_id=stripe_price.id,
        stripe_subscription_id=stripe_subscription_id,
        status=subscription_data.get("status", "active"),
        current_period_start=datetime.fromtimestamp(subscription_data.get("current_period_start", 0)),
        current_period_end=datetime.fromtimestamp(subscription_data.get("current_period_end", 0)),
        cancel_at_period_end=subscription_data.get("cancel_at_period_end", False),
        trial_start=datetime.fromtimestamp(subscription_data["trial_start"]) if subscription_data.get("trial_start") else None,
        trial_end=datetime.fromtimestamp(subscription_data["trial_end"]) if subscription_data.get("trial_end") else None,
    )
    db.add(subscription)
    await db.commit()

    logger.info(f"Created subscription record for: {stripe_subscription_id}")


async def handle_subscription_updated(db: AsyncSession, subscription_data: dict):
    """Handle subscription updates (status changes, period changes, etc.)."""
    stripe_subscription_id = subscription_data.get("id")

    if not stripe_subscription_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription not found for update: {stripe_subscription_id}")
        return

    # Update fields
    subscription.status = subscription_data.get("status", subscription.status)
    subscription.current_period_start = datetime.fromtimestamp(subscription_data.get("current_period_start", 0))
    subscription.current_period_end = datetime.fromtimestamp(subscription_data.get("current_period_end", 0))
    subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)

    if subscription_data.get("canceled_at"):
        subscription.canceled_at = datetime.fromtimestamp(subscription_data["canceled_at"])

    if subscription_data.get("trial_start"):
        subscription.trial_start = datetime.fromtimestamp(subscription_data["trial_start"])
    if subscription_data.get("trial_end"):
        subscription.trial_end = datetime.fromtimestamp(subscription_data["trial_end"])

    await db.commit()

    logger.info(f"Updated subscription: {stripe_subscription_id} - status: {subscription.status}")


async def handle_subscription_deleted(db: AsyncSession, subscription_data: dict):
    """Handle subscription cancellation/deletion."""
    stripe_subscription_id = subscription_data.get("id")

    if not stripe_subscription_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription not found for deletion: {stripe_subscription_id}")
        return

    subscription.status = "canceled"
    subscription.canceled_at = datetime.now()

    await db.commit()

    logger.info(f"Subscription canceled: {stripe_subscription_id}")


async def handle_stripe_invoice_paid(db: AsyncSession, stripe_invoice: dict):
    """Handle Stripe invoice paid event (for subscriptions)."""
    subscription_id = stripe_invoice.get("subscription")

    if not subscription_id:
        # Not a subscription invoice, might be one-time payment
        return

    # Find our subscription
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.contact))
        .where(Subscription.stripe_subscription_id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription not found for invoice: {subscription_id}")
        return

    # Check if we already have an invoice for this Stripe invoice
    stripe_invoice_id = stripe_invoice.get("id")
    result = await db.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
    )
    existing_invoice = result.scalar_one_or_none()

    if existing_invoice:
        # Update existing invoice
        existing_invoice.status = "paid"
        existing_invoice.paid_at = datetime.now()
        existing_invoice.amount_paid = stripe_invoice.get("amount_paid", 0) / 100
        existing_invoice.balance_due = 0
        await db.commit()
        logger.info(f"Updated existing invoice {existing_invoice.invoice_number} as paid")
        return

    # Create a new invoice record for this subscription payment
    amount = stripe_invoice.get("amount_paid", 0) / 100

    invoice = Invoice(
        contact_id=subscription.contact_id,
        subscription_id=subscription.id,
        stripe_invoice_id=stripe_invoice_id,
        invoice_number=f"SUB-{stripe_invoice.get('number', '')}",
        status="paid",
        subtotal=amount,
        total=amount,
        amount_paid=amount,
        balance_due=0,
        due_date=datetime.now().date(),
        paid_at=datetime.now(),
        line_items=[{
            "description": f"Subscription payment - {stripe_invoice.get('lines', {}).get('data', [{}])[0].get('description', 'Subscription')}",
            "quantity": 1,
            "unit_price": float(amount),
        }],
    )
    db.add(invoice)

    # Create payment record
    payment = Payment(
        invoice_id=invoice.id,
        amount=amount,
        payment_method="stripe_subscription",
        transaction_id=stripe_invoice.get("payment_intent"),
        status="completed",
        notes=f"Subscription payment (Invoice: {stripe_invoice_id})",
    )
    db.add(payment)

    await db.commit()

    logger.info(f"Created invoice and payment for subscription: {subscription_id}")


async def handle_stripe_invoice_failed(db: AsyncSession, stripe_invoice: dict):
    """Handle Stripe invoice payment failure."""
    subscription_id = stripe_invoice.get("subscription")

    if not subscription_id:
        return

    # Find our subscription
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return

    # Update subscription status to past_due
    subscription.status = "past_due"
    await db.commit()

    logger.warning(f"Subscription payment failed: {subscription_id}")


async def handle_setup_intent_succeeded(db: AsyncSession, setup_intent: dict):
    """Handle successful setup intent (payment method added)."""
    stripe_customer_id = setup_intent.get("customer")
    payment_method_id = setup_intent.get("payment_method")

    if not stripe_customer_id or not payment_method_id:
        return

    # Find our StripeCustomer record
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.stripe_customer_id == stripe_customer_id)
    )
    stripe_customer = result.scalar_one_or_none()

    if not stripe_customer:
        logger.warning(f"StripeCustomer not found for setup intent: {stripe_customer_id}")
        return

    # Update default payment method
    stripe_customer.default_payment_method_id = payment_method_id
    await db.commit()

    logger.info(f"Updated payment method for customer: {stripe_customer_id}")
