"""
Payment plan management router.
"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment_plan import PaymentPlan
from app.schemas.payment_plan import PaymentPlanCreate, PaymentPlanUpdate, PaymentPlanRead

router = APIRouter(prefix="/api", tags=["payment-plans"])


def _enrich_payment_plan_response(plan: PaymentPlan) -> PaymentPlanRead:
    """Add computed fields to payment plan response."""
    schedule = plan.schedule or []

    paid_count = sum(1 for item in schedule if item.get("status") == "paid")
    pending_count = sum(1 for item in schedule if item.get("status") == "pending")

    next_due = None
    for item in schedule:
        if item.get("status") == "pending":
            next_due = item
            break

    return PaymentPlanRead(
        id=plan.id,
        invoice_id=plan.invoice_id,
        total_amount=plan.total_amount,
        number_of_payments=plan.number_of_payments,
        payment_frequency=plan.payment_frequency,
        start_date=plan.start_date,
        schedule=schedule,
        status=plan.status,
        created_at=plan.created_at,
        next_due=next_due,
        paid_installments=paid_count,
        remaining_installments=pending_count,
    )


@router.get("/invoices/{invoice_id}/payment-plan", response_model=PaymentPlanRead)
async def get_payment_plan(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaymentPlanRead:
    """Get payment plan for an invoice."""
    result = await db.execute(
        select(PaymentPlan).where(PaymentPlan.invoice_id == invoice_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    return _enrich_payment_plan_response(plan)


@router.post("/invoices/{invoice_id}/payment-plan", response_model=PaymentPlanRead)
async def create_payment_plan(
    invoice_id: str,
    data: PaymentPlanCreate,
    db: AsyncSession = Depends(get_db),
) -> PaymentPlanRead:
    """Create a payment plan for an invoice."""
    # Verify invoice exists and doesn't already have a plan
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.payment_plan))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.payment_plan:
        raise HTTPException(
            status_code=400,
            detail="Invoice already has a payment plan"
        )

    if invoice.status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Cannot create payment plan for paid invoice"
        )

    if data.number_of_payments < 2:
        raise HTTPException(
            status_code=400,
            detail="Payment plan must have at least 2 payments"
        )

    # Create plan
    plan = PaymentPlan(
        invoice_id=invoice_id,
        total_amount=invoice.balance_due,  # Plan for remaining balance
        number_of_payments=data.number_of_payments,
        payment_frequency=data.payment_frequency,
        start_date=data.start_date,
    )

    # Generate schedule
    plan.generate_schedule()

    # Update invoice
    invoice.is_payment_plan = True

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return _enrich_payment_plan_response(plan)


@router.put("/payment-plans/{plan_id}", response_model=PaymentPlanRead)
async def update_payment_plan(
    plan_id: str,
    data: PaymentPlanUpdate,
    db: AsyncSession = Depends(get_db),
) -> PaymentPlanRead:
    """Update a payment plan."""
    result = await db.execute(
        select(PaymentPlan).where(PaymentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    if plan.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Cannot modify completed or cancelled payment plan"
        )

    # Check if any payments have been made
    paid_count = sum(1 for item in (plan.schedule or []) if item.get("status") == "paid")
    if paid_count > 0 and (data.payment_frequency or data.start_date):
        raise HTTPException(
            status_code=400,
            detail="Cannot modify schedule after payments have been made"
        )

    if data.payment_frequency is not None:
        plan.payment_frequency = data.payment_frequency
        plan.generate_schedule()

    if data.start_date is not None:
        plan.start_date = data.start_date
        plan.generate_schedule()

    if data.status is not None:
        plan.status = data.status

    await db.commit()
    await db.refresh(plan)

    return _enrich_payment_plan_response(plan)


@router.delete("/payment-plans/{plan_id}")
async def cancel_payment_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel a payment plan."""
    result = await db.execute(
        select(PaymentPlan)
        .options(selectinload(PaymentPlan.invoice))
        .where(PaymentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    if plan.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Payment plan is already completed or cancelled"
        )

    plan.status = "cancelled"

    # Update invoice
    if plan.invoice:
        plan.invoice.is_payment_plan = False

    await db.commit()

    return {"message": "Payment plan cancelled"}


@router.post("/payment-plans/{plan_id}/mark-paid/{installment}")
async def mark_installment_paid(
    plan_id: str,
    installment: int,
    payment_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaymentPlanRead:
    """Mark an installment as paid."""
    result = await db.execute(
        select(PaymentPlan).where(PaymentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    if plan.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Payment plan is not active"
        )

    # Verify installment exists
    found = False
    for item in plan.schedule or []:
        if item.get("installment") == installment:
            if item.get("status") == "paid":
                raise HTTPException(
                    status_code=400,
                    detail="Installment already paid"
                )
            found = True
            break

    if not found:
        raise HTTPException(
            status_code=404,
            detail="Installment not found"
        )

    plan.mark_installment_paid(installment, payment_id)

    await db.commit()
    await db.refresh(plan)

    return _enrich_payment_plan_response(plan)
