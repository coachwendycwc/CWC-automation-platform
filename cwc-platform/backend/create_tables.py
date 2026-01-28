"""Script to create all database tables."""

import asyncio
from app.database import engine, Base
from app.models import (
    User, Organization, Contact, Interaction, FathomWebhook,
    BookingType, Availability, AvailabilityOverride, Booking,
    Invoice, Payment, PaymentPlan, FathomExtraction,
    ContractTemplate, Contract, SignatureAuditLog,
    ProjectTemplate, Project, Task, TimeEntry, ProjectActivityLog,
    ExpenseCategory, Expense, RecurringExpense,
    MileageLog, MileageRate,
    Contractor, ContractorPayment,
    OffboardingWorkflow, OffboardingTemplate, OffboardingActivity,
    StripeCustomer, StripeProduct, StripePrice, Subscription, RecurringInvoice,
)


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
