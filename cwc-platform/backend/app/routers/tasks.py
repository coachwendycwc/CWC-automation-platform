"""
Task management router.
"""
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.schemas.project import (
    TaskCreate,
    TaskUpdate,
    TaskRead,
    TaskList,
    TaskDetail,
    TaskReorderRequest,
    TaskStats,
    TimeEntryCreate,
    TimeEntryRead,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api", tags=["tasks"])


# ============ Task CRUD ============

@router.get("/projects/{project_id}/tasks", response_model=list[TaskList])
async def list_project_tasks(
    project_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
) -> list[TaskList]:
    """List all tasks for a project."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = select(Task).where(Task.project_id == project_id)

    # Apply filters
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)

    query = query.order_by(Task.order_index, Task.created_at)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [TaskList.model_validate(task) for task in tasks]


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=201)
async def create_task(
    project_id: str,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Create a new task in a project."""
    service = ProjectService(db)

    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate task number
    task_number = await service.generate_task_number()

    task = Task(
        id=str(uuid.uuid4()),
        task_number=task_number,
        project_id=project_id,
        title=data.title,
        description=data.description,
        status="todo",
        priority=data.priority,
        assigned_to=data.assigned_to,
        due_date=data.due_date,
        estimated_hours=data.estimated_hours,
        order_index=data.order_index,
        depends_on_task_id=data.depends_on_task_id,
        parent_task_id=data.parent_task_id,
        notes=data.notes,
    )

    db.add(task)
    await db.flush()

    # Log activity
    await service.log_activity(
        project_id=project_id,
        task_id=task.id,
        action="task_added",
        details={"task_title": task.title},
    )

    await db.commit()
    await db.refresh(task)

    return TaskRead.model_validate(task)


@router.get("/tasks/stats", response_model=TaskStats)
async def get_task_stats(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db),
) -> TaskStats:
    """Get task statistics."""
    service = ProjectService(db)
    stats = await service.get_task_stats(project_id)
    return TaskStats(**stats)


@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskDetail:
    """Get a specific task with details."""
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.time_entries),
            selectinload(Task.project),
        )
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskDetail(
        id=task.id,
        task_number=task.task_number,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assigned_to=task.assigned_to,
        due_date=task.due_date,
        completed_at=task.completed_at,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        order_index=task.order_index,
        depends_on_task_id=task.depends_on_task_id,
        parent_task_id=task.parent_task_id,
        notes=task.notes,
        created_at=task.created_at,
        updated_at=task.updated_at,
        time_entries=[TimeEntryRead.model_validate(te) for te in task.time_entries],
        project_title=task.project.title if task.project else None,
        project_number=task.project.project_number if task.project else None,
    )


@router.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Update a task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    service = ProjectService(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Handle status change to completed
    if "status" in update_data:
        if update_data["status"] == "completed" and old_status != "completed":
            task.completed_at = datetime.now()
        elif update_data["status"] != "completed":
            task.completed_at = None

    # Log status change
    if "status" in update_data and update_data["status"] != old_status:
        await service.log_activity(
            project_id=task.project_id,
            task_id=task_id,
            action="task_status_changed",
            details={
                "old_status": old_status,
                "new_status": update_data["status"],
                "task_title": task.title,
            },
        )

        # Update project progress
        await service.update_project_progress(task.project_id)

    await db.commit()
    await db.refresh(task)

    return TaskRead.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project_id = task.project_id
    service = ProjectService(db)

    # Log activity
    await service.log_activity(
        project_id=project_id,
        action="task_deleted",
        details={"task_title": task.title, "task_number": task.task_number},
    )

    await db.delete(task)
    await db.commit()

    # Update project progress
    await service.update_project_progress(project_id)


@router.post("/tasks/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Mark a task as completed."""
    service = ProjectService(db)

    try:
        task = await service.complete_task(task_id)
        await db.commit()
        await db.refresh(task)
        return TaskRead.model_validate(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============ Kanban Reorder ============

@router.put("/tasks/reorder", response_model=dict)
async def reorder_tasks(
    data: TaskReorderRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Batch update task order and status for Kanban drag-drop."""
    service = ProjectService(db)

    updates = [
        {
            "id": item.id,
            "status": item.status,
            "order_index": item.order_index,
        }
        for item in data.task_updates
    ]

    await service.reorder_tasks(updates)

    # Update project progress for affected projects
    # Get unique project IDs from updated tasks
    task_ids = [item.id for item in data.task_updates]
    result = await db.execute(
        select(Task.project_id).where(Task.id.in_(task_ids)).distinct()
    )
    project_ids = result.scalars().all()

    for project_id in project_ids:
        await service.update_project_progress(project_id)

    await db.commit()

    return {"success": True, "updated_count": len(updates)}


# ============ Time Entries ============

@router.get("/tasks/{task_id}/time-entries", response_model=list[TimeEntryRead])
async def list_time_entries(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TimeEntryRead]:
    """List all time entries for a task."""
    # Verify task exists
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(TimeEntry)
        .where(TimeEntry.task_id == task_id)
        .order_by(TimeEntry.entry_date.desc(), TimeEntry.created_at.desc())
    )
    entries = result.scalars().all()

    return [TimeEntryRead.model_validate(entry) for entry in entries]


@router.post("/tasks/{task_id}/time-entries", response_model=TimeEntryRead, status_code=201)
async def create_time_entry(
    task_id: str,
    data: TimeEntryCreate,
    db: AsyncSession = Depends(get_db),
) -> TimeEntryRead:
    """Log time on a task."""
    # Verify task exists
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    service = ProjectService(db)

    entry = TimeEntry(
        id=str(uuid.uuid4()),
        task_id=task_id,
        description=data.description,
        hours=data.hours,
        entry_date=data.entry_date,
        created_by=data.created_by,
    )

    db.add(entry)
    await db.flush()

    # Update task actual hours
    await service.update_task_hours(task_id)

    # Log activity
    await service.log_activity(
        project_id=task.project_id,
        task_id=task_id,
        action="time_logged",
        details={
            "hours": float(data.hours),
            "description": data.description,
        },
    )

    await db.commit()
    await db.refresh(entry)

    return TimeEntryRead.model_validate(entry)


@router.delete("/time-entries/{entry_id}", status_code=204)
async def delete_time_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a time entry."""
    result = await db.execute(
        select(TimeEntry).where(TimeEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    task_id = entry.task_id
    service = ProjectService(db)

    await db.delete(entry)
    await db.flush()

    # Update task actual hours
    await service.update_task_hours(task_id)

    await db.commit()


# ============ Global Task List ============

@router.get("/tasks", response_model=list[TaskList])
async def list_all_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    search: Optional[str] = Query(None, description="Search task number or title"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[TaskList]:
    """List all tasks across projects."""
    query = select(Task)

    # Apply filters
    conditions = []
    if status:
        conditions.append(Task.status == status)
    if priority:
        conditions.append(Task.priority == priority)
    if assigned_to:
        conditions.append(Task.assigned_to.ilike(f"%{assigned_to}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Task.task_number.ilike(search_term),
                Task.title.ilike(search_term),
            )
        )

    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [TaskList.model_validate(task) for task in tasks]


