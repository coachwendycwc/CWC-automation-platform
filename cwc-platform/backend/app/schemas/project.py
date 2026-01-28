from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

ProjectType = Literal["coaching", "workshop", "consulting", "speaking"]
ProjectStatus = Literal["planning", "active", "paused", "completed", "cancelled"]
TaskStatus = Literal["todo", "in_progress", "review", "completed", "blocked"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


# Time Entry schemas
class TimeEntryBase(BaseModel):
    description: Optional[str] = None
    hours: Decimal
    entry_date: date


class TimeEntryCreate(TimeEntryBase):
    created_by: Optional[str] = None


class TimeEntryRead(TimeEntryBase):
    id: str
    task_id: str
    created_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Task schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = "medium"
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = None
    notes: Optional[str] = None


class TaskCreate(TaskBase):
    project_id: str
    parent_task_id: Optional[str] = None
    depends_on_task_id: Optional[str] = None
    order_index: int = 0


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = None
    notes: Optional[str] = None
    order_index: Optional[int] = None
    depends_on_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None


class TaskRead(BaseModel):
    id: str
    task_number: str
    project_id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = None
    actual_hours: Decimal
    order_index: int
    depends_on_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskList(BaseModel):
    id: str
    task_number: str
    project_id: str
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = None
    actual_hours: Decimal
    order_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(TaskRead):
    """Extended task with time entries"""
    time_entries: list[TimeEntryRead] = []
    project_title: Optional[str] = None
    project_number: Optional[str] = None


class TaskReorderItem(BaseModel):
    id: str
    status: Optional[TaskStatus] = None
    order_index: int


class TaskReorderRequest(BaseModel):
    task_updates: list[TaskReorderItem]


class TaskStats(BaseModel):
    total_tasks: int
    todo_count: int
    in_progress_count: int
    review_count: int
    completed_count: int
    blocked_count: int
    estimated_hours: float
    actual_hours: float


# Project Activity Log schemas
class ProjectActivityLogRead(BaseModel):
    id: str
    project_id: str
    task_id: Optional[str] = None
    action: str
    actor: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Project Template schemas
class TaskTemplateItem(BaseModel):
    title: str
    description: Optional[str] = None
    estimated_hours: Optional[float] = None
    order_index: int = 0


class ProjectTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: ProjectType = "coaching"
    default_duration_days: int = 30
    estimated_hours: Optional[Decimal] = None


class ProjectTemplateCreate(ProjectTemplateBase):
    task_templates: list[TaskTemplateItem] = []


class ProjectTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    default_duration_days: Optional[int] = None
    estimated_hours: Optional[Decimal] = None
    task_templates: Optional[list[TaskTemplateItem]] = None
    is_active: Optional[bool] = None


class ProjectTemplateRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_type: str
    default_duration_days: int
    estimated_hours: Optional[Decimal] = None
    task_templates: list[dict] = []
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectTemplateList(BaseModel):
    id: str
    name: str
    project_type: str
    default_duration_days: int
    task_count: int = 0
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# Project schemas
class ProjectBase(BaseModel):
    contact_id: str
    organization_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    project_type: ProjectType = "coaching"


class ProjectCreate(ProjectBase):
    template_id: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    budget_amount: Optional[Decimal] = None
    estimated_hours: Optional[Decimal] = None
    linked_contract_id: Optional[str] = None
    linked_invoice_id: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    budget_amount: Optional[Decimal] = None
    estimated_hours: Optional[Decimal] = None
    linked_contract_id: Optional[str] = None
    linked_invoice_id: Optional[str] = None
    client_visible: Optional[bool] = None


class ProjectRead(BaseModel):
    id: str
    project_number: str
    contact_id: str
    organization_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    project_type: str
    status: str
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    budget_amount: Optional[Decimal] = None
    estimated_hours: Optional[Decimal] = None
    linked_contract_id: Optional[str] = None
    linked_invoice_id: Optional[str] = None
    template_id: Optional[str] = None
    progress_percent: int
    view_token: str
    client_visible: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    id: str
    project_number: str
    title: str
    project_type: str
    status: str
    contact_id: str
    contact_name: Optional[str] = None
    organization_name: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    progress_percent: int
    task_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectRead):
    """Extended project with related data"""
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    organization_name: Optional[str] = None
    template_name: Optional[str] = None
    linked_contract_number: Optional[str] = None
    linked_invoice_number: Optional[str] = None
    tasks: list[TaskRead] = []
    activity_logs: list[ProjectActivityLogRead] = []
    task_stats: Optional[TaskStats] = None


class ProjectStats(BaseModel):
    total_projects: int
    planning_count: int
    active_count: int
    paused_count: int
    completed_count: int
    total_estimated_hours: float
    total_actual_hours: float
    started_this_month: int
    completed_this_month: int


class ProjectComplete(BaseModel):
    """Request to mark project as completed"""
    pass


class ProjectDuplicate(BaseModel):
    """Request to duplicate a project"""
    new_title: Optional[str] = None
    include_tasks: bool = True


# Public project view (for client portal)
class ProjectPublic(BaseModel):
    project_number: str
    title: str
    description: Optional[str] = None
    status: str
    progress_percent: int
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    contact_name: str
    organization_name: Optional[str] = None
    tasks: list[TaskList] = []

    model_config = ConfigDict(from_attributes=True)
