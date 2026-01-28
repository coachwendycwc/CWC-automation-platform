"""Goals router for admin dashboard."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.client_goal import ClientGoal
from app.models.goal_milestone import GoalMilestone
from app.models.contact import Contact
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalList,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse,
)

router = APIRouter(prefix="/api/goals", tags=["Goals"])


def goal_to_response(goal: ClientGoal) -> GoalResponse:
    """Convert goal model to response."""
    contact_name = ""
    if goal.contact:
        contact_name = f"{goal.contact.first_name} {goal.contact.last_name or ''}".strip()

    return GoalResponse(
        id=goal.id,
        contact_id=goal.contact_id,
        contact_name=contact_name,
        title=goal.title,
        description=goal.description,
        category=goal.category,
        status=goal.status,
        target_date=goal.target_date,
        completed_at=goal.completed_at,
        progress_percent=goal.progress_percent,
        milestones=[
            MilestoneResponse(
                id=m.id,
                goal_id=m.goal_id,
                title=m.title,
                description=m.description,
                target_date=m.target_date,
                is_completed=m.is_completed,
                completed_at=m.completed_at,
                sort_order=m.sort_order,
                created_at=m.created_at,
            )
            for m in goal.milestones
        ],
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


@router.get("", response_model=GoalList)
async def list_goals(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contact_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all goals with filters."""
    query = select(ClientGoal).options(
        selectinload(ClientGoal.contact),
        selectinload(ClientGoal.milestones),
    )

    # Apply filters
    if contact_id:
        query = query.where(ClientGoal.contact_id == contact_id)
    if status_filter:
        query = query.where(ClientGoal.status == status_filter)
    if category:
        query = query.where(ClientGoal.category == category)

    # Get total count
    count_query = select(func.count(ClientGoal.id))
    if contact_id:
        count_query = count_query.where(ClientGoal.contact_id == contact_id)
    if status_filter:
        count_query = count_query.where(ClientGoal.status == status_filter)
    if category:
        count_query = count_query.where(ClientGoal.category == category)

    total = await db.scalar(count_query) or 0

    # Get paginated results
    query = query.offset((page - 1) * size).limit(size).order_by(
        ClientGoal.created_at.desc()
    )
    result = await db.execute(query)
    goals = result.scalars().unique().all()

    return GoalList(
        items=[goal_to_response(g) for g in goals],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single goal."""
    result = await db.execute(
        select(ClientGoal)
        .options(
            selectinload(ClientGoal.contact),
            selectinload(ClientGoal.milestones),
        )
        .where(ClientGoal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return goal_to_response(goal)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    data: GoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new goal for a client."""
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

    # Create goal
    goal = ClientGoal(
        contact_id=data.contact_id,
        title=data.title,
        description=data.description,
        category=data.category,
        target_date=data.target_date,
        status="active",
    )
    db.add(goal)
    await db.flush()

    # Create milestones if provided
    if data.milestones:
        for i, m in enumerate(data.milestones):
            milestone = GoalMilestone(
                goal_id=goal.id,
                title=m.title,
                description=m.description,
                target_date=m.target_date,
                sort_order=m.sort_order if m.sort_order is not None else i,
            )
            db.add(milestone)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ClientGoal)
        .options(
            selectinload(ClientGoal.contact),
            selectinload(ClientGoal.milestones),
        )
        .where(ClientGoal.id == goal.id)
    )
    goal = result.scalar_one()

    return goal_to_response(goal)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    data: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a goal."""
    result = await db.execute(
        select(ClientGoal)
        .options(
            selectinload(ClientGoal.contact),
            selectinload(ClientGoal.milestones),
        )
        .where(ClientGoal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    # Update fields
    if data.title is not None:
        goal.title = data.title
    if data.description is not None:
        goal.description = data.description
    if data.category is not None:
        goal.category = data.category
    if data.target_date is not None:
        goal.target_date = data.target_date
    if data.status is not None:
        goal.status = data.status
        if data.status == "completed":
            goal.completed_at = datetime.utcnow()
        elif data.status in ["active", "abandoned"]:
            goal.completed_at = None

    await db.commit()
    await db.refresh(goal)

    return goal_to_response(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a goal."""
    result = await db.execute(
        select(ClientGoal).where(ClientGoal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    await db.delete(goal)
    await db.commit()


# Milestone endpoints
@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def add_milestone(
    goal_id: str,
    data: MilestoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a milestone to a goal."""
    result = await db.execute(
        select(ClientGoal)
        .options(selectinload(ClientGoal.milestones))
        .where(ClientGoal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    # Determine sort order
    max_order = max((m.sort_order for m in goal.milestones), default=-1)

    milestone = GoalMilestone(
        goal_id=goal_id,
        title=data.title,
        description=data.description,
        target_date=data.target_date,
        sort_order=data.sort_order if data.sort_order is not None else max_order + 1,
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)

    return MilestoneResponse(
        id=milestone.id,
        goal_id=milestone.goal_id,
        title=milestone.title,
        description=milestone.description,
        target_date=milestone.target_date,
        is_completed=milestone.is_completed,
        completed_at=milestone.completed_at,
        sort_order=milestone.sort_order,
        created_at=milestone.created_at,
    )


@router.put("/{goal_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    goal_id: str,
    milestone_id: str,
    data: MilestoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a milestone."""
    result = await db.execute(
        select(GoalMilestone)
        .where(GoalMilestone.id == milestone_id)
        .where(GoalMilestone.goal_id == goal_id)
    )
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    # Update fields
    if data.title is not None:
        milestone.title = data.title
    if data.description is not None:
        milestone.description = data.description
    if data.target_date is not None:
        milestone.target_date = data.target_date
    if data.sort_order is not None:
        milestone.sort_order = data.sort_order
    if data.is_completed is not None:
        milestone.is_completed = data.is_completed
        if data.is_completed:
            milestone.completed_at = datetime.utcnow()
        else:
            milestone.completed_at = None

    await db.commit()
    await db.refresh(milestone)

    return MilestoneResponse(
        id=milestone.id,
        goal_id=milestone.goal_id,
        title=milestone.title,
        description=milestone.description,
        target_date=milestone.target_date,
        is_completed=milestone.is_completed,
        completed_at=milestone.completed_at,
        sort_order=milestone.sort_order,
        created_at=milestone.created_at,
    )


@router.delete("/{goal_id}/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    goal_id: str,
    milestone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a milestone."""
    result = await db.execute(
        select(GoalMilestone)
        .where(GoalMilestone.id == milestone_id)
        .where(GoalMilestone.goal_id == goal_id)
    )
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    await db.delete(milestone)
    await db.commit()
