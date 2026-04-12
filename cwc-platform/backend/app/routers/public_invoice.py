"""
Public invoice viewing router (token-based, no auth required).
"""
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.booking import Booking
from app.models.invoice import Invoice
from app.schemas.invoice import InvoicePublic, InvoicePublicBooking

router = APIRouter(prefix="/api/invoice", tags=["public-invoice"])


@router.get("/{token}", response_model=InvoicePublic)
async def view_invoice(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvoicePublic:
    """
    View invoice by public token.
    Marks the invoice as viewed on first access.
    """
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.contact),
            selectinload(Invoice.organization),
        )
        .where(Invoice.view_token == token)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "cancelled":
        raise HTTPException(status_code=410, detail="Invoice has been cancelled")

    # Mark as viewed on first access
    if invoice.status == "sent" and invoice.viewed_at is None:
        invoice.status = "viewed"
        invoice.viewed_at = datetime.now()
        await db.commit()
        await db.refresh(invoice)

    # Check if overdue
    is_overdue = (
        invoice.due_date < date.today()
        and invoice.status not in ["paid", "cancelled"]
    )

    booking_summary = None
    booking_id = next(
        (
            item.get("booking_id")
            for item in (invoice.line_items or [])
            if isinstance(item, dict) and item.get("booking_id")
        ),
        None,
    )
    if booking_id:
        booking_result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.booking_type))
            .where(Booking.id == booking_id)
        )
        booking = booking_result.scalar_one_or_none()
        if booking and booking.booking_type:
            booking_summary = InvoicePublicBooking(
                id=booking.id,
                status=booking.status,
                start_time=booking.start_time,
                end_time=booking.end_time,
                booking_type_name=booking.booking_type.name,
                confirmation_token=booking.confirmation_token,
                meeting_provider=booking.meeting_provider,
                meeting_url=booking.meeting_url,
                location_details=booking.booking_type.location_details,
                post_booking_instructions=booking.booking_type.post_booking_instructions,
            )

    return InvoicePublic(
        invoice_number=invoice.invoice_number,
        line_items=invoice.line_items,
        subtotal=invoice.subtotal,
        tax_rate=invoice.tax_rate,
        tax_amount=invoice.tax_amount,
        discount_amount=invoice.discount_amount,
        total=invoice.total,
        amount_paid=invoice.amount_paid,
        balance_due=invoice.balance_due,
        payment_terms=invoice.payment_terms,
        due_date=invoice.due_date,
        status=invoice.status,
        memo=invoice.memo,
        contact_name=invoice.contact.full_name if invoice.contact else "Unknown",
        organization_name=invoice.organization.name if invoice.organization else None,
        is_overdue=is_overdue,
        booking=booking_summary,
    )


@router.post("/{token}/pay")
async def pay_invoice(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initiate payment for an invoice.
    Currently stubbed - will integrate with Stripe in the future.
    """
    result = await db.execute(
        select(Invoice).where(Invoice.view_token == token)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "cancelled":
        raise HTTPException(status_code=410, detail="Invoice has been cancelled")

    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Invoice already paid")

    if invoice.balance_due <= 0:
        raise HTTPException(status_code=400, detail="No balance due")

    # TODO: Create Stripe PaymentIntent here
    # For now, return a stub response

    return {
        "message": "Payment integration coming soon",
        "invoice_number": invoice.invoice_number,
        "amount_due": float(invoice.balance_due),
        "stripe_client_secret": None,  # Will be Stripe PaymentIntent client_secret
    }
