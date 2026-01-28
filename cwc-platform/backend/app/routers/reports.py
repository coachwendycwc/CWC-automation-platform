"""Reports and analytics endpoints."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, case, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.contact import Contact
from app.models.booking import Booking
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.expense import Expense, ExpenseCategory
from app.models.mileage import MileageLog
from app.models.contractor import Contractor, ContractorPayment
from app.routers.auth import get_current_user
from app.schemas.expense import ProfitLossReport, TaxSummary, ContractorSummary

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get main dashboard statistics."""
    today = date.today()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    # Revenue stats
    total_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.user_id == current_user.id)
    )
    total_revenue = total_revenue_result.scalar() or Decimal("0")

    # This month's revenue
    month_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(
            Payment.user_id == current_user.id,
            Payment.payment_date >= start_of_month
        )
    )
    month_revenue = month_revenue_result.scalar() or Decimal("0")

    # Outstanding invoices
    outstanding_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.balance_due), 0))
        .where(
            Invoice.user_id == current_user.id,
            Invoice.status.in_(["draft", "sent", "partial"])
        )
    )
    outstanding = outstanding_result.scalar() or Decimal("0")

    # Invoice counts by status
    invoice_counts_result = await db.execute(
        select(Invoice.status, func.count(Invoice.id))
        .where(Invoice.user_id == current_user.id)
        .group_by(Invoice.status)
    )
    invoice_counts = {row[0]: row[1] for row in invoice_counts_result.fetchall()}

    # Contact count
    contact_count_result = await db.execute(
        select(func.count(Contact.id))
        .where(Contact.user_id == current_user.id)
    )
    contact_count = contact_count_result.scalar() or 0

    # Active projects
    active_projects_result = await db.execute(
        select(func.count(Project.id))
        .where(
            Project.user_id == current_user.id,
            Project.status == "active"
        )
    )
    active_projects = active_projects_result.scalar() or 0

    # Bookings this month
    bookings_month_result = await db.execute(
        select(func.count(Booking.id))
        .where(
            Booking.user_id == current_user.id,
            Booking.start_time >= datetime.combine(start_of_month, datetime.min.time())
        )
    )
    bookings_this_month = bookings_month_result.scalar() or 0

    # Upcoming bookings (next 7 days)
    upcoming_result = await db.execute(
        select(func.count(Booking.id))
        .where(
            Booking.user_id == current_user.id,
            Booking.start_time >= datetime.now(),
            Booking.start_time <= datetime.now() + timedelta(days=7),
            Booking.status == "confirmed"
        )
    )
    upcoming_bookings = upcoming_result.scalar() or 0

    return {
        "revenue": {
            "total": float(total_revenue),
            "this_month": float(month_revenue),
            "outstanding": float(outstanding),
        },
        "invoices": {
            "draft": invoice_counts.get("draft", 0),
            "sent": invoice_counts.get("sent", 0),
            "partial": invoice_counts.get("partial", 0),
            "paid": invoice_counts.get("paid", 0),
            "overdue": invoice_counts.get("overdue", 0),
        },
        "contacts": contact_count,
        "projects": {
            "active": active_projects,
        },
        "bookings": {
            "this_month": bookings_this_month,
            "upcoming": upcoming_bookings,
        },
    }


