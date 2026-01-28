import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Date, Numeric, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class PaymentPlan(Base):
    """Payment plan for splitting invoice into installments."""

    __tablename__ = "payment_plans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    number_of_payments: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )  # monthly, bi_weekly, weekly, custom
    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Schedule stored as JSON
    # [{due_date: str, amount: float, status: str, payment_id: str | None}]
    schedule: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, completed, cancelled

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payment_plan")

    def __repr__(self) -> str:
        return f"<PaymentPlan {self.id} - {self.number_of_payments} payments>"

    def generate_schedule(self) -> None:
        """Generate payment schedule based on plan parameters."""
        from datetime import timedelta

        amount_per_payment = self.total_amount / self.number_of_payments
        schedule = []
        current_date = self.start_date

        for i in range(self.number_of_payments):
            schedule.append({
                "installment": i + 1,
                "due_date": current_date.isoformat(),
                "amount": float(round(amount_per_payment, 2)),
                "status": "pending",  # pending, paid, overdue
                "payment_id": None,
            })

            # Calculate next due date
            if self.payment_frequency == "weekly":
                current_date = current_date + timedelta(weeks=1)
            elif self.payment_frequency == "bi_weekly":
                current_date = current_date + timedelta(weeks=2)
            elif self.payment_frequency == "monthly":
                # Add roughly a month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    try:
                        current_date = current_date.replace(month=current_date.month + 1)
                    except ValueError:
                        # Handle months with fewer days
                        if current_date.month + 1 == 2:
                            current_date = current_date.replace(month=3, day=1) - timedelta(days=1)
                        else:
                            current_date = current_date.replace(month=current_date.month + 2, day=1) - timedelta(days=1)

        # Adjust last payment for rounding
        total_scheduled = sum(item["amount"] for item in schedule)
        diff = float(self.total_amount) - total_scheduled
        if diff != 0 and schedule:
            schedule[-1]["amount"] = round(schedule[-1]["amount"] + diff, 2)

        self.schedule = schedule

    def get_next_due_installment(self) -> dict | None:
        """Get the next pending installment."""
        for item in self.schedule or []:
            if item.get("status") == "pending":
                return item
        return None

    def mark_installment_paid(self, installment_num: int, payment_id: str) -> None:
        """Mark an installment as paid."""
        for item in self.schedule or []:
            if item.get("installment") == installment_num:
                item["status"] = "paid"
                item["payment_id"] = payment_id
                break

        # Check if all installments are paid
        all_paid = all(item.get("status") == "paid" for item in self.schedule or [])
        if all_paid:
            self.status = "completed"
