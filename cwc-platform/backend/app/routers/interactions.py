from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.models.interaction import Interaction
from app.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    InteractionList,
)

router = APIRouter(prefix="/interactions", tags=["Interactions"])


@router.get("/contact/{contact_id}", response_model=InteractionList)
async def list_contact_interactions(
    contact_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all interactions for a contact."""
    # Verify contact exists
    contact_result = await db.execute(select(Contact).where(Contact.id == contact_id))
    if not contact_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    # Get interactions
    query = (
        select(Interaction)
        .where(Interaction.contact_id == contact_id)
        .order_by(Interaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    interactions = result.scalars().all()

    # Get total count
    count_result = await db.scalar(
        select(func.count()).where(Interaction.contact_id == contact_id)
    )

    return InteractionList(
        items=[InteractionResponse.model_validate(i) for i in interactions],
        total=count_result or 0,
    )


@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction_data: InteractionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new interaction (note, call, meeting, etc.)."""
    # Verify contact exists
    contact_result = await db.execute(
        select(Contact).where(Contact.id == interaction_data.contact_id)
    )
    if not contact_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact not found",
        )

    interaction = Interaction(
        **interaction_data.model_dump(),
        created_by=current_user.id,
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return InteractionResponse.model_validate(interaction)


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single interaction by ID."""
    result = await db.execute(
        select(Interaction).where(Interaction.id == interaction_id)
    )
    interaction = result.scalar_one_or_none()

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )

    return InteractionResponse.model_validate(interaction)


@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(
    interaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an interaction."""
    result = await db.execute(
        select(Interaction).where(Interaction.id == interaction_id)
    )
    interaction = result.scalar_one_or_none()

    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )

    await db.delete(interaction)
    await db.commit()
