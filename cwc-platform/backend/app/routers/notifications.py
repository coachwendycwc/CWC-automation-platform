from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.services.auth_service import require_staff

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> dict:
    """My notifications, newest first, with the unread count for the badge."""
    rows = (
        await db.execute(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(min(limit, 200))
        )
    ).scalars().all()

    unread_count = (
        await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == current_user.id,
                Notification.read_at.is_(None),
            )
        )
    ).scalar_one()

    return {
        "unread_count": unread_count,
        "items": [
            {
                "id": n.id,
                "kind": n.kind,
                "message": n.message,
                "task_id": n.task_id,
                "read": n.read_at is not None,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ],
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> dict:
    """Mark one of my notifications read."""
    notification = (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read_at = datetime.utcnow()
    await db.commit()
    return {"id": notification.id, "read": True}


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> dict:
    """Clear my unread badge."""
    rows = (
        await db.execute(
            select(Notification).where(
                Notification.user_id == current_user.id,
                Notification.read_at.is_(None),
            )
        )
    ).scalars().all()
    now = datetime.utcnow()
    for notification in rows:
        notification.read_at = now
    await db.commit()
    return {"marked_read": len(rows)}
