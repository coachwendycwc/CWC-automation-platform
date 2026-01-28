"""Action items router for admin dashboard."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.client_action_item import ClientActionItem
from app.models.contact import Contact
from app.schemas.action_item import (
    ActionItemCreate,
    ActionItemUpdate,
    ActionItemResponse,
    ActionItemList,
)

router = APIRouter(prefix="/action-items", tags=["Action Items"])


def action_item_to_response(item: ClientActionItem) -> ActionItemResponse:
    """Convert action item model to response."""
    contact_name = ""
    if item.contact:
        contact_name = f"{item.contact.first_name} {item.contact.last_name or ''}".strip()

    return ActionItemResponse(
        id=item.id,
        contact_id=item.contact_id,
        contact_name=contact_name,
        session_id=item.session_id,
        title=item.title,
        description=item.description,
        due_date=item.due_date,
        priority=item.priority,
        status=item.status,
        completed_at=item.completed_at,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=ActionItemList)
async def list_action_items(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contact_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all action items with filters."""
    query = select(ClientActionItem).options(selectinload(ClientActionItem.contact))

    # Apply filters
    if contact_id:
        query = query.where(ClientActionItem.contact_id == contact_id)
    if status_filter:
        query = query.where(ClientActionItem.status == status_filter)
    if priority:
        query = query.where(ClientActionItem.priority == priority)

    # Get total count
    count_query = select(func.count(ClientActionItem.id))
    if contact_id:
        count_query = count_query.where(ClientActionItem.contact_id == contact_id)
    if status_filter:
        count_query = count_query.where(ClientActionItem.status == status_filter)
    if priority:
        count_query = count_query.where(ClientActionItem.priority == priority)

    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.offset((page - 1) * size).limit(size).order_by(
        ClientActionItem.due_date.asc().nullslast(),
        ClientActionItem.created_at.desc(),
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return ActionItemList(
        items=[action_item_to_response(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{item_id}", response_model=ActionItemResponse)
async def get_action_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single action item."""
    result = await db.execute(
        select(ClientActionItem)
        .options(selectinload(ClientActionItem.contact))
        .where(ClientActionItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    return action_item_to_response(item)


@router.post("", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_action_item(
    data: ActionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new action item for a client."""
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

    # Create action item
    item = ClientActionItem(
        contact_id=data.contact_id,
        session_id=data.session_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        priority=data.priority,
        status="pending",
        created_by="coach",
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Reload with contact
    result = await db.execute(
        select(ClientActionItem)
        .options(selectinload(ClientActionItem.contact))
        .where(ClientActionItem.id == item.id)
    )
    item = result.scalar_one()

    return action_item_to_response(item)


@router.put("/{item_id}", response_model=ActionItemResponse)
async def update_action_item(
    item_id: str,
    data: ActionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an action item."""
    result = await db.execute(
        select(ClientActionItem)
        .options(selectinload(ClientActionItem.contact))
        .where(ClientActionItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    # Update fields
    if data.title is not None:
        item.title = data.title
    if data.description is not None:
        item.description = data.description
    if data.due_date is not None:
        item.due_date = data.due_date
    if data.priority is not None:
        item.priority = data.priority
    if data.status is not None:
        item.status = data.status
        if data.status == "completed":
            item.completed_at = datetime.utcnow()
        elif data.status in ["pending", "in_progress"]:
            item.completed_at = None

    await db.commit()
    await db.refresh(item)

    return action_item_to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an action item."""
    result = await db.execute(
        select(ClientActionItem).where(ClientActionItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    await db.delete(item)
    await db.commit()
