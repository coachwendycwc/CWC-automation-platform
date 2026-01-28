"""Expense tracking API endpoints."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.expense import Expense, ExpenseCategory, RecurringExpense
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseRead, ExpenseList,
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryRead,
    RecurringExpenseCreate, RecurringExpenseUpdate, RecurringExpenseRead,
    ExpenseSummary,
)

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


# ============ Default Categories ============

DEFAULT_CATEGORIES = [
    {"name": "Software & Subscriptions", "color": "#8b5cf6", "icon": "laptop"},
    {"name": "Marketing & Advertising", "color": "#ec4899", "icon": "megaphone"},
    {"name": "Professional Services", "color": "#3b82f6", "icon": "briefcase"},
    {"name": "Office Supplies", "color": "#10b981", "icon": "package"},
    {"name": "Travel & Transportation", "color": "#f59e0b", "icon": "car"},
    {"name": "Meals & Entertainment", "color": "#ef4444", "icon": "utensils"},
    {"name": "Education & Training", "color": "#6366f1", "icon": "book-open"},
    {"name": "Insurance", "color": "#14b8a6", "icon": "shield"},
    {"name": "Bank & Payment Fees", "color": "#64748b", "icon": "credit-card"},
    {"name": "Utilities", "color": "#a855f7", "icon": "zap"},
    {"name": "Contractor Payments", "color": "#f97316", "icon": "users"},
    {"name": "Other", "color": "#6b7280", "icon": "folder"},
]


# ============ Category Endpoints ============

@router.get("/categories", response_model=List[ExpenseCategoryRead])
async def list_categories(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all expense categories."""
    query = select(ExpenseCategory)
    if not include_inactive:
        query = query.where(ExpenseCategory.is_active == True)
    query = query.order_by(ExpenseCategory.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    # If no categories exist, create defaults
    if not categories:
        for cat_data in DEFAULT_CATEGORIES:
            category = ExpenseCategory(
                id=str(uuid.uuid4()),
                name=cat_data["name"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                is_tax_deductible=True,
                is_active=True,
            )
            db.add(category)
        await db.commit()

        result = await db.execute(query)
        categories = result.scalars().all()

    return categories


@router.post("/categories", response_model=ExpenseCategoryRead)
async def create_category(
    data: ExpenseCategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense category."""
    category = ExpenseCategory(
        id=str(uuid.uuid4()),
        **data.model_dump(),
        is_active=True,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=ExpenseCategoryRead)
async def update_category(
    category_id: str,
    data: ExpenseCategoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an expense category."""
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an expense category (soft delete)."""
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = False
    await db.commit()
    return {"message": "Category deleted"}


# ============ Expense Endpoints ============

@router.get("", response_model=ExpenseList)
async def list_expenses(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    category_id: Optional[str] = None,
    vendor: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tax_year: Optional[int] = None,
    is_recurring: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List expenses with filters."""
    query = select(Expense).options(selectinload(Expense.category))

    # Apply filters
    if category_id:
        query = query.where(Expense.category_id == category_id)
    if vendor:
        query = query.where(Expense.vendor.ilike(f"%{vendor}%"))
    if start_date:
        query = query.where(Expense.expense_date >= start_date)
    if end_date:
        query = query.where(Expense.expense_date <= end_date)
    if tax_year:
        query = query.where(Expense.tax_year == tax_year)
    if is_recurring is not None:
        query = query.where(Expense.is_recurring == is_recurring)
    if search:
        query = query.where(
            Expense.description.ilike(f"%{search}%") |
            Expense.vendor.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count(Expense.id))
    if category_id:
        count_query = count_query.where(Expense.category_id == category_id)
    if vendor:
        count_query = count_query.where(Expense.vendor.ilike(f"%{vendor}%"))
    if start_date:
        count_query = count_query.where(Expense.expense_date >= start_date)
    if end_date:
        count_query = count_query.where(Expense.expense_date <= end_date)
    if tax_year:
        count_query = count_query.where(Expense.tax_year == tax_year)
    if is_recurring is not None:
        count_query = count_query.where(Expense.is_recurring == is_recurring)
    if search:
        count_query = count_query.where(
            Expense.description.ilike(f"%{search}%") |
            Expense.vendor.ilike(f"%{search}%")
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(Expense.expense_date.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    expenses = result.scalars().all()

    return ExpenseList(items=expenses, total=total, page=page, size=size)


@router.post("", response_model=ExpenseRead)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense."""
    expense = Expense(
        id=str(uuid.uuid4()),
        **data.model_dump(),
        tax_year=data.expense_date.year,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense, ["category"])
    return expense


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single expense."""
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(Expense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: str,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an expense."""
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    # Update tax year if date changed
    if "expense_date" in update_data:
        expense.tax_year = expense.expense_date.year

    await db.commit()
    await db.refresh(expense, ["category"])
    return expense


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an expense."""
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    await db.delete(expense)
    await db.commit()
    return {"message": "Expense deleted"}


# ============ Recurring Expense Endpoints ============

@router.get("/recurring", response_model=List[RecurringExpenseRead])
async def list_recurring_expenses(
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
):
    """List recurring expenses."""
    query = select(RecurringExpense).options(selectinload(RecurringExpense.category))
    if is_active is not None:
        query = query.where(RecurringExpense.is_active == is_active)
    query = query.order_by(RecurringExpense.next_due_date)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/recurring", response_model=RecurringExpenseRead)
async def create_recurring_expense(
    data: RecurringExpenseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a recurring expense."""
    recurring = RecurringExpense(
        id=str(uuid.uuid4()),
        **data.model_dump(),
        next_due_date=data.start_date,
        is_active=True,
    )
    db.add(recurring)
    await db.commit()
    await db.refresh(recurring, ["category"])
    return recurring


@router.put("/recurring/{recurring_id}", response_model=RecurringExpenseRead)
async def update_recurring_expense(
    recurring_id: str,
    data: RecurringExpenseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a recurring expense."""
    result = await db.execute(
        select(RecurringExpense).where(RecurringExpense.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()
    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recurring, field, value)

    await db.commit()
    await db.refresh(recurring, ["category"])
    return recurring


@router.delete("/recurring/{recurring_id}")
async def delete_recurring_expense(
    recurring_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a recurring expense."""
    result = await db.execute(
        select(RecurringExpense).where(RecurringExpense.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()
    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    recurring.is_active = False
    await db.commit()
    return {"message": "Recurring expense deleted"}


@router.post("/recurring/{recurring_id}/generate", response_model=ExpenseRead)
async def generate_expense_from_recurring(
    recurring_id: str,
    expense_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually generate an expense from a recurring expense template."""
    result = await db.execute(
        select(RecurringExpense).where(RecurringExpense.id == recurring_id)
    )
    recurring = result.scalar_one_or_none()
    if not recurring:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    use_date = expense_date or recurring.next_due_date

    expense = Expense(
        id=str(uuid.uuid4()),
        description=recurring.description,
        amount=recurring.amount,
        expense_date=use_date,
        category_id=recurring.category_id,
        vendor=recurring.vendor,
        is_recurring=True,
        recurring_expense_id=recurring.id,
        is_tax_deductible=True,
        tax_year=use_date.year,
    )
    db.add(expense)

    # Update recurring expense
    recurring.last_generated_date = use_date
    # Calculate next due date based on frequency
    from dateutil.relativedelta import relativedelta
    freq_map = {
        "weekly": relativedelta(weeks=1),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
        "yearly": relativedelta(years=1),
    }
    recurring.next_due_date = use_date + freq_map.get(recurring.frequency, relativedelta(months=1))

    await db.commit()
    await db.refresh(expense, ["category"])
    return expense


# ============ Summary Endpoint ============

@router.get("/summary/{tax_year}", response_model=ExpenseSummary)
async def get_expense_summary(
    tax_year: int,
    db: AsyncSession = Depends(get_db),
):
    """Get expense summary for a tax year."""
    # Total expenses
    total_result = await db.execute(
        select(func.sum(Expense.amount))
        .where(Expense.tax_year == tax_year)
    )
    total_expenses = total_result.scalar() or Decimal("0")

    # Total deductible
    deductible_result = await db.execute(
        select(func.sum(Expense.amount))
        .where(Expense.tax_year == tax_year)
        .where(Expense.is_tax_deductible == True)
    )
    total_deductible = deductible_result.scalar() or Decimal("0")

    # By category
    category_result = await db.execute(
        select(
            ExpenseCategory.name,
            func.sum(Expense.amount).label("amount"),
            func.count(Expense.id).label("count"),
        )
        .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id, isouter=True)
        .where(Expense.tax_year == tax_year)
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(Expense.amount).desc())
    )
    by_category = [
        {"category": row.name or "Uncategorized", "amount": float(row.amount or 0), "count": row.count}
        for row in category_result.all()
    ]

    # By month
    month_result = await db.execute(
        select(
            extract("month", Expense.expense_date).label("month"),
            func.sum(Expense.amount).label("amount"),
        )
        .where(Expense.tax_year == tax_year)
        .group_by(extract("month", Expense.expense_date))
        .order_by(extract("month", Expense.expense_date))
    )
    by_month = [
        {"month": int(row.month), "amount": float(row.amount or 0)}
        for row in month_result.all()
    ]

    return ExpenseSummary(
        total_expenses=total_expenses,
        total_deductible=total_deductible,
        by_category=by_category,
        by_month=by_month,
    )
