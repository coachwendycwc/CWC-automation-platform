"""Contractor (1099) tracking API endpoints."""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.contractor import Contractor, ContractorPayment
from app.models.expense import Expense, ExpenseCategory
from app.schemas.expense import (
    ContractorCreate, ContractorUpdate, ContractorRead, ContractorList,
    ContractorPaymentCreate, ContractorPaymentUpdate, ContractorPaymentRead,
    ContractorSummary,
)

router = APIRouter(prefix="/api/contractors", tags=["contractors"])


# ============ Contractor Endpoints ============

@router.get("", response_model=ContractorList)
async def list_contractors(
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all contractors."""
    query = select(Contractor)

    if is_active is not None:
        query = query.where(Contractor.is_active == is_active)
    if search:
        query = query.where(
            Contractor.name.ilike(f"%{search}%") |
            Contractor.business_name.ilike(f"%{search}%") |
            Contractor.email.ilike(f"%{search}%")
        )

    query = query.order_by(Contractor.name)

    # Count
    count_query = select(func.count(Contractor.id))
    if is_active is not None:
        count_query = count_query.where(Contractor.is_active == is_active)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query)
    contractors = result.scalars().all()

    # Add YTD totals
    current_year = date.today().year
    contractor_list = []
    for c in contractors:
        # Get YTD total
        ytd_result = await db.execute(
            select(func.sum(ContractorPayment.amount))
            .where(ContractorPayment.contractor_id == c.id)
            .where(ContractorPayment.tax_year == current_year)
        )
        ytd_total = ytd_result.scalar() or Decimal("0")

        contractor_dict = {
            "id": c.id,
            "name": c.name,
            "business_name": c.business_name,
            "email": c.email,
            "phone": c.phone,
            "tax_id": c.tax_id,
            "tax_id_type": c.tax_id_type,
            "w9_on_file": c.w9_on_file,
            "w9_received_date": c.w9_received_date,
            "address_line1": c.address_line1,
            "address_line2": c.address_line2,
            "city": c.city,
            "state": c.state,
            "zip_code": c.zip_code,
            "service_type": c.service_type,
            "is_active": c.is_active,
            "notes": c.notes,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "total_paid_ytd": ytd_total,
        }
        contractor_list.append(ContractorRead(**contractor_dict))

    return ContractorList(items=contractor_list, total=total)


@router.post("", response_model=ContractorRead)
async def create_contractor(
    data: ContractorCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new contractor."""
    contractor = Contractor(
        id=str(uuid.uuid4()),
        **data.model_dump(),
        is_active=True,
    )
    db.add(contractor)
    await db.commit()
    await db.refresh(contractor)

    return ContractorRead(**contractor.__dict__, total_paid_ytd=Decimal("0"))


@router.get("/{contractor_id}", response_model=ContractorRead)
async def get_contractor(
    contractor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single contractor."""
    result = await db.execute(
        select(Contractor).where(Contractor.id == contractor_id)
    )
    contractor = result.scalar_one_or_none()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Get YTD total
    current_year = date.today().year
    ytd_result = await db.execute(
        select(func.sum(ContractorPayment.amount))
        .where(ContractorPayment.contractor_id == contractor_id)
        .where(ContractorPayment.tax_year == current_year)
    )
    ytd_total = ytd_result.scalar() or Decimal("0")

    return ContractorRead(**contractor.__dict__, total_paid_ytd=ytd_total)


@router.put("/{contractor_id}", response_model=ContractorRead)
async def update_contractor(
    contractor_id: str,
    data: ContractorUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a contractor."""
    result = await db.execute(
        select(Contractor).where(Contractor.id == contractor_id)
    )
    contractor = result.scalar_one_or_none()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contractor, field, value)

    await db.commit()
    await db.refresh(contractor)

    # Get YTD total
    current_year = date.today().year
    ytd_result = await db.execute(
        select(func.sum(ContractorPayment.amount))
        .where(ContractorPayment.contractor_id == contractor_id)
        .where(ContractorPayment.tax_year == current_year)
    )
    ytd_total = ytd_result.scalar() or Decimal("0")

    return ContractorRead(**contractor.__dict__, total_paid_ytd=ytd_total)


@router.delete("/{contractor_id}")
async def delete_contractor(
    contractor_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a contractor (soft delete)."""
    result = await db.execute(
        select(Contractor).where(Contractor.id == contractor_id)
    )
    contractor = result.scalar_one_or_none()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    contractor.is_active = False
    await db.commit()
    return {"message": "Contractor deactivated"}


# ============ Payment Endpoints ============

@router.get("/{contractor_id}/payments", response_model=List[ContractorPaymentRead])
async def list_contractor_payments(
    contractor_id: str,
    tax_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List payments for a contractor."""
    query = select(ContractorPayment).where(ContractorPayment.contractor_id == contractor_id)

    if tax_year:
        query = query.where(ContractorPayment.tax_year == tax_year)

    query = query.order_by(ContractorPayment.payment_date.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/payments", response_model=ContractorPaymentRead)
async def create_contractor_payment(
    data: ContractorPaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Record a payment to a contractor."""
    # Verify contractor exists
    result = await db.execute(
        select(Contractor).where(Contractor.id == data.contractor_id)
    )
    contractor = result.scalar_one_or_none()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    expense_id = None

    # Optionally create matching expense
    if data.create_expense:
        # Get or create "Contractor Payments" category
        cat_result = await db.execute(
            select(ExpenseCategory).where(ExpenseCategory.name == "Contractor Payments")
        )
        category = cat_result.scalar_one_or_none()
        if not category:
            category = ExpenseCategory(
                id=str(uuid.uuid4()),
                name="Contractor Payments",
                color="#f97316",
                icon="users",
                is_tax_deductible=True,
                is_active=True,
            )
            db.add(category)
            await db.flush()

        expense = Expense(
            id=str(uuid.uuid4()),
            description=f"Payment to {contractor.name}: {data.description}",
            amount=data.amount,
            expense_date=data.payment_date,
            category_id=category.id,
            vendor=contractor.business_name or contractor.name,
            payment_method=data.payment_method,
            reference=data.reference,
            is_tax_deductible=True,
            tax_year=data.payment_date.year,
            notes=f"Contractor: {contractor.name}",
        )
        db.add(expense)
        await db.flush()
        expense_id = expense.id

    payment = ContractorPayment(
        id=str(uuid.uuid4()),
        contractor_id=data.contractor_id,
        amount=data.amount,
        payment_date=data.payment_date,
        description=data.description,
        payment_method=data.payment_method,
        reference=data.reference,
        invoice_number=data.invoice_number,
        invoice_url=data.invoice_url,
        expense_id=expense_id,
        tax_year=data.payment_date.year,
        notes=data.notes,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return payment


@router.put("/payments/{payment_id}", response_model=ContractorPaymentRead)
async def update_contractor_payment(
    payment_id: str,
    data: ContractorPaymentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a contractor payment."""
    result = await db.execute(
        select(ContractorPayment).where(ContractorPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    # Update tax year if date changed
    if "payment_date" in update_data:
        payment.tax_year = payment.payment_date.year

    await db.commit()
    await db.refresh(payment)
    return payment


@router.delete("/payments/{payment_id}")
async def delete_contractor_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a contractor payment."""
    result = await db.execute(
        select(ContractorPayment).where(ContractorPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Also delete linked expense if exists
    if payment.expense_id:
        expense_result = await db.execute(
            select(Expense).where(Expense.id == payment.expense_id)
        )
        expense = expense_result.scalar_one_or_none()
        if expense:
            await db.delete(expense)

    await db.delete(payment)
    await db.commit()
    return {"message": "Payment deleted"}


# ============ 1099 Summary ============

@router.get("/1099/{tax_year}", response_model=List[ContractorSummary])
async def get_1099_summary(
    tax_year: int,
    db: AsyncSession = Depends(get_db),
):
    """Get 1099 summary for all contractors for a tax year."""
    result = await db.execute(
        select(
            Contractor.id,
            Contractor.name,
            func.sum(ContractorPayment.amount).label("total_paid"),
            func.count(ContractorPayment.id).label("payment_count"),
        )
        .join(ContractorPayment, Contractor.id == ContractorPayment.contractor_id)
        .where(ContractorPayment.tax_year == tax_year)
        .group_by(Contractor.id, Contractor.name)
        .order_by(func.sum(ContractorPayment.amount).desc())
    )

    summaries = []
    for row in result.all():
        total = row.total_paid or Decimal("0")
        summaries.append(ContractorSummary(
            contractor_id=row.id,
            contractor_name=row.name,
            total_paid=total,
            payment_count=row.payment_count,
            needs_1099=total >= Decimal("600"),
        ))

    return summaries
