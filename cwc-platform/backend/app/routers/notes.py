"""Notes router for admin dashboard."""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.email_service import email_service
from app.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)
from app.models.client_note import ClientNote
from app.models.contact import Contact
from app.schemas.note import (
    NoteCreate,
    NoteReply,
    NoteResponse,
    NoteList,
    UnreadCount,
)

router = APIRouter(prefix="/notes", tags=["Notes"])


def note_to_response(note: ClientNote, include_replies: bool = False) -> NoteResponse:
    """Convert note model to response with contact name."""
    contact_name = ""
    if note.contact:
        contact_name = f"{note.contact.first_name} {note.contact.last_name or ''}".strip()

    replies = []
    if include_replies and note.replies:
        replies = [note_to_response(r, include_replies=False) for r in note.replies]

    return NoteResponse(
        id=note.id,
        contact_id=note.contact_id,
        contact_name=contact_name,
        content=note.content,
        direction=note.direction,
        parent_id=note.parent_id,
        is_read=note.is_read,
        read_at=note.read_at,
        created_at=note.created_at,
        replies=replies,
    )


@router.get("", response_model=NoteList)
async def list_notes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contact_id: Optional[str] = None,
    direction: Optional[str] = None,
    is_read: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all notes with filters. Only shows top-level notes (not replies)."""
    query = select(ClientNote).options(
        selectinload(ClientNote.contact),
        selectinload(ClientNote.replies).selectinload(ClientNote.contact),
    ).where(ClientNote.parent_id.is_(None))  # Only top-level notes

    # Apply filters
    if contact_id:
        query = query.where(ClientNote.contact_id == contact_id)
    if direction:
        query = query.where(ClientNote.direction == direction)
    if is_read is not None:
        query = query.where(ClientNote.is_read == is_read)
    if search:
        query = query.where(ClientNote.content.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count(ClientNote.id)).where(ClientNote.parent_id.is_(None))
    if contact_id:
        count_query = count_query.where(ClientNote.contact_id == contact_id)
    if direction:
        count_query = count_query.where(ClientNote.direction == direction)
    if is_read is not None:
        count_query = count_query.where(ClientNote.is_read == is_read)
    if search:
        count_query = count_query.where(ClientNote.content.ilike(f"%{search}%"))

    total = await db.scalar(count_query) or 0

    # Get paginated results, ordered by newest first
    query = query.offset((page - 1) * size).limit(size).order_by(ClientNote.created_at.desc())
    result = await db.execute(query)
    notes = result.scalars().all()

    return NoteList(
        items=[note_to_response(n, include_replies=True) for n in notes],
        total=total,
        page=page,
        size=size,
    )


@router.get("/unread-count", response_model=UnreadCount)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notes from clients."""
    count = await db.scalar(
        select(func.count(ClientNote.id)).where(
            and_(
                ClientNote.direction == "to_coach",
                ClientNote.is_read == False,
            )
        )
    )
    return UnreadCount(count=count or 0)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single note with replies."""
    result = await db.execute(
        select(ClientNote)
        .options(
            selectinload(ClientNote.contact),
            selectinload(ClientNote.replies).selectinload(ClientNote.contact),
        )
        .where(ClientNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return note_to_response(note, include_replies=True)


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new note to a client."""
    # Validate contact exists
    contact_result = await db.execute(
        select(Contact).where(Contact.id == data.contact_id)
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact not found",
        )

    # Create note
    note = ClientNote(
        contact_id=data.contact_id,
        content=data.content,
        direction="to_client",
        is_read=False,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    # Send email notification to client
    if contact.email:
        settings = get_settings()
        client_name = f"{contact.first_name} {contact.last_name or ''}".strip()
        portal_url = f"{settings.frontend_url}/client/notes"
        try:
            await email_service.send_note_to_client_notification(
                client_email=contact.email,
                client_name=client_name,
                note_content=data.content,
                portal_url=portal_url,
            )
        except Exception as e:
            logger.error(f"Failed to send note notification email to client: {e}")

    # Reload with contact
    result = await db.execute(
        select(ClientNote)
        .options(selectinload(ClientNote.contact))
        .where(ClientNote.id == note.id)
    )
    note = result.scalar_one()

    return note_to_response(note)


@router.post("/{note_id}/reply", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def reply_to_note(
    note_id: str,
    data: NoteReply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reply to a note."""
    # Get parent note with contact
    result = await db.execute(
        select(ClientNote)
        .options(selectinload(ClientNote.contact))
        .where(ClientNote.id == note_id)
    )
    parent_note = result.scalar_one_or_none()

    if not parent_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    # Create reply note
    reply = ClientNote(
        contact_id=parent_note.contact_id,
        content=data.content,
        direction="to_client",
        parent_id=note_id,
        is_read=False,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)

    # Send email notification to client
    contact = parent_note.contact
    if contact and contact.email:
        settings = get_settings()
        client_name = f"{contact.first_name} {contact.last_name or ''}".strip()
        portal_url = f"{settings.frontend_url}/client/notes"
        try:
            await email_service.send_note_to_client_notification(
                client_email=contact.email,
                client_name=client_name,
                note_content=data.content,
                portal_url=portal_url,
            )
        except Exception as e:
            logger.error(f"Failed to send reply notification email to client: {e}")

    # Reload with contact
    result = await db.execute(
        select(ClientNote)
        .options(selectinload(ClientNote.contact))
        .where(ClientNote.id == reply.id)
    )
    reply = result.scalar_one()

    return note_to_response(reply)


@router.put("/{note_id}/read", response_model=NoteResponse)
async def mark_as_read(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a note as read."""
    result = await db.execute(
        select(ClientNote)
        .options(selectinload(ClientNote.contact))
        .where(ClientNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    note.is_read = True
    note.read_at = datetime.utcnow()
    await db.commit()
    await db.refresh(note)

    return note_to_response(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a note and its replies."""
    result = await db.execute(
        select(ClientNote).where(ClientNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    await db.delete(note)
    await db.commit()
