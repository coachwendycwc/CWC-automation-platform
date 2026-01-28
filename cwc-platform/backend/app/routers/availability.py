from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.availability import Availability, AvailabilityOverride
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityResponse,
    AvailabilityBulkUpdate,
    WeeklyAvailabilityResponse,
    AvailabilityOverrideCreate,
    AvailabilityOverrideResponse,
    AvailabilityOverrideList,
)

router = APIRouter(prefix="/availability", tags=["Availability"])

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@router.get("", response_model=WeeklyAvailabilityResponse)
async def get_weekly_availability(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's weekly availability schedule."""
    result = await db.execute(
        select(Availability)
        .where(Availability.user_id == current_user.id)
        .order_by(Availability.day_of_week, Availability.start_time)
    )
    availabilities = result.scalars().all()

    # Group by day
    weekly = {day: [] for day in DAY_NAMES}
    for avail in availabilities:
        day_name = DAY_NAMES[avail.day_of_week]
        weekly[day_name].append(AvailabilityResponse.model_validate(avail))

    return WeeklyAvailabilityResponse(**weekly)


@router.put("", response_model=WeeklyAvailabilityResponse)
async def update_weekly_availability(
    data: AvailabilityBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Replace the entire weekly availability schedule.
    This deletes all existing availability and creates new entries.
    """
    # Delete existing availability
    await db.execute(
        delete(Availability).where(Availability.user_id == current_user.id)
    )

    # Create new availability entries
    new_availabilities = []
    for avail_data in data.availabilities:
        availability = Availability(
            user_id=current_user.id,
            **avail_data.model_dump(),
        )
        db.add(availability)
        new_availabilities.append(availability)

    await db.commit()

    # Refresh all to get generated fields
    for avail in new_availabilities:
        await db.refresh(avail)

    # Group by day
    weekly = {day: [] for day in DAY_NAMES}
    for avail in new_availabilities:
        day_name = DAY_NAMES[avail.day_of_week]
        weekly[day_name].append(AvailabilityResponse.model_validate(avail))

    return WeeklyAvailabilityResponse(**weekly)


# --- Availability Overrides ---


@router.get("/overrides", response_model=AvailabilityOverrideList)
async def list_availability_overrides(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all availability overrides (date-specific changes)."""
    query = (
        select(AvailabilityOverride)
        .where(AvailabilityOverride.user_id == current_user.id)
        .order_by(AvailabilityOverride.date.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    overrides = result.scalars().all()

    count = await db.scalar(
        select(func.count())
        .where(AvailabilityOverride.user_id == current_user.id)
    )

    return AvailabilityOverrideList(
        items=[AvailabilityOverrideResponse.model_validate(o) for o in overrides],
        total=count or 0,
    )


@router.post("/overrides", response_model=AvailabilityOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_availability_override(
    data: AvailabilityOverrideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an availability override for a specific date.

    Use is_available=False to block a date (vacation, holiday).
    Use is_available=True with start_time/end_time to add extra hours.
    """
    # Check if override already exists for this date
    existing = await db.execute(
        select(AvailabilityOverride).where(
            AvailabilityOverride.user_id == current_user.id,
            AvailabilityOverride.date == data.date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An override already exists for this date. Delete it first.",
        )

    override = AvailabilityOverride(
        user_id=current_user.id,
        **data.model_dump(),
    )
    db.add(override)
    await db.commit()
    await db.refresh(override)

    return AvailabilityOverrideResponse.model_validate(override)


@router.get("/overrides/{override_id}", response_model=AvailabilityOverrideResponse)
async def get_availability_override(
    override_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific availability override."""
    result = await db.execute(
        select(AvailabilityOverride).where(
            AvailabilityOverride.id == override_id,
            AvailabilityOverride.user_id == current_user.id,
        )
    )
    override = result.scalar_one_or_none()

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Override not found",
        )

    return AvailabilityOverrideResponse.model_validate(override)


@router.delete("/overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_override(
    override_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an availability override."""
    result = await db.execute(
        select(AvailabilityOverride).where(
            AvailabilityOverride.id == override_id,
            AvailabilityOverride.user_id == current_user.id,
        )
    )
    override = result.scalar_one_or_none()

    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Override not found",
        )

    await db.delete(override)
    await db.commit()
