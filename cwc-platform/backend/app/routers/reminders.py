"""Admin endpoints for managing booking reminders."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.reminder_service import reminder_service

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.post("/check")
async def trigger_reminder_check(
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a reminder check (admin only)."""
    try:
        await reminder_service.check_and_send_reminders()
        return {"message": "Reminder check completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/{booking_id}")
async def send_booking_reminder(
    booking_id: str,
    hours_until: int = 24,
    current_user: User = Depends(get_current_user),
):
    """Manually send a reminder for a specific booking."""
    success = await reminder_service.send_immediate_reminder(booking_id, hours_until)

    if not success:
        raise HTTPException(status_code=404, detail="Booking not found or reminder failed")

    return {"message": f"Reminder sent for booking {booking_id}"}


@router.get("/status")
async def get_reminder_status(
    current_user: User = Depends(get_current_user),
):
    """Get the status of the reminder service."""
    return {
        "is_running": reminder_service.is_running,
        "message": "Reminder service is active" if reminder_service.is_running else "Reminder service is stopped",
    }
