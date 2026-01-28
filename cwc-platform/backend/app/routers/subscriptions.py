"""
Subscriptions router.
Handles Stripe subscriptions, products, prices, and customer management.
"""
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.stripe_service import stripe_service
from app.models.contact import Contact
from app.models.stripe_customer import StripeCustomer
from app.models.stripe_product import StripeProduct
from app.models.stripe_price import StripePrice
from app.models.subscription import Subscription
from app.schemas.subscription import (
    StripeCustomerCreate,
    StripeCustomerRead,
    StripeProductCreate,
    StripeProductUpdate,
    StripeProductRead,
    StripePriceCreate,
    StripePriceRead,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionRead,
    SubscriptionList,
    SubscriptionDetail,
    SubscriptionStats,
    SetupIntentResponse,
    PaymentMethodRead,
    PaymentMethodCard,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


# ==================== Products ====================


@router.get("/products", response_model=list[StripeProductRead])
async def list_products(
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Only return active products"),
):
    """List all subscription products."""
    query = select(StripeProduct)
    if active_only:
        query = query.where(StripeProduct.is_active == True)
    query = query.order_by(StripeProduct.name)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/products", response_model=StripeProductRead)
async def create_product(
    data: StripeProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new subscription product in Stripe and locally."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    try:
        # Create in Stripe
        stripe_product = stripe_service.create_product(
            name=data.name,
            description=data.description,
        )

        # Create locally
        product = StripeProduct(
            name=data.name,
            description=data.description,
            stripe_product_id=stripe_product["id"],
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)

        return product
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/products/{product_id}", response_model=StripeProductRead)
async def update_product(
    product_id: str,
    data: StripeProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a subscription product."""
    result = await db.execute(
        select(StripeProduct).where(StripeProduct.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Update in Stripe
        stripe_service.update_product(
            product_id=product.stripe_product_id,
            name=data.name,
            description=data.description,
            active=data.is_active,
        )

        # Update locally
        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.is_active is not None:
            product.is_active = data.is_active

        await db.commit()
        await db.refresh(product)

        return product
    except Exception as e:
        logger.error(f"Failed to update product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Prices ====================


@router.get("/products/{product_id}/prices", response_model=list[StripePriceRead])
async def list_product_prices(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True),
):
    """List prices for a product."""
    query = (
        select(StripePrice)
        .options(selectinload(StripePrice.product))
        .where(StripePrice.product_id == product_id)
    )
    if active_only:
        query = query.where(StripePrice.is_active == True)

    result = await db.execute(query)
    prices = result.scalars().all()

    return [
        StripePriceRead(
            id=p.id,
            product_id=p.product_id,
            stripe_price_id=p.stripe_price_id,
            amount=p.amount,
            currency=p.currency,
            interval=p.interval,
            interval_count=p.interval_count,
            is_active=p.is_active,
            created_at=p.created_at,
            product_name=p.product.name if p.product else None,
        )
        for p in prices
    ]


@router.post("/products/{product_id}/prices", response_model=StripePriceRead)
async def create_price(
    product_id: str,
    data: StripePriceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new price for a product."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    # Get product
    result = await db.execute(
        select(StripeProduct).where(StripeProduct.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Create in Stripe
        stripe_price = stripe_service.create_price(
            product_id=product.stripe_product_id,
            amount=data.amount,
            currency=data.currency,
            interval=data.interval,
            interval_count=data.interval_count,
        )

        # Create locally
        price = StripePrice(
            product_id=product_id,
            stripe_price_id=stripe_price["id"],
            amount=data.amount,
            currency=data.currency,
            interval=data.interval,
            interval_count=data.interval_count,
        )
        db.add(price)
        await db.commit()
        await db.refresh(price)

        return StripePriceRead(
            id=price.id,
            product_id=price.product_id,
            stripe_price_id=price.stripe_price_id,
            amount=price.amount,
            currency=price.currency,
            interval=price.interval,
            interval_count=price.interval_count,
            is_active=price.is_active,
            created_at=price.created_at,
            product_name=product.name,
        )
    except Exception as e:
        logger.error(f"Failed to create price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Customers ====================


@router.post("/customers", response_model=StripeCustomerRead)
async def create_customer(
    data: StripeCustomerCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe customer for a contact."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    # Check if customer already exists
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.contact_id == data.contact_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return existing

    # Get contact
    result = await db.execute(
        select(Contact).where(Contact.id == data.contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    try:
        # Create in Stripe
        stripe_customer = stripe_service.create_customer(
            email=contact.email,
            name=contact.full_name,
            metadata={"contact_id": contact.id},
        )

        # Create locally
        customer = StripeCustomer(
            contact_id=contact.id,
            stripe_customer_id=stripe_customer["id"],
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        return customer
    except Exception as e:
        logger.error(f"Failed to create customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/setup-intent", response_model=SetupIntentResponse)
async def create_setup_intent(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a setup intent to collect payment method."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        setup_intent = stripe_service.create_setup_intent(
            customer_id=customer.stripe_customer_id
        )

        return SetupIntentResponse(
            setup_intent_id=setup_intent["id"],
            client_secret=setup_intent["client_secret"],
            status=setup_intent["status"],
        )
    except Exception as e:
        logger.error(f"Failed to create setup intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/payment-methods", response_model=list[PaymentMethodRead])
async def list_payment_methods(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List payment methods for a customer."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        methods = stripe_service.list_payment_methods(
            customer_id=customer.stripe_customer_id
        )

        return [
            PaymentMethodRead(
                payment_method_id=m["id"],
                type=m["type"],
                card=PaymentMethodCard(
                    brand=m["card"]["brand"],
                    last4=m["card"]["last4"],
                    exp_month=m["card"]["exp_month"],
                    exp_year=m["card"]["exp_year"],
                ) if m.get("card") else None,
            )
            for m in methods
        ]
    except Exception as e:
        logger.error(f"Failed to list payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Subscriptions ====================


@router.get("", response_model=SubscriptionList)
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all subscriptions."""
    query = (
        select(Subscription)
        .options(
            selectinload(Subscription.contact),
            selectinload(Subscription.organization),
            selectinload(Subscription.stripe_price).selectinload(StripePrice.product),
        )
    )

    if status:
        query = query.where(Subscription.status == status)
    if contact_id:
        query = query.where(Subscription.contact_id == contact_id)

    # Get total count
    count_query = select(func.count(Subscription.id))
    if status:
        count_query = count_query.where(Subscription.status == status)
    if contact_id:
        count_query = count_query.where(Subscription.contact_id == contact_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    subscriptions = result.scalars().all()

    items = [
        SubscriptionRead(
            id=s.id,
            contact_id=s.contact_id,
            organization_id=s.organization_id,
            stripe_customer_id=s.stripe_customer_id,
            stripe_price_id=s.stripe_price_id,
            stripe_subscription_id=s.stripe_subscription_id,
            status=s.status,
            current_period_start=s.current_period_start,
            current_period_end=s.current_period_end,
            cancel_at_period_end=s.cancel_at_period_end,
            canceled_at=s.canceled_at,
            trial_start=s.trial_start,
            trial_end=s.trial_end,
            notes=s.notes,
            created_at=s.created_at,
            updated_at=s.updated_at,
            contact_name=s.contact.full_name if s.contact else None,
            organization_name=s.organization.name if s.organization else None,
            product_name=s.stripe_price.product.name if s.stripe_price and s.stripe_price.product else None,
            price_amount=s.stripe_price.amount if s.stripe_price else None,
            price_interval=s.stripe_price.interval if s.stripe_price else None,
        )
        for s in subscriptions
    ]

    return SubscriptionList(items=items, total=total)


@router.post("", response_model=SubscriptionRead)
async def create_subscription(
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new subscription."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    # Get or create StripeCustomer
    result = await db.execute(
        select(StripeCustomer)
        .options(selectinload(StripeCustomer.contact))
        .where(StripeCustomer.contact_id == data.contact_id)
    )
    stripe_customer = result.scalar_one_or_none()

    if not stripe_customer:
        # Need to create customer first
        result = await db.execute(
            select(Contact).where(Contact.id == data.contact_id)
        )
        contact = result.scalar_one_or_none()

        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        try:
            stripe_cust = stripe_service.create_customer(
                email=contact.email,
                name=contact.full_name,
                metadata={"contact_id": contact.id},
            )

            stripe_customer = StripeCustomer(
                contact_id=contact.id,
                stripe_customer_id=stripe_cust["id"],
            )
            db.add(stripe_customer)
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create customer: {e}")

    # Get price
    result = await db.execute(
        select(StripePrice)
        .options(selectinload(StripePrice.product))
        .where(StripePrice.id == data.price_id)
    )
    price = result.scalar_one_or_none()

    if not price:
        raise HTTPException(status_code=404, detail="Price not found")

    try:
        # Create subscription in Stripe
        stripe_sub = stripe_service.create_subscription(
            customer_id=stripe_customer.stripe_customer_id,
            price_id=price.stripe_price_id,
            trial_days=data.trial_days,
        )

        # Create local subscription
        subscription = Subscription(
            contact_id=data.contact_id,
            organization_id=data.organization_id,
            stripe_customer_id=stripe_customer.id,
            stripe_price_id=price.id,
            stripe_subscription_id=stripe_sub["id"],
            status=stripe_sub["status"],
            current_period_start=datetime.fromtimestamp(stripe_sub["current_period_start"]),
            current_period_end=datetime.fromtimestamp(stripe_sub["current_period_end"]),
            cancel_at_period_end=stripe_sub.get("cancel_at_period_end", False),
            trial_start=datetime.fromtimestamp(stripe_sub["trial_start"]) if stripe_sub.get("trial_start") else None,
            trial_end=datetime.fromtimestamp(stripe_sub["trial_end"]) if stripe_sub.get("trial_end") else None,
            notes=data.notes,
        )
        db.add(subscription)
        await db.commit()

        # Refresh with relationships
        result = await db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.contact),
                selectinload(Subscription.organization),
                selectinload(Subscription.stripe_price).selectinload(StripePrice.product),
            )
            .where(Subscription.id == subscription.id)
        )
        subscription = result.scalar_one()

        return SubscriptionRead(
            id=subscription.id,
            contact_id=subscription.contact_id,
            organization_id=subscription.organization_id,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_price_id=subscription.stripe_price_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            trial_start=subscription.trial_start,
            trial_end=subscription.trial_end,
            notes=subscription.notes,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            contact_name=subscription.contact.full_name if subscription.contact else None,
            organization_name=subscription.organization.name if subscription.organization else None,
            product_name=subscription.stripe_price.product.name if subscription.stripe_price and subscription.stripe_price.product else None,
            price_amount=subscription.stripe_price.amount if subscription.stripe_price else None,
            price_interval=subscription.stripe_price.interval if subscription.stripe_price else None,
        )
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get subscription statistics."""
    # Count by status
    status_counts = {}
    for status in ["active", "trialing", "past_due", "canceled"]:
        result = await db.execute(
            select(func.count(Subscription.id)).where(Subscription.status == status)
        )
        status_counts[status] = result.scalar() or 0

    # Calculate MRR (Monthly Recurring Revenue)
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.stripe_price))
        .where(Subscription.status.in_(["active", "trialing"]))
    )
    active_subscriptions = result.scalars().all()

    mrr = Decimal("0")
    for sub in active_subscriptions:
        if sub.stripe_price:
            amount = sub.stripe_price.amount
            interval = sub.stripe_price.interval
            interval_count = sub.stripe_price.interval_count

            # Normalize to monthly
            if interval == "weekly":
                mrr += (amount * 52) / 12 / interval_count
            elif interval == "monthly":
                mrr += amount / interval_count
            elif interval == "quarterly":
                mrr += amount / 3 / interval_count
            elif interval == "yearly":
                mrr += amount / 12 / interval_count

    return SubscriptionStats(
        active_count=status_counts["active"],
        trialing_count=status_counts["trialing"],
        past_due_count=status_counts["past_due"],
        canceled_count=status_counts["canceled"],
        monthly_recurring_revenue=mrr,
        annual_recurring_revenue=mrr * 12,
    )


@router.get("/{subscription_id}", response_model=SubscriptionDetail)
async def get_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get subscription details with billing history."""
    result = await db.execute(
        select(Subscription)
        .options(
            selectinload(Subscription.contact),
            selectinload(Subscription.organization),
            selectinload(Subscription.stripe_price).selectinload(StripePrice.product),
            selectinload(Subscription.invoices),
        )
        .where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Get billing history from Stripe
    billing_history = []
    payment_methods = []

    if stripe_service.is_configured():
        try:
            invoices = stripe_service.list_subscription_invoices(
                subscription_id=subscription.stripe_subscription_id
            )
            billing_history = [
                {
                    "id": inv["id"],
                    "amount": inv["amount_paid"] / 100,
                    "status": inv["status"],
                    "created": datetime.fromtimestamp(inv["created"]).isoformat(),
                    "invoice_pdf": inv.get("invoice_pdf"),
                }
                for inv in invoices
            ]

            # Get payment methods
            result = await db.execute(
                select(StripeCustomer).where(StripeCustomer.id == subscription.stripe_customer_id)
            )
            stripe_customer = result.scalar_one_or_none()

            if stripe_customer:
                methods = stripe_service.list_payment_methods(
                    customer_id=stripe_customer.stripe_customer_id
                )
                payment_methods = [
                    {
                        "id": m["id"],
                        "type": m["type"],
                        "brand": m.get("card", {}).get("brand"),
                        "last4": m.get("card", {}).get("last4"),
                    }
                    for m in methods
                ]
        except Exception as e:
            logger.error(f"Failed to get billing history: {e}")

    return SubscriptionDetail(
        id=subscription.id,
        contact_id=subscription.contact_id,
        organization_id=subscription.organization_id,
        stripe_customer_id=subscription.stripe_customer_id,
        stripe_price_id=subscription.stripe_price_id,
        stripe_subscription_id=subscription.stripe_subscription_id,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
        notes=subscription.notes,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
        contact_name=subscription.contact.full_name if subscription.contact else None,
        organization_name=subscription.organization.name if subscription.organization else None,
        product_name=subscription.stripe_price.product.name if subscription.stripe_price and subscription.stripe_price.product else None,
        price_amount=subscription.stripe_price.amount if subscription.stripe_price else None,
        price_interval=subscription.stripe_price.interval if subscription.stripe_price else None,
        billing_history=billing_history,
        payment_methods=payment_methods,
    )


@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = Query(True, description="Cancel at period end or immediately"),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a subscription."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        stripe_service.cancel_subscription(
            subscription_id=subscription.stripe_subscription_id,
            at_period_end=at_period_end,
        )

        if at_period_end:
            subscription.cancel_at_period_end = True
        else:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.now()

        await db.commit()

        return {"status": "ok", "message": "Subscription cancelled"}
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{subscription_id}/pause")
async def pause_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Pause a subscription."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        stripe_service.pause_subscription(
            subscription_id=subscription.stripe_subscription_id
        )

        subscription.status = "paused"
        await db.commit()

        return {"status": "ok", "message": "Subscription paused"}
    except Exception as e:
        logger.error(f"Failed to pause subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{subscription_id}/resume")
async def resume_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused subscription."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    try:
        stripe_service.resume_subscription(
            subscription_id=subscription.stripe_subscription_id
        )

        subscription.status = "active"
        await db.commit()

        return {"status": "ok", "message": "Subscription resumed"}
    except Exception as e:
        logger.error(f"Failed to resume subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))
