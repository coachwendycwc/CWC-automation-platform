"""Pydantic schemas for goals and milestones."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


# Milestone schemas
class MilestoneBase(BaseModel):
    """Base milestone schema."""

    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None


class MilestoneCreate(MilestoneBase):
    """Schema for creating a milestone."""

    sort_order: Optional[int] = 0


class MilestoneUpdate(BaseModel):
    """Schema for updating a milestone."""

    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    sort_order: Optional[int] = None
    is_completed: Optional[bool] = None


class MilestoneResponse(MilestoneBase):
    """Schema for milestone response."""

    id: str
    goal_id: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


# Goal schemas
class GoalBase(BaseModel):
    """Base goal schema."""

    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[date] = None


class GoalCreate(GoalBase):
    """Schema for creating a goal."""

    contact_id: str
    milestones: Optional[List[MilestoneCreate]] = None


class GoalUpdate(BaseModel):
    """Schema for updating a goal."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_date: Optional[date] = None
    status: Optional[str] = None


class GoalResponse(GoalBase):
    """Schema for goal response."""

    id: str
    contact_id: str
    contact_name: str = ""
    status: str
    completed_at: Optional[datetime] = None
    progress_percent: int = 0
    milestones: List[MilestoneResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoalList(BaseModel):
    """Schema for paginated goal list."""

    items: List[GoalResponse]
    total: int
    page: int
    size: int


# Client portal schemas
class ClientGoalResponse(BaseModel):
    """Schema for client portal goal response."""

    id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    target_date: Optional[date] = None
    progress_percent: int = 0
    milestones: List[MilestoneResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ClientMilestoneComplete(BaseModel):
    """Schema for completing a milestone."""

    is_completed: bool = True
