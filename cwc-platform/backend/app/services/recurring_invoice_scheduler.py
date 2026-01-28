"""Background scheduler for recurring invoice generation."""

import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.recurring_invoice import RecurringInvoice
from app.models.invoice import Invoice
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


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


def get_due_date(today: date, payment_terms: str) -> date:
    """Calculate due date based on payment terms."""
    if payment_terms == "due_on_receipt":
        return today
    elif payment_terms == "net_15":
        return today + timedelta(days=15)
    elif payment_terms == "net_30":
        return today + timedelta(days=30)
    elif payment_terms == "net_45":
        return today + timedelta(days=45)
    elif payment_terms == "net_60":
        return today + timedelta(days=60)
    else:
        return today + timedelta(days=30)


class RecurringInvoiceScheduler:
    """Background scheduler for automated recurring invoice generation."""

    def __init__(self):
        self.running = False
        self.task = None
        self.check_interval = 3600  # Check every hour

    async def start(self):
        """Start the scheduler."""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("Recurring invoice scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Recurring invoice scheduler stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_and_generate_invoices()
            except Exception as e:
                logger.error(f"Error in recurring invoice scheduler: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_and_generate_invoices(self):
        """Check for recurring invoices that need to be generated."""
        async with async_session_maker() as db:
            today = date.today()

            # Find recurring invoices where:
            # - is_active is True
            # - next_invoice_date <= today
            # - end_date is None OR end_date >= today
            query = (
                select(RecurringInvoice)
                .options(selectinload(RecurringInvoice.contact))
                .where(
                    RecurringInvoice.is_active == True,
                    RecurringInvoice.next_invoice_date <= today,
                )
            )

            result = await db.execute(query)
            recurring_invoices = result.scalars().all()

            for recurring in recurring_invoices:
                # Skip if past end date
                if recurring.end_date and recurring.next_invoice_date > recurring.end_date:
                    recurring.is_active = False
                    await db.commit()
                    logger.info(f"Deactivated recurring invoice {recurring.id} - past end date")
                    continue

                try:
                    await self._generate_invoice(db, recurring, today)
                except Exception as e:
                    logger.error(f"Failed to generate invoice for recurring {recurring.id}: {e}")

    async def _generate_invoice(
        self,
        db: AsyncSession,
        recurring: RecurringInvoice,
        today: date,
    ):
        """Generate an invoice from a recurring template."""
        # Calculate due date
        due_date = get_due_date(today, recurring.payment_terms)

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
            logger.info(f"Deactivated recurring invoice {recurring.id} - reached end date")

        await db.commit()
        await db.refresh(invoice)

        logger.info(f"Generated invoice {invoice.invoice_number} from recurring {recurring.id}")

        # Auto-send if configured
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
                logger.error(f"Failed to auto-send invoice {invoice.invoice_number}: {e}")


# Singleton instance
recurring_invoice_scheduler = RecurringInvoiceScheduler()
