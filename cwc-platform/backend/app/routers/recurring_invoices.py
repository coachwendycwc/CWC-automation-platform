"""
Recurring invoices router.
Handles auto-generated invoice templates and schedules.
"""
import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contact import Contact
from app.models.recurring_invoice import RecurringInvoice
from app.models.invoice import Invoice
from app.schemas.recurring_invoice import (
    RecurringInvoiceCreate,
    RecurringInvoiceUpdate,
    RecurringInvoiceRead,
    RecurringInvoiceList,
    RecurringInvoiceDetail,
    RecurringInvoiceStats,
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recurring-invoices", tags=["recurring-invoices"])


def calculate_next_date(current_date: date, frequency: str) -> date:
    """Calculate the next invoice date based on frequency."""
    if frequency == "weekly":
        return current_date + timedelta(weeks=1)
    elif frequency == "bi_weekly":
        return current_date + timedelta(weeks=2)
    elif frequency == "monthly":
        # Add one month
        month = current_date.month + 1
        year = current_date.year
        if month > 12:
            month = 1
            year += 1
        day = min(current_date.day, 28)  # Handle month-end dates
        return date(year, month, day)
    elif frequency == "quarterly":
        # Add three months
        month = current_date.month + 3
        year = current_date.year
        while month > 12:
            month -= 12
            year += 1
        day = min(current_date.day, 28)
        return date(year, month, day)
    elif frequency == "annual":
        return date(current_date.year + 1, current_date.month, current_date.day)
    else:
        return current_date + timedelta(days=30)  # Default to ~monthly


def calculate_totals(line_items: list, tax_rate: Optional[Decimal], discount_amount: Decimal) -> dict:
    """Calculate subtotal, tax, and total from line items."""
    subtotal = Decimal("0")
    for item in line_items:
        quantity = Decimal(str(item.get("quantity", 1)))
        unit_price = Decimal(str(item.get("unit_price", 0)))
        subtotal += quantity * unit_price

    tax_amount = Decimal("0")
    if tax_rate and tax_rate > 0:
        tax_amount = (subtotal - discount_amount) * (tax_rate / 100)

    total = subtotal - discount_amount + tax_amount

    return {
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total": total,
    }


@router.get("", response_model=RecurringInvoiceList)
async def list_recurring_invoices(
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all recurring invoices."""
    query = (
        select(RecurringInvoice)
        .options(
            selectinload(RecurringInvoice.contact),
            selectinload(RecurringInvoice.organization),
        )
    )

    if is_active is not None:
        query = query.where(RecurringInvoice.is_active == is_active)
    if contact_id:
        query = query.where(RecurringInvoice.contact_id == contact_id)

    # Get total count
    count_query = select(func.count(RecurringInvoice.id))
    if is_active is not None:
        count_query = count_query.where(RecurringInvoice.is_active == is_active)
    if contact_id:
        count_query = count_query.where(RecurringInvoice.contact_id == contact_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(RecurringInvoice.next_invoice_date).offset(skip).limit(limit)
    result = await db.execute(query)
    recurring_invoices = result.scalars().all()

    items = [
        RecurringInvoiceRead(
            id=r.id,
            contact_id=r.contact_id,
            organization_id=r.organization_id,
            title=r.title,
            line_items=r.line_items,
            subtotal=r.subtotal,
            tax_rate=r.tax_rate,
            tax_amount=r.tax_amount,
            discount_amount=r.discount_amount,
            total=r.total,
            payment_terms=r.payment_terms,
            memo=r.memo,
            notes=r.notes,
            frequency=r.frequency,
            start_date=r.start_date,
            end_date=r.end_date,
            next_invoice_date=r.next_invoice_date,
            last_generated_date=r.last_generated_date,
            is_active=r.is_active,
            auto_send=r.auto_send,
            send_days_before=r.send_days_before,
            invoices_generated=r.invoices_generated,
            created_at=r.created_at,
            updated_at=r.updated_at,
            contact_name=r.contact.full_name if r.contact else None,
            organization_name=r.organization.name if r.organization else None,
        )
        for r in recurring_invoices
    ]

    return RecurringInvoiceList(items=items, total=total)


@router.post("", response_model=RecurringInvoiceRead)
async def create_recurring_invoice(
    data: RecurringInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new recurring invoice template."""
    # Verify contact exists
    result = await db.execute(
        select(Contact).where(Contact.id == data.contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Calculate totals
    line_items = [item.model_dump() for item in data.line_items]
    totals = calculate_totals(line_items, data.tax_rate, data.discount_amount)

    # Create recurring invoice
    recurring = RecurringInvoice(
        contact_id=data.contact_id,
        organization_id=data.organization_id,
        title=data.title,
        line_items=line_items,
        subtotal=totals["subtotal"],
        tax_rate=data.tax_rate,
        tax_amount=totals["tax_amount"],
        discount_amount=data.discount_amount,
        total=totals["total"],
        payment_terms=data.payment_terms,
        memo=data.memo,
        notes=data.notes,
        frequency=data.frequency,
        start_date=data.start_date,
        end_date=data.end_date,
        next_invoice_date=data.start_date,
        auto_send=data.auto_send,
        send_days_before=data.send_days_before,
    )
    db.add(recurring)
    await db.commit()
    await db.refresh(recurring)

    # Load relationships
    result = await db.execute(
        select(RecurringInvoice)
        .options(
            selectinload(RecurringInvoice.contact),
            selectinload(RecurringInvoice.organization),
        )
        .where(RecurringInvoice.id == recurring.id)
    )
    recurring = result.scalar_one()

    return RecurringInvoiceRead(
        id=recurring.id,
        contact_id=recurring.contact_id,
        organization_id=recurring.organization_id,
        title=recurring.title,
        line_items=recurring.line_items,
        subtotal=recurring.subtotal,
        tax_rate=recurring.tax_rate,
        tax_amount=recurring.tax_amount,
        discount_amount=recurring.discount_amount,
        total=recurring.total,
        payment_terms=recurring.payment_terms,
        memo=recurring.memo,
        notes=recurring.notes,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        end_date=recurring.end_date,
        next_invoice_date=recurring.next_invoice_date,
        last_generated_date=recurring.last_generated_date,
        is_active=recurring.is_active,
        auto_send=recurring.auto_send,
        send_days_before=recurring.send_days_before,
        invoices_generated=recurring.invoices_generated,
        created_at=recurring.created_at,
        updated_at=recurring.updated_at,
        contact_name=recurring.contact.full_name if recurring.contact else None,
        organization_name=recurring.organization.name if recurring.organization else None,
    )


@router.get("/stats", response_model=RecurringInvoiceStats)
async def get_recurring_invoice_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get recurring invoice statistics."""
    # Count by status
    active_result = await db.execute(
        select(func.count(RecurringInvoice.id)).where(RecurringInvoice.is_active == True)
    )
    active_count = active_result.scalar() or 0

    paused_result = await db.execute(
        select(func.count(RecurringInvoice.id)).where(RecurringInvoice.is_active == False)
    )
    paused_count = paused_result.scalar() or 0

    # Ended (past end_date)
    today = date.today()
    ended_result = await db.execute(
        select(func.count(RecurringInvoice.id)).where(
            RecurringInvoice.end_date != None,
            RecurringInvoice.end_date < today,
        )
    )
    ended_count = ended_result.scalar() or 0

    # Calculate monthly value of active recurring invoices
    result = await db.execute(
        select(RecurringInvoice).where(RecurringInvoice.is_active == True)
    )
    active_recurring = result.scalars().all()

    total_monthly_value = Decimal("0")
    for r in active_recurring:
        amount = r.total or Decimal("0")
        if r.frequency == "weekly":
            total_monthly_value += amount * Decimal("52") / Decimal("12")
        elif r.frequency == "bi_weekly":
            total_monthly_value += amount * Decimal("26") / Decimal("12")
        elif r.frequency == "monthly":
            total_monthly_value += amount
        elif r.frequency == "quarterly":
            total_monthly_value += amount / Decimal("3")
        elif r.frequency == "annual":
            total_monthly_value += amount / Decimal("12")

    # Count upcoming generations (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_result = await db.execute(
        select(func.count(RecurringInvoice.id)).where(
            RecurringInvoice.is_active == True,
            RecurringInvoice.next_invoice_date <= next_week,
        )
    )
    next_generation_count = upcoming_result.scalar() or 0

    return RecurringInvoiceStats(
        active_count=active_count,
        paused_count=paused_count,
        ended_count=ended_count,
        total_monthly_value=total_monthly_value,
        next_generation_count=next_generation_count,
    )


@router.get("/{recurring_id}", response_model=RecurringInvoiceDetail)
async def get_recurring_invoice(
    recurring_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get recurring invoice details with generated invoices."""
    result = await db.execute(
        select(RecurringInvoice)
        .options(
            selectinload(RecurringInvoice.contact),
            selectinload(RecurringInvoice.organization),
            selectinload(RecurringInvoice.generated_invoices),
        )
        .where(RecurringInvoice.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()

    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    generated_invoices = [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "total": float(inv.total),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "created_at": inv.created_at.isoformat(),
        }
        for inv in (recurring.generated_invoices or [])
    ]

    return RecurringInvoiceDetail(
        id=recurring.id,
        contact_id=recurring.contact_id,
        organization_id=recurring.organization_id,
        title=recurring.title,
        line_items=recurring.line_items,
        subtotal=recurring.subtotal,
        tax_rate=recurring.tax_rate,
        tax_amount=recurring.tax_amount,
        discount_amount=recurring.discount_amount,
        total=recurring.total,
        payment_terms=recurring.payment_terms,
        memo=recurring.memo,
        notes=recurring.notes,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        end_date=recurring.end_date,
        next_invoice_date=recurring.next_invoice_date,
        last_generated_date=recurring.last_generated_date,
        is_active=recurring.is_active,
        auto_send=recurring.auto_send,
        send_days_before=recurring.send_days_before,
        invoices_generated=recurring.invoices_generated,
        created_at=recurring.created_at,
        updated_at=recurring.updated_at,
        contact_name=recurring.contact.full_name if recurring.contact else None,
        organization_name=recurring.organization.name if recurring.organization else None,
        generated_invoices=generated_invoices,
    )


@router.put("/{recurring_id}", response_model=RecurringInvoiceRead)
async def update_recurring_invoice(
    recurring_id: str,
    data: RecurringInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a recurring invoice template."""
    result = await db.execute(
        select(RecurringInvoice)
        .options(
            selectinload(RecurringInvoice.contact),
            selectinload(RecurringInvoice.organization),
        )
        .where(RecurringInvoice.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()

    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    # Update fields
    if data.title is not None:
        recurring.title = data.title
    if data.line_items is not None:
        recurring.line_items = [item.model_dump() for item in data.line_items]
    if data.tax_rate is not None:
        recurring.tax_rate = data.tax_rate
    if data.discount_amount is not None:
        recurring.discount_amount = data.discount_amount
    if data.payment_terms is not None:
        recurring.payment_terms = data.payment_terms
    if data.memo is not None:
        recurring.memo = data.memo
    if data.notes is not None:
        recurring.notes = data.notes
    if data.frequency is not None:
        recurring.frequency = data.frequency
    if data.end_date is not None:
        recurring.end_date = data.end_date
    if data.auto_send is not None:
        recurring.auto_send = data.auto_send
    if data.send_days_before is not None:
        recurring.send_days_before = data.send_days_before

    # Recalculate totals
    totals = calculate_totals(recurring.line_items, recurring.tax_rate, recurring.discount_amount)
    recurring.subtotal = totals["subtotal"]
    recurring.tax_amount = totals["tax_amount"]
    recurring.total = totals["total"]

    await db.commit()
    await db.refresh(recurring)

    return RecurringInvoiceRead(
        id=recurring.id,
        contact_id=recurring.contact_id,
        organization_id=recurring.organization_id,
        title=recurring.title,
        line_items=recurring.line_items,
        subtotal=recurring.subtotal,
        tax_rate=recurring.tax_rate,
        tax_amount=recurring.tax_amount,
        discount_amount=recurring.discount_amount,
        total=recurring.total,
        payment_terms=recurring.payment_terms,
        memo=recurring.memo,
        notes=recurring.notes,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        end_date=recurring.end_date,
        next_invoice_date=recurring.next_invoice_date,
        last_generated_date=recurring.last_generated_date,
        is_active=recurring.is_active,
        auto_send=recurring.auto_send,
        send_days_before=recurring.send_days_before,
        invoices_generated=recurring.invoices_generated,
        created_at=recurring.created_at,
        updated_at=recurring.updated_at,
        contact_name=recurring.contact.full_name if recurring.contact else None,
        organization_name=recurring.organization.name if recurring.organization else None,
    )


@router.delete("/{recurring_id}")
async def delete_recurring_invoice(
    recurring_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a recurring invoice template."""
    result = await db.execute(
        select(RecurringInvoice).where(RecurringInvoice.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()

    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    await db.delete(recurring)
    await db.commit()

    return {"status": "ok", "message": "Recurring invoice deleted"}


@router.post("/{recurring_id}/activate")
async def activate_recurring_invoice(
    recurring_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Activate a recurring invoice."""
    result = await db.execute(
        select(RecurringInvoice).where(RecurringInvoice.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()

    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    recurring.is_active = True
    await db.commit()

    return {"status": "ok", "message": "Recurring invoice activated"}


@router.post("/{recurring_id}/deactivate")
async def deactivate_recurring_invoice(
    recurring_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate (pause) a recurring invoice."""
    result = await db.execute(
        select(RecurringInvoice).where(RecurringInvoice.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()

    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    recurring.is_active = False
    await db.commit()

    return {"status": "ok", "message": "Recurring invoice deactivated"}


@router.post("/{recurring_id}/generate")
async def generate_invoice(
    recurring_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Manually generate an invoice from the template."""
    result = await db.execute(
        select(RecurringInvoice)
        .options(selectinload(RecurringInvoice.contact))
        .where(RecurringInvoice.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()

    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring invoice not found")

    # Calculate due date based on payment terms
    today = date.today()
    if recurring.payment_terms == "due_on_receipt":
        due_date = today
    elif recurring.payment_terms == "net_15":
        due_date = today + timedelta(days=15)
    elif recurring.payment_terms == "net_30":
        due_date = today + timedelta(days=30)
    elif recurring.payment_terms == "net_45":
        due_date = today + timedelta(days=45)
    elif recurring.payment_terms == "net_60":
        due_date = today + timedelta(days=60)
    else:
        due_date = today + timedelta(days=30)

    # Create invoice
    invoice = Invoice(
        contact_id=recurring.contact_id,
        organization_id=recurring.organization_id,
        recurring_invoice_id=recurring.id,
        line_items=recurring.line_items,
        subtotal=recurring.subtotal,
        tax_rate=recurring.tax_rate,
        tax_amount=recurring.tax_amount,
        discount_amount=recurring.discount_amount,
        total=recurring.total,
        payment_terms=recurring.payment_terms,
        memo=recurring.memo,
        notes=recurring.notes,
        due_date=due_date,
        status="draft",
    )
    db.add(invoice)

    # Update recurring invoice
    recurring.last_generated_date = today
    recurring.next_invoice_date = calculate_next_date(today, recurring.frequency)
    recurring.invoices_generated += 1

    # Check if end date reached
    if recurring.end_date and recurring.next_invoice_date > recurring.end_date:
        recurring.is_active = False

    await db.commit()
    await db.refresh(invoice)

    # Optionally auto-send
    if recurring.auto_send and recurring.contact and recurring.contact.email:
        invoice.status = "sent"
        await db.commit()

        try:
            await email_service.send_invoice(
                invoice=invoice,
                contact=recurring.contact,
            )
            logger.info(f"Auto-sent invoice {invoice.invoice_number} to {recurring.contact.email}")
        except Exception as e:
            logger.error(f"Failed to auto-send invoice: {e}")

    return {
        "status": "ok",
        "message": "Invoice generated",
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
    }