@router.get("/revenue/monthly")
async def get_monthly_revenue(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get monthly revenue for charting."""
    if year is None:
        year = date.today().year

    # Get monthly revenue
    result = await db.execute(
        select(
            extract("month", Payment.payment_date).label("month"),
            func.coalesce(func.sum(Payment.amount), 0).label("amount")
        )
        .where(
            Payment.user_id == current_user.id,
            extract("year", Payment.payment_date) == year
        )
        .group_by(extract("month", Payment.payment_date))
        .order_by(extract("month", Payment.payment_date))
    )

    monthly_data = {int(row.month): float(row.amount) for row in result.fetchall()}

    # Fill in all 12 months
    months = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for i in range(1, 13):
        months.append({
            "month": month_names[i - 1],
            "month_num": i,
            "revenue": monthly_data.get(i, 0),
        })

    # Calculate year total
    year_total = sum(m["revenue"] for m in months)

    return {
        "year": year,
        "months": months,
        "total": year_total,
    }


@router.get("/invoices/aging")
async def get_invoice_aging(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get invoice aging report."""
    today = date.today()

    # Get all unpaid invoices
    result = await db.execute(
        select(Invoice)
        .where(
            Invoice.user_id == current_user.id,
            Invoice.status.in_(["sent", "partial", "overdue"])
        )
        .order_by(Invoice.due_date)
    )
    invoices = result.scalars().all()

    # Categorize by age
    current = []  # Not yet due
    days_1_30 = []  # 1-30 days overdue
    days_31_60 = []  # 31-60 days overdue
    days_61_90 = []  # 61-90 days overdue
    days_90_plus = []  # 90+ days overdue

    for invoice in invoices:
        if invoice.due_date is None:
            current.append(invoice)
            continue

        days_overdue = (today - invoice.due_date).days

        inv_data = {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "contact_id": invoice.contact_id,
            "total": float(invoice.total),
            "balance_due": float(invoice.balance_due),
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "days_overdue": max(0, days_overdue),
        }

        if days_overdue <= 0:
            current.append(inv_data)
        elif days_overdue <= 30:
            days_1_30.append(inv_data)
        elif days_overdue <= 60:
            days_31_60.append(inv_data)
        elif days_overdue <= 90:
            days_61_90.append(inv_data)
        else:
            days_90_plus.append(inv_data)

    return {
        "current": {
            "invoices": current,
            "total": sum(i["balance_due"] for i in current if isinstance(i, dict)),
            "count": len(current),
        },
        "1_30_days": {
            "invoices": days_1_30,
            "total": sum(i["balance_due"] for i in days_1_30),
            "count": len(days_1_30),
        },
        "31_60_days": {
            "invoices": days_31_60,
            "total": sum(i["balance_due"] for i in days_31_60),
            "count": len(days_31_60),
        },
        "61_90_days": {
            "invoices": days_61_90,
            "total": sum(i["balance_due"] for i in days_61_90),
            "count": len(days_61_90),
        },
        "90_plus_days": {
            "invoices": days_90_plus,
            "total": sum(i["balance_due"] for i in days_90_plus),
            "count": len(days_90_plus),
        },
        "summary": {
            "total_outstanding": sum(
                sum(i["balance_due"] for i in bucket if isinstance(i, dict))
                for bucket in [current, days_1_30, days_31_60, days_61_90, days_90_plus]
            ),
            "total_invoices": len(invoices),
        },
    }


@router.get("/projects/hours")
async def get_project_hours(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project hours summary."""
    # Build query
    query = (
        select(
            Project.id,
            Project.title,
            Project.project_number,
            Project.status,
            func.coalesce(func.sum(TimeEntry.hours), 0).label("logged_hours"),
            func.coalesce(Project.estimated_hours, 0).label("estimated_hours"),
        )
        .outerjoin(Task, Task.project_id == Project.id)
        .outerjoin(TimeEntry, TimeEntry.task_id == Task.id)
        .where(Project.user_id == current_user.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )

    if project_id:
        query = query.where(Project.id == project_id)

    result = await db.execute(query)
    rows = result.fetchall()

    projects = []
    for row in rows:
        logged = float(row.logged_hours or 0)
        estimated = float(row.estimated_hours or 0)

        projects.append({
            "id": row.id,
            "project_number": row.project_number,
            "title": row.title,
            "status": row.status,
            "logged_hours": logged,
            "estimated_hours": estimated,
            "remaining_hours": max(0, estimated - logged) if estimated > 0 else None,
            "percent_used": round((logged / estimated) * 100, 1) if estimated > 0 else None,
        })

    # Summary
    total_logged = sum(p["logged_hours"] for p in projects)
    total_estimated = sum(p["estimated_hours"] for p in projects)

    return {
        "projects": projects,
        "summary": {
            "total_logged_hours": total_logged,
            "total_estimated_hours": total_estimated,
            "total_remaining": max(0, total_estimated - total_logged),
        },
    }


@router.get("/contacts/engagement")
async def get_contact_engagement(
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contact engagement metrics."""
    # Top contacts by revenue
    revenue_result = await db.execute(
        select(
            Contact.id,
            Contact.first_name,
            Contact.last_name,
            Contact.email,
            func.coalesce(func.sum(Payment.amount), 0).label("total_revenue"),
            func.count(Invoice.id.distinct()).label("invoice_count"),
        )
        .outerjoin(Invoice, Invoice.contact_id == Contact.id)
        .outerjoin(Payment, Payment.invoice_id == Invoice.id)
        .where(Contact.user_id == current_user.id)
        .group_by(Contact.id)
        .order_by(func.sum(Payment.amount).desc().nullslast())
        .limit(limit)
    )

    top_contacts = []
    for row in revenue_result.fetchall():
        top_contacts.append({
            "id": row.id,
            "name": f"{row.first_name} {row.last_name}".strip(),
            "email": row.email,
            "total_revenue": float(row.total_revenue or 0),
            "invoice_count": row.invoice_count or 0,
        })

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)

    active_contacts_result = await db.execute(
        select(func.count(Contact.id.distinct()))
        .outerjoin(Invoice, Invoice.contact_id == Contact.id)
        .where(
            Contact.user_id == current_user.id,
            Invoice.created_at >= thirty_days_ago
        )
    )
    active_count = active_contacts_result.scalar() or 0

    total_contacts_result = await db.execute(
        select(func.count(Contact.id))
        .where(Contact.user_id == current_user.id)
    )
    total_count = total_contacts_result.scalar() or 0

    return {
        "top_contacts": top_contacts,
        "activity": {
            "active_last_30_days": active_count,
            "total_contacts": total_count,
            "engagement_rate": round((active_count / total_count) * 100, 1) if total_count > 0 else 0,
        },
    }


@router.get("/export/invoices")
async def export_invoices_csv(
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export invoices to CSV."""
    query = (
        select(Invoice, Contact)
        .outerjoin(Contact, Invoice.contact_id == Contact.id)
        .where(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
    )

    if status:
        query = query.where(Invoice.status == status)
    if start_date:
        query = query.where(Invoice.issue_date >= start_date)
    if end_date:
        query = query.where(Invoice.issue_date <= end_date)

    result = await db.execute(query)
    rows = result.fetchall()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Invoice Number", "Date", "Due Date", "Client Name", "Client Email",
        "Subtotal", "Tax", "Discount", "Total", "Amount Paid", "Balance Due", "Status"
    ])

    for invoice, contact in rows:
        client_name = f"{contact.first_name} {contact.last_name}".strip() if contact else ""
        client_email = contact.email if contact else ""

        writer.writerow([
            invoice.invoice_number,
            invoice.issue_date.isoformat() if invoice.issue_date else "",
            invoice.due_date.isoformat() if invoice.due_date else "",
            client_name,
            client_email,
            float(invoice.subtotal),
            float(invoice.tax_amount),
            float(invoice.discount_amount),
            float(invoice.total),
            float(invoice.amount_paid),
            float(invoice.balance_due),
            invoice.status,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=invoices_{date.today().isoformat()}.csv"
        },
    )


@router.get("/export/payments")
async def export_payments_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export payments to CSV."""
    query = (
        select(Payment, Invoice, Contact)
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .outerjoin(Contact, Invoice.contact_id == Contact.id)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.payment_date.desc())
    )

    if start_date:
        query = query.where(Payment.payment_date >= start_date)
    if end_date:
        query = query.where(Payment.payment_date <= end_date)

    result = await db.execute(query)
    rows = result.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Payment Date", "Invoice Number", "Client Name", "Client Email",
        "Amount", "Payment Method", "Reference", "Notes"
    ])

    for payment, invoice, contact in rows:
        client_name = f"{contact.first_name} {contact.last_name}".strip() if contact else ""
        client_email = contact.email if contact else ""

        writer.writerow([
            payment.payment_date.isoformat() if payment.payment_date else "",
            invoice.invoice_number if invoice else "",
            client_name,
            client_email,
            float(payment.amount),
            payment.payment_method or "",
            payment.reference or "",
            payment.notes or "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=payments_{date.today().isoformat()}.csv"
        },
    )


