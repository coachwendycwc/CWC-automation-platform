"""Mileage tracking API endpoints."""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.mileage import MileageLog, MileageRate
from app.schemas.expense import (
    MileageLogCreate, MileageLogUpdate, MileageLogRead, MileageLogList,
    MileageSummary,
)

router = APIRouter(prefix="/api/mileage", tags=["mileage"])


# IRS standard mileage rates by year
IRS_RATES = {
    2024: Decimal("0.67"),
    2025: Decimal("0.70"),  # Estimated, update when announced
}


async def get_mileage_rate(year: int, db: AsyncSession) -> Decimal:
    """Get mileage rate for a given year."""
    # Check database first
    result = await db.execute(
        select(MileageRate).where(MileageRate.year == year)
    )
    rate = result.scalar_one_or_none()
    if rate:
        return rate.rate_per_mile

    # Fall back to hardcoded rates
    return IRS_RATES.get(year, Decimal("0.67"))


@router.get("", response_model=MileageLogList)
async def list_mileage_logs(
    tax_year: Optional[int] = None,
    purpose: Optional[str] = None,
    contact_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """List mileage logs with filters."""
    query = select(MileageLog)

    if tax_year:
        query = query.where(MileageLog.tax_year == tax_year)
    if purpose:
        query = query.where(MileageLog.purpose == purpose)
    if contact_id:
        query = query.where(MileageLog.contact_id == contact_id)
    if start_date:
        query = query.where(MileageLog.trip_date >= start_date)
    if end_date:
        query = query.where(MileageLog.trip_date <= end_date)

    query = query.order_by(MileageLog.trip_date.desc())

    # Count
    count_query = select(func.count(MileageLog.id))
    if tax_year:
        count_query = count_query.where(MileageLog.tax_year == tax_year)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query)
    logs = result.scalars().all()

    return MileageLogList(items=logs, total=total)


@router.post("", response_model=MileageLogRead)
async def create_mileage_log(
    data: MileageLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Log a business trip."""
    # Get rate
    rate = data.rate_per_mile or await get_mileage_rate(data.trip_date.year, db)

    # Calculate total miles (double if round trip)
    total_miles = data.miles * 2 if data.round_trip else data.miles

    # Calculate deduction
    total_deduction = total_miles * rate

    log = MileageLog(
        id=str(uuid.uuid4()),
        trip_date=data.trip_date,
        description=data.description,
        purpose=data.purpose,
        miles=total_miles,
        rate_per_mile=rate,
        total_deduction=total_deduction,
        start_location=data.start_location,
        end_location=data.end_location,
        round_trip=data.round_trip,
        contact_id=data.contact_id,
        tax_year=data.trip_date.year,
        notes=data.notes,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/{log_id}", response_model=MileageLogRead)
async def get_mileage_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single mileage log."""
    result = await db.execute(
        select(MileageLog).where(MileageLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Mileage log not found")
    return log


@router.put("/{log_id}", response_model=MileageLogRead)
async def update_mileage_log(
    log_id: str,
    data: MileageLogUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a mileage log."""
    result = await db.execute(
        select(MileageLog).where(MileageLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Mileage log not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle miles and round_trip changes
    if "miles" in update_data or "round_trip" in update_data:
        miles = update_data.get("miles", log.miles)
        round_trip = update_data.get("round_trip", log.round_trip)
        if round_trip:
            update_data["miles"] = miles * 2 if "miles" in update_data else log.miles
        # Recalculate deduction
        final_miles = update_data.get("miles", log.miles)
        log.total_deduction = final_miles * log.rate_per_mile

    for field, value in update_data.items():
        setattr(log, field, value)

    # Update tax year if date changed
    if "trip_date" in update_data:
        log.tax_year = log.trip_date.year

    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/{log_id}")
async def delete_mileage_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a mileage log."""
    result = await db.execute(
        select(MileageLog).where(MileageLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Mileage log not found")

    await db.delete(log)
    await db.commit()
    return {"message": "Mileage log deleted"}


@router.get("/summary/{tax_year}", response_model=MileageSummary)
async def get_mileage_summary(
    tax_year: int,
    db: AsyncSession = Depends(get_db),
):
    """Get mileage summary for a tax year."""
    # Totals
    result = await db.execute(
        select(
            func.sum(MileageLog.miles).label("total_miles"),
            func.sum(MileageLog.total_deduction).label("total_deduction"),
            func.count(MileageLog.id).label("trip_count"),
        )
        .where(MileageLog.tax_year == tax_year)
    )
    row = result.one()

    # By purpose
    purpose_result = await db.execute(
        select(
            MileageLog.purpose,
            func.sum(MileageLog.miles).label("miles"),
            func.sum(MileageLog.total_deduction).label("amount"),
        )
        .where(MileageLog.tax_year == tax_year)
        .group_by(MileageLog.purpose)
        .order_by(func.sum(MileageLog.miles).desc())
    )
    by_purpose = [
        {"purpose": r.purpose, "miles": float(r.miles or 0), "amount": float(r.amount or 0)}
        for r in purpose_result.all()
    ]

    return MileageSummary(
        total_miles=row.total_miles or Decimal("0"),
        total_deduction=row.total_deduction or Decimal("0"),
        trip_count=row.trip_count or 0,
        by_purpose=by_purpose,
    )


@router.get("/rates", response_model=List[dict])
async def get_mileage_rates(
    db: AsyncSession = Depends(get_db),
):
    """Get all mileage rates."""
    result = await db.execute(
        select(MileageRate).order_by(MileageRate.year.desc())
    )
    db_rates = result.scalars().all()

    # Combine with hardcoded rates
    rates = []
    for year, rate in sorted(IRS_RATES.items(), reverse=True):
        rates.append({"year": year, "rate_per_mile": float(rate), "source": "irs"})

    for db_rate in db_rates:
        # Override if exists
        for i, r in enumerate(rates):
            if r["year"] == db_rate.year:
                rates[i] = {
                    "year": db_rate.year,
                    "rate_per_mile": float(db_rate.rate_per_mile),
                    "source": "custom",
                }
                break
        else:
            rates.append({
                "year": db_rate.year,
                "rate_per_mile": float(db_rate.rate_per_mile),
                "source": "custom",
            })

    return sorted(rates, key=lambda x: x["year"], reverse=True)
