"""
Invoice service for number generation and calculations.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.invoice import LineItemCreate


class InvoiceService:
    """Service for invoice operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_invoice_number(self) -> str:
        """
        Generate unique invoice number in format: INV-YYYY-###
        Example: INV-2025-001, INV-2025-002, etc.
        """
        year = datetime.now().year
        prefix = f"INV-{year}-"

        # Find the last invoice number for this year
        result = await self.db.execute(
            select(Invoice.invoice_number)
            .where(Invoice.invoice_number.like(f"{prefix}%"))
            .order_by(Invoice.invoice_number.desc())
            .limit(1)
        )
        last_invoice_number = result.scalar_one_or_none()

        if last_invoice_number:
            # Extract the number part and increment
            last_num = int(last_invoice_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:03d}"

    @staticmethod
    def calculate_due_date(payment_terms: str, invoice_date: Optional[date] = None) -> date:
        """Calculate due date based on payment terms."""
        if invoice_date is None:
            invoice_date = date.today()

        match payment_terms:
            case "due_on_receipt":
                return invoice_date
            case "net_15":
                return invoice_date + timedelta(days=15)
            case "net_30":
                return invoice_date + timedelta(days=30)
            case "50_50_split":
                # First payment due immediately
                return invoice_date
            case _:
                # Default to net_30
                return invoice_date + timedelta(days=30)

    @staticmethod
    def calculate_line_item_amount(line_item: LineItemCreate) -> Decimal:
        """Calculate amount for a single line item."""
        return Decimal(str(line_item.quantity)) * Decimal(str(line_item.unit_price))

    @staticmethod
    def calculate_totals(
        line_items: list[LineItemCreate],
        tax_rate: Optional[Decimal] = None,
        discount_amount: Decimal = Decimal("0"),
    ) -> dict:
        """
        Calculate all totals for an invoice.

        Returns dict with: subtotal, tax_amount, total
        """
        subtotal = sum(
            InvoiceService.calculate_line_item_amount(item)
            for item in line_items
        )

        tax_amount = Decimal("0")
        if tax_rate:
            tax_amount = subtotal * (tax_rate / Decimal("100"))

        total = subtotal + tax_amount - discount_amount

        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total": total,
        }

    @staticmethod
    def prepare_line_items(line_items: list[LineItemCreate]) -> list[dict]:
        """
        Prepare line items for storage, calculating amounts.
        Returns list of dicts ready for JSON storage.
        """
        prepared = []
        for item in line_items:
            amount = InvoiceService.calculate_line_item_amount(item)
            prepared.append({
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "amount": float(amount),
                "service_type": item.service_type,
                "booking_id": item.booking_id,
            })
        return prepared

    async def get_stats(self) -> dict:
        """Get invoice statistics for dashboard."""
        # Total revenue (paid invoices)
        paid_result = await self.db.execute(
            select(func.sum(Invoice.total))
            .where(Invoice.status == "paid")
        )
        total_revenue = paid_result.scalar_one_or_none() or Decimal("0")

        # Total outstanding (sent, viewed, partial)
        outstanding_result = await self.db.execute(
            select(func.sum(Invoice.balance_due))
            .where(Invoice.status.in_(["sent", "viewed", "partial"]))
        )
        total_outstanding = outstanding_result.scalar_one_or_none() or Decimal("0")

        # Total overdue
        today = date.today()
        overdue_result = await self.db.execute(
            select(func.sum(Invoice.balance_due))
            .where(
                and_(
                    Invoice.status.in_(["sent", "viewed", "partial", "overdue"]),
                    Invoice.due_date < today,
                )
            )
        )
        total_overdue = overdue_result.scalar_one_or_none() or Decimal("0")

        # Counts
        count_result = await self.db.execute(
            select(
                func.count().filter(Invoice.status != "cancelled").label("total"),
                func.count().filter(Invoice.status == "paid").label("paid"),
                func.count().filter(Invoice.status.in_(["sent", "viewed", "partial"])).label("pending"),
                func.count().filter(Invoice.status == "overdue").label("overdue"),
            )
        )
        counts = count_result.one()

        return {
            "total_revenue": total_revenue,
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "invoices_count": counts.total,
            "paid_count": counts.paid,
            "pending_count": counts.pending,
            "overdue_count": counts.overdue,
        }

    async def check_overdue_invoices(self) -> int:
        """
        Check for invoices past their due date and mark them as overdue.
        Returns number of invoices marked as overdue.
        """
        today = date.today()
        result = await self.db.execute(
            select(Invoice)
            .where(
                and_(
                    Invoice.status.in_(["sent", "viewed", "partial"]),
                    Invoice.due_date < today,
                )
            )
        )
        invoices = result.scalars().all()

        count = 0
        for invoice in invoices:
            invoice.status = "overdue"
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def record_payment(
        self,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str = "other",
        payment_date: Optional[date] = None,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Payment:
        """Record a payment against an invoice."""
        if payment_date is None:
            payment_date = date.today()

        payment = Payment(
            invoice_id=invoice.id,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            reference=reference,
            notes=notes,
            created_by=created_by,
        )

        self.db.add(payment)

        # Update invoice amounts
        invoice.amount_paid = (invoice.amount_paid or Decimal("0")) + amount
        invoice.balance_due = invoice.total - invoice.amount_paid

        # Update status
        if invoice.balance_due <= 0:
            invoice.status = "paid"
            invoice.paid_at = datetime.now()
        elif invoice.amount_paid > 0:
            invoice.status = "partial"

        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def remove_payment(self, payment: Payment) -> None:
        """Remove a payment and update invoice amounts."""
        invoice = payment.invoice

        # Update invoice amounts
        invoice.amount_paid = (invoice.amount_paid or Decimal("0")) - payment.amount
        invoice.balance_due = invoice.total - invoice.amount_paid

        # Update status
        if invoice.amount_paid <= 0:
            invoice.status = "sent"
            invoice.paid_at = None
        else:
            invoice.status = "partial"

        await self.db.delete(payment)
        await self.db.commit()
