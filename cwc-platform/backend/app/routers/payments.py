"""
Payment management router.
"""
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentList
from app.services.invoice_service import InvoiceService
from app.services.email_service import email_service

router = APIRouter(prefix="/api", tags=["payments"])


@router.get("/invoices/{invoice_id}/payments", response_model=list[PaymentRead])
async def list_invoice_payments(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentRead]:
    """List all payments for an invoice."""
    # Verify invoice exists
    invoice_result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    if not invoice_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Invoice not found")

    result = await db.execute(
        select(Payment)
        .where(Payment.invoice_id == invoice_id)
        .order_by(Payment.payment_date.desc())
    )
    payments = result.scalars().all()

    return [PaymentRead.model_validate(p) for p in payments]


@router.post("/invoices/{invoice_id}/payments", response_model=PaymentRead)
async def record_payment(
    invoice_id: str,
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    """Record a payment against an invoice."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.contact))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status in ["cancelled", "draft"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot record payment on {invoice.status} invoice"
        )

    if data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be positive"
        )

    if data.amount > invoice.balance_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount (${data.amount}) exceeds balance due (${invoice.balance_due})"
        )

    service = InvoiceService(db)

    payment = await service.record_payment(
        invoice=invoice,
        amount=data.amount,
        payment_method=data.payment_method,
        payment_date=data.payment_date,
        reference=data.reference,
        notes=data.notes,
    )

    # Send confirmation email
    if invoice.contact:
        await email_service.send_payment_confirmation(
            invoice,
            invoice.contact,
            float(data.amount),
        )

    return PaymentRead.model_validate(payment)


@router.get("/payments", response_model=list[PaymentList])
async def list_all_payments(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentList]:
    """List all payments across all invoices."""
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.invoice))
        .order_by(Payment.payment_date.desc())
        .offset(skip)
        .limit(limit)
    )
    payments = result.scalars().all()

    return [
        PaymentList(
            id=p.id,
            invoice_id=p.invoice_id,
            invoice_number=p.invoice.invoice_number if p.invoice else None,
            amount=p.amount,
            payment_method=p.payment_method,
            payment_date=p.payment_date,
            reference=p.reference,
            created_at=p.created_at,
        )
        for p in payments
    ]


@router.get("/payments/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    """Get payment by ID."""
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return PaymentRead.model_validate(payment)


@router.delete("/payments/{payment_id}")
async def delete_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a payment and update invoice balance."""
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.invoice))
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    service = InvoiceService(db)
    await service.remove_payment(payment)

    return {"message": "Payment deleted"}