@router.get("/export/time-entries")
async def export_time_entries_csv(
    project_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export time entries to CSV."""
    query = (
        select(TimeEntry, Task, Project)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .where(Project.user_id == current_user.id)
        .order_by(TimeEntry.entry_date.desc())
    )

    if project_id:
        query = query.where(Project.id == project_id)
    if start_date:
        query = query.where(TimeEntry.entry_date >= start_date)
    if end_date:
        query = query.where(TimeEntry.entry_date <= end_date)

    result = await db.execute(query)
    rows = result.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date", "Project", "Task", "Hours", "Description", "Created By"
    ])

    for entry, task, project in rows:
        writer.writerow([
            entry.entry_date.isoformat() if entry.entry_date else "",
            project.title if project else "",
            task.title if task else "",
            float(entry.hours),
            entry.description or "",
            entry.created_by or "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=time_entries_{date.today().isoformat()}.csv"
        },
    )


# ============ Profit & Loss Report ============

@router.get("/profit-loss", response_model=ProfitLossReport)
async def get_profit_loss_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tax_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get profit & loss report for a date range or tax year.
    If tax_year is provided, it overrides start_date/end_date.
    """
    # Determine date range
    if tax_year:
        period_start = date(tax_year, 1, 1)
        period_end = date(tax_year, 12, 31)
    else:
        period_start = start_date or date(date.today().year, 1, 1)
        period_end = end_date or date.today()

    # === REVENUE ===
    # Total payments received
    revenue_result = await db.execute(
        select(
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
            func.count(Invoice.id.distinct()).label("invoice_count"),
        )
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .where(
            Payment.user_id == current_user.id,
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
        )
    )
    revenue_row = revenue_result.one()
    total_revenue = Decimal(str(revenue_row.total or 0))
    invoices_paid = revenue_row.invoice_count or 0

    # === EXPENSES ===
    # Total expenses
    expenses_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
        )
    )
    total_expenses = Decimal(str(expenses_result.scalar() or 0))

    # Expenses by category
    category_result = await db.execute(
        select(
            ExpenseCategory.name,
            func.coalesce(func.sum(Expense.amount), 0).label("amount"),
            func.count(Expense.id).label("count"),
        )
        .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id, isouter=True)
        .where(
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
        )
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(Expense.amount).desc())
    )
    expenses_by_category = [
        {"category": row.name or "Uncategorized", "amount": float(row.amount), "count": row.count}
        for row in category_result.all()
    ]

    # === MILEAGE DEDUCTION ===
    mileage_result = await db.execute(
        select(func.coalesce(func.sum(MileageLog.total_deduction), 0))
        .where(
            MileageLog.trip_date >= period_start,
            MileageLog.trip_date <= period_end,
        )
    )
    total_mileage_deduction = Decimal(str(mileage_result.scalar() or 0))

    # === CONTRACTOR PAYMENTS ===
    # Note: Contractor payments should already be in expenses if create_expense=True
    # This gets payments not linked to expenses
    contractor_result = await db.execute(
        select(func.coalesce(func.sum(ContractorPayment.amount), 0))
        .where(
            ContractorPayment.payment_date >= period_start,
            ContractorPayment.payment_date <= period_end,
            ContractorPayment.expense_id.is_(None),  # Only unlinked payments
        )
    )
    total_contractor_payments = Decimal(str(contractor_result.scalar() or 0))

    # === CALCULATE NET ===
    # Total deductible outflows = expenses + mileage + unlinked contractor payments
    total_outflows = total_expenses + total_mileage_deduction + total_contractor_payments
    net_profit = total_revenue - total_outflows

    # Profit margin
    profit_margin = None
    if total_revenue > 0:
        profit_margin = (net_profit / total_revenue) * 100

    return ProfitLossReport(
        period_start=period_start,
        period_end=period_end,
        total_revenue=total_revenue,
        invoices_paid=invoices_paid,
        total_expenses=total_expenses,
        expenses_by_category=expenses_by_category,
        total_mileage_deduction=total_mileage_deduction,
        total_contractor_payments=total_contractor_payments,
        net_profit=net_profit,
        profit_margin=profit_margin,
    )


