"""
Invoice management router.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.invoice import Invoice
from app.models.contact import Contact
from app.models.organization import Organization
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceRead,
    InvoiceList,
    InvoiceSend,
    InvoiceStats,
)
from app.services.invoice_service import InvoiceService
from app.services.email_service import email_service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceList])
async def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search invoice number or contact name"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceList]:
    """List all invoices with optional filters."""
    query = select(Invoice).options(
        selectinload(Invoice.contact),
        selectinload(Invoice.organization),
    )

    # Apply filters
    conditions = []
    if status:
        conditions.append(Invoice.status == status)
    if contact_id:
        conditions.append(Invoice.contact_id == contact_id)
    if organization_id:
        conditions.append(Invoice.organization_id == organization_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Invoice.invoice_number.ilike(search_term),
            )
        )

    query = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    invoices = result.scalars().all()

    return [
        InvoiceList(
            id=inv.id,
            invoice_number=inv.invoice_number,
            contact_id=inv.contact_id,
            contact_name=inv.contact.full_name if inv.contact else None,
            organization_name=inv.organization.name if inv.organization else None,
            total=inv.total,
            balance_due=inv.balance_due,
            status=inv.status,
            due_date=inv.due_date,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]


@router.get("/stats", response_model=InvoiceStats)
async def get_invoice_stats(
    db: AsyncSession = Depends(get_db),
) -> InvoiceStats:
    """Get invoice statistics for dashboard."""
    service = InvoiceService(db)
    stats = await service.get_stats()
    return InvoiceStats(**stats)


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    """Get invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.contact),
            selectinload(Invoice.organization),
            selectinload(Invoice.payments),
            selectinload(Invoice.payment_plan),
        )
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return InvoiceRead.model_validate(invoice)


@router.post("", response_model=InvoiceRead)
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    """Create a new invoice."""
    # Verify contact exists
    contact_result = await db.execute(
        select(Contact).where(Contact.id == data.contact_id)
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Verify organization if provided
    if data.organization_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == data.organization_id)
        )
        if not org_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Organization not found")

    service = InvoiceService(db)

    # Generate invoice number
    invoice_number = await service.generate_invoice_number()

    # Calculate due date
    due_date = data.due_date or service.calculate_due_date(data.payment_terms)

    # Prepare line items and calculate totals
    line_items = service.prepare_line_items(data.line_items)
    totals = service.calculate_totals(
        data.line_items,
        data.tax_rate,
        data.discount_amount,
    )

    invoice = Invoice(
        invoice_number=invoice_number,
        contact_id=data.contact_id,
        organization_id=data.organization_id,
        line_items=line_items,
        subtotal=totals["subtotal"],
        tax_rate=data.tax_rate,
        tax_amount=totals["tax_amount"],
        discount_amount=data.discount_amount,
        total=totals["total"],
        balance_due=totals["total"],
        payment_terms=data.payment_terms,
        due_date=due_date,
        notes=data.notes,
        memo=data.memo,
    )

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    return InvoiceRead.model_validate(invoice)


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: str,
    data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    """Update an invoice. Only draft invoices can have line items changed."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    service = InvoiceService(db)

    # Update simple fields
    if data.contact_id is not None:
        # Verify contact exists
        contact_result = await db.execute(
            select(Contact).where(Contact.id == data.contact_id)
        )
        if not contact_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Contact not found")
        invoice.contact_id = data.contact_id

    if data.organization_id is not None:
        if data.organization_id:
            org_result = await db.execute(
                select(Organization).where(Organization.id == data.organization_id)
            )
            if not org_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Organization not found")
        invoice.organization_id = data.organization_id or None

    if data.payment_terms is not None:
        invoice.payment_terms = data.payment_terms

    if data.due_date is not None:
        invoice.due_date = data.due_date

    if data.tax_rate is not None:
        invoice.tax_rate = data.tax_rate

    if data.discount_amount is not None:
        invoice.discount_amount = data.discount_amount

    if data.notes is not None:
        invoice.notes = data.notes

    if data.memo is not None:
        invoice.memo = data.memo

    if data.status is not None:
        invoice.status = data.status

    # Update line items only for draft invoices
    if data.line_items is not None:
        if invoice.status != "draft":
            raise HTTPException(
                status_code=400,
                detail="Cannot modify line items on non-draft invoice"
            )

        invoice.line_items = service.prepare_line_items(data.line_items)

    # Recalculate totals if needed
    if data.line_items is not None or data.tax_rate is not None or data.discount_amount is not None:
        from app.schemas.invoice import LineItemCreate

        # Convert stored line items back to LineItemCreate for calculation
        line_items = [
            LineItemCreate(
                description=item["description"],
                quantity=Decimal(str(item["quantity"])),
                unit_price=Decimal(str(item["unit_price"])),
                service_type=item.get("service_type"),
                booking_id=item.get("booking_id"),
            )
            for item in invoice.line_items
        ]

        totals = service.calculate_totals(
            line_items,
            invoice.tax_rate,
            invoice.discount_amount,
        )

        invoice.subtotal = totals["subtotal"]
        invoice.tax_amount = totals["tax_amount"]
        invoice.total = totals["total"]
        invoice.balance_due = totals["total"] - invoice.amount_paid

    await db.commit()
    await db.refresh(invoice)

    return InvoiceRead.model_validate(invoice)


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a draft invoice. Cannot delete sent/paid invoices."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete non-draft invoice. Cancel it instead."
        )

    await db.delete(invoice)
    await db.commit()

    return {"message": "Invoice deleted"}


@router.post("/{invoice_id}/send", response_model=InvoiceRead)
async def send_invoice(
    invoice_id: str,
    data: InvoiceSend,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    """Send invoice to client."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.contact))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status not in ["draft", "sent"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot send invoice in current status"
        )

    # Send email if requested
    if data.send_email and invoice.contact:
        # TODO: Get actual base_url from config
        base_url = "http://localhost:3001"
        await email_service.send_invoice(
            invoice,
            invoice.contact,
            base_url,
            data.email_message,
        )

    # Update status
    invoice.status = "sent"
    invoice.sent_at = datetime.now()

    await db.commit()
    await db.refresh(invoice)

    return InvoiceRead.model_validate(invoice)


@router.post("/{invoice_id}/duplicate", response_model=InvoiceRead)
async def duplicate_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    """Create a new draft invoice as a copy of an existing one."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Invoice not found")

    service = InvoiceService(db)

    # Generate new invoice number
    invoice_number = await service.generate_invoice_number()

    # Calculate new due date based on original payment terms
    due_date = service.calculate_due_date(original.payment_terms)

    # Create new invoice
    new_invoice = Invoice(
        invoice_number=invoice_number,
        contact_id=original.contact_id,
        organization_id=original.organization_id,
        line_items=original.line_items.copy() if original.line_items else [],
        subtotal=original.subtotal,
        tax_rate=original.tax_rate,
        tax_amount=original.tax_amount,
        discount_amount=original.discount_amount,
        total=original.total,
        balance_due=original.total,  # Reset balance
        payment_terms=original.payment_terms,
        due_date=due_date,
        notes=original.notes,
        memo=original.memo,
        status="draft",
    )

    db.add(new_invoice)
    await db.commit()
    await db.refresh(new_invoice)

    return InvoiceRead.model_validate(new_invoice)


@router.post("/{invoice_id}/cancel", response_model=InvoiceRead)
async def cancel_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
) -> InvoiceRead:
    """Cancel an invoice."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel paid invoice"
        )

    invoice.status = "cancelled"

    await db.commit()
    await db.refresh(invoice)

    return InvoiceRead.model_validate(invoice)