@router.get("/tax-summary/{tax_year}", response_model=TaxSummary)
async def get_tax_summary(
    tax_year: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive tax summary for a specific year."""

    # === GROSS INCOME ===
    income_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(
            Payment.user_id == current_user.id,
            extract("year", Payment.payment_date) == tax_year,
        )
    )
    gross_income = Decimal(str(income_result.scalar() or 0))

    # === EXPENSES ===
    expenses_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(
            Expense.tax_year == tax_year,
            Expense.is_tax_deductible == True,
        )
    )
    total_expenses = Decimal(str(expenses_result.scalar() or 0))

    # === MILEAGE DEDUCTION ===
    mileage_result = await db.execute(
        select(func.coalesce(func.sum(MileageLog.total_deduction), 0))
        .where(MileageLog.tax_year == tax_year)
    )
    mileage_deduction = Decimal(str(mileage_result.scalar() or 0))

    # === CONTRACTOR PAYMENTS ===
    contractor_result = await db.execute(
        select(func.coalesce(func.sum(ContractorPayment.amount), 0))
        .where(ContractorPayment.tax_year == tax_year)
    )
    contractor_payments = Decimal(str(contractor_result.scalar() or 0))

    # Total deductions (expenses already include contractor payments if linked)
    # Mileage is separate deduction
    total_deductions = total_expenses + mileage_deduction

    # Estimated taxable income
    estimated_taxable_income = gross_income - total_deductions

    # === QUARTERLY BREAKDOWN ===
    quarters = []
    for q in range(1, 5):
        if q == 1:
            q_start = date(tax_year, 1, 1)
            q_end = date(tax_year, 3, 31)
        elif q == 2:
            q_start = date(tax_year, 4, 1)
            q_end = date(tax_year, 6, 30)
        elif q == 3:
            q_start = date(tax_year, 7, 1)
            q_end = date(tax_year, 9, 30)
        else:
            q_start = date(tax_year, 10, 1)
            q_end = date(tax_year, 12, 31)

        # Quarter income
        q_income_result = await db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(
                Payment.user_id == current_user.id,
                Payment.payment_date >= q_start,
                Payment.payment_date <= q_end,
            )
        )
        q_income = Decimal(str(q_income_result.scalar() or 0))

        # Quarter expenses
        q_expense_result = await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0))
            .where(
                Expense.expense_date >= q_start,
                Expense.expense_date <= q_end,
            )
        )
        q_expenses = Decimal(str(q_expense_result.scalar() or 0))

        # Quarter mileage
        q_mileage_result = await db.execute(
            select(func.coalesce(func.sum(MileageLog.total_deduction), 0))
            .where(
                MileageLog.trip_date >= q_start,
                MileageLog.trip_date <= q_end,
            )
        )
        q_mileage = Decimal(str(q_mileage_result.scalar() or 0))

        quarters.append({
            "quarter": q,
            "income": float(q_income),
            "expenses": float(q_expenses),
            "mileage": float(q_mileage),
            "net": float(q_income - q_expenses - q_mileage),
        })

    # === CONTRACTORS NEEDING 1099 ===
    contractor_1099_result = await db.execute(
        select(
            Contractor.id,
            Contractor.name,
            func.sum(ContractorPayment.amount).label("total_paid"),
            func.count(ContractorPayment.id).label("payment_count"),
        )
        .join(ContractorPayment, Contractor.id == ContractorPayment.contractor_id)
        .where(ContractorPayment.tax_year == tax_year)
        .group_by(Contractor.id, Contractor.name)
        .having(func.sum(ContractorPayment.amount) >= 600)
        .order_by(func.sum(ContractorPayment.amount).desc())
    )

    contractors_needing_1099 = []
    for row in contractor_1099_result.all():
        total = Decimal(str(row.total_paid or 0))
        contractors_needing_1099.append(ContractorSummary(
            contractor_id=row.id,
            contractor_name=row.name,
            total_paid=total,
            payment_count=row.payment_count,
            needs_1099=True,
        ))

    return TaxSummary(
        tax_year=tax_year,
        gross_income=gross_income,
        total_expenses=total_expenses,
        mileage_deduction=mileage_deduction,
        contractor_payments=contractor_payments,
        total_deductions=total_deductions,
        estimated_taxable_income=estimated_taxable_income,
        quarters=quarters,
        contractors_needing_1099=contractors_needing_1099,
    )


@router.get("/export/expenses")
async def export_expenses_csv(
    tax_year: Optional[int] = None,
    category_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export expenses to CSV for tax purposes."""
    query = (
        select(Expense, ExpenseCategory)
        .outerjoin(ExpenseCategory, Expense.category_id == ExpenseCategory.id)
        .order_by(Expense.expense_date.desc())
    )

    if tax_year:
        query = query.where(Expense.tax_year == tax_year)
    if category_id:
        query = query.where(Expense.category_id == category_id)
    if start_date:
        query = query.where(Expense.expense_date >= start_date)
    if end_date:
        query = query.where(Expense.expense_date <= end_date)

    result = await db.execute(query)
    rows = result.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date", "Category", "Description", "Vendor", "Amount",
        "Payment Method", "Reference", "Tax Deductible", "Tax Year", "Notes"
    ])

    for expense, category in rows:
        writer.writerow([
            expense.expense_date.isoformat() if expense.expense_date else "",
            category.name if category else "Uncategorized",
            expense.description or "",
            expense.vendor or "",
            float(expense.amount),
            expense.payment_method or "",
            expense.reference or "",
            "Yes" if expense.is_tax_deductible else "No",
            expense.tax_year,
            expense.notes or "",
        ])

    output.seek(0)

    filename = f"expenses_{tax_year or 'all'}_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/mileage")
async def export_mileage_csv(
    tax_year: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export mileage log to CSV for IRS documentation."""
    query = select(MileageLog).order_by(MileageLog.trip_date.desc())

    if tax_year:
        query = query.where(MileageLog.tax_year == tax_year)
    if start_date:
        query = query.where(MileageLog.trip_date >= start_date)
    if end_date:
        query = query.where(MileageLog.trip_date <= end_date)

    result = await db.execute(query)
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date", "Purpose", "Description", "Start Location", "End Location",
        "Miles", "Round Trip", "Rate", "Deduction", "Notes"
    ])

    for log in logs:
        writer.writerow([
            log.trip_date.isoformat() if log.trip_date else "",
            log.purpose or "",
            log.description or "",
            log.start_location or "",
            log.end_location or "",
            float(log.miles),
            "Yes" if log.round_trip else "No",
            float(log.rate_per_mile),
            float(log.total_deduction),
            log.notes or "",
        ])

    output.seek(0)

    filename = f"mileage_log_{tax_year or 'all'}_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/contractors")
async def export_contractors_csv(
    tax_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export contractor payments for 1099 preparation."""
    # Get contractors with payment totals
    query = (
        select(
            Contractor,
            func.coalesce(func.sum(ContractorPayment.amount), 0).label("total_paid"),
            func.count(ContractorPayment.id).label("payment_count"),
        )
        .outerjoin(
            ContractorPayment,
            and_(
                Contractor.id == ContractorPayment.contractor_id,
                ContractorPayment.tax_year == tax_year if tax_year else True,
            )
        )
        .group_by(Contractor.id)
        .order_by(Contractor.name)
    )

    result = await db.execute(query)
    rows = result.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Name", "Business Name", "Tax ID", "Tax ID Type", "W-9 on File",
        "Address", "City", "State", "ZIP", "Total Paid", "Payment Count",
        "Needs 1099", "Email", "Phone"
    ])

    for contractor, total_paid, payment_count in rows:
        total = float(total_paid or 0)
        needs_1099 = "Yes" if total >= 600 else "No"

        writer.writerow([
            contractor.name,
            contractor.business_name or "",
            contractor.tax_id or "",
            contractor.tax_id_type or "",
            "Yes" if contractor.w9_on_file else "No",
            contractor.address_line1 or "",
            contractor.city or "",
            contractor.state or "",
            contractor.zip_code or "",
            total,
            payment_count,
            needs_1099,
            contractor.email or "",
            contractor.phone or "",
        ])

    output.seek(0)

    filename = f"contractors_1099_{tax_year or 'all'}_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
