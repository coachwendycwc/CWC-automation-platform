"""
Project service for project and task operations.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.project_template import ProjectTemplate
from app.models.project_activity_log import ProjectActivityLog


class ProjectService:
    """Service for project and task operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_project_number(self) -> str:
        """
        Generate unique project number in format: PRJ-YYYY-###
        Example: PRJ-2025-001, PRJ-2025-002, etc.
        """
        year = datetime.now().year
        prefix = f"PRJ-{year}-"

        result = await self.db.execute(
            select(Project.project_number)
            .where(Project.project_number.like(f"{prefix}%"))
            .order_by(Project.project_number.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()

        if last_number:
            last_num = int(last_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:03d}"

    async def generate_task_number(self) -> str:
        """
        Generate unique task number in format: TSK-YYYY-###
        Example: TSK-2025-001, TSK-2025-002, etc.
        """
        year = datetime.now().year
        prefix = f"TSK-{year}-"

        result = await self.db.execute(
            select(Task.task_number)
            .where(Task.task_number.like(f"{prefix}%"))
            .order_by(Task.task_number.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()

        if last_number:
            last_num = int(last_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:03d}"

    async def calculate_progress(self, project_id: str) -> int:
        """
        Calculate project progress percentage based on completed tasks.
        Returns 0 if no tasks exist.
        """
        result = await self.db.execute(
            select(
                func.count().filter(Task.status == "completed").label("completed"),
                func.count().label("total"),
            )
            .where(Task.project_id == project_id)
        )
        counts = result.one()

        if counts.total == 0:
            return 0

        return int((counts.completed / counts.total) * 100)

    async def update_project_progress(self, project_id: str) -> int:
        """Update and return the project's progress percentage."""
        progress = await self.calculate_progress(project_id)

        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if project:
            project.progress_percent = progress
            await self.db.flush()

        return progress

    async def create_from_template(
        self,
        template_id: str,
        contact_id: str,
        title: str,
        organization_id: Optional[str] = None,
        start_date: Optional[date] = None,
        description: Optional[str] = None,
        budget_amount: Optional[Decimal] = None,
    ) -> Project:
        """
        Create a new project from a template with pre-defined tasks.
        """
        # Get the template
        result = await self.db.execute(
            select(ProjectTemplate).where(ProjectTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Generate project number
        project_number = await self.generate_project_number()

        # Calculate end date from template duration
        actual_start = start_date or date.today()
        target_end = actual_start + timedelta(days=template.default_duration_days)

        # Create project
        project = Project(
            id=str(uuid.uuid4()),
            project_number=project_number,
            contact_id=contact_id,
            organization_id=organization_id,
            title=title,
            description=description or template.description,
            project_type=template.project_type,
            status="planning",
            start_date=actual_start,
            target_end_date=target_end,
            budget_amount=budget_amount,
            estimated_hours=template.estimated_hours,
            template_id=template_id,
        )
        self.db.add(project)
        await self.db.flush()

        # Create tasks from template
        if template.task_templates:
            for task_template in template.task_templates:
                task_number = await self.generate_task_number()
                task = Task(
                    id=str(uuid.uuid4()),
                    task_number=task_number,
                    project_id=project.id,
                    title=task_template.get("title", "Untitled Task"),
                    description=task_template.get("description"),
                    estimated_hours=Decimal(str(task_template.get("estimated_hours", 0))) if task_template.get("estimated_hours") else None,
                    order_index=task_template.get("order_index", 0),
                    status="todo",
                    priority="medium",
                )
                self.db.add(task)

        await self.db.flush()

        # Log activity
        await self.log_activity(
            project_id=project.id,
            action="created",
            details={"from_template": template.name, "template_id": template_id},
        )

        return project

    async def log_activity(
        self,
        project_id: str,
        action: str,
        task_id: Optional[str] = None,
        actor: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> ProjectActivityLog:
        """Create an activity log entry for a project or task action."""
        log = ProjectActivityLog(
            id=str(uuid.uuid4()),
            project_id=project_id,
            task_id=task_id,
            action=action,
            actor=actor,
            details=details,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def update_task_hours(self, task_id: str) -> Decimal:
        """
        Sum all time entries for a task and update actual_hours.
        Returns the new total.
        """
        result = await self.db.execute(
            select(func.sum(TimeEntry.hours))
            .where(TimeEntry.task_id == task_id)
        )
        total = result.scalar_one() or Decimal("0")

        # Update the task
        task_result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task_result.scalar_one_or_none()

        if task:
            task.actual_hours = total
            await self.db.flush()

        return total

    async def get_stats(self) -> dict:
        """Get project statistics for dashboard."""
        # Get counts by status
        count_result = await self.db.execute(
            select(
                func.count().filter(Project.status != "cancelled").label("total"),
                func.count().filter(Project.status == "planning").label("planning"),
                func.count().filter(Project.status == "active").label("active"),
                func.count().filter(Project.status == "paused").label("paused"),
                func.count().filter(Project.status == "completed").label("completed"),
            )
        )
        counts = count_result.one()

        # Get total estimated and actual hours
        hours_result = await self.db.execute(
            select(
                func.sum(Project.estimated_hours).label("total_estimated"),
            )
            .where(Project.status != "cancelled")
        )
        hours = hours_result.one()

        # Get total actual hours from tasks
        task_hours_result = await self.db.execute(
            select(func.sum(Task.actual_hours))
        )
        total_actual_hours = task_hours_result.scalar_one() or Decimal("0")

        # Projects started this month
        first_of_month = date.today().replace(day=1)
        started_month_result = await self.db.execute(
            select(func.count())
            .where(
                and_(
                    Project.status != "cancelled",
                    Project.created_at >= datetime.combine(first_of_month, datetime.min.time()),
                )
            )
        )
        started_this_month = started_month_result.scalar_one()

        # Completed this month
        completed_month_result = await self.db.execute(
            select(func.count())
            .where(
                and_(
                    Project.status == "completed",
                    Project.actual_end_date >= first_of_month,
                )
            )
        )
        completed_this_month = completed_month_result.scalar_one()

        return {
            "total_projects": counts.total,
            "planning_count": counts.planning,
            "active_count": counts.active,
            "paused_count": counts.paused,
            "completed_count": counts.completed,
            "total_estimated_hours": float(hours.total_estimated or 0),
            "total_actual_hours": float(total_actual_hours),
            "started_this_month": started_this_month,
            "completed_this_month": completed_this_month,
        }

    async def get_task_stats(self, project_id: Optional[str] = None) -> dict:
        """Get task statistics, optionally filtered by project."""
        query = select(
            func.count().label("total"),
            func.count().filter(Task.status == "todo").label("todo"),
            func.count().filter(Task.status == "in_progress").label("in_progress"),
            func.count().filter(Task.status == "review").label("review"),
            func.count().filter(Task.status == "completed").label("completed"),
            func.count().filter(Task.status == "blocked").label("blocked"),
            func.sum(Task.estimated_hours).label("estimated_hours"),
            func.sum(Task.actual_hours).label("actual_hours"),
        )

        if project_id:
            query = query.where(Task.project_id == project_id)

        result = await self.db.execute(query)
        stats = result.one()

        return {
            "total_tasks": stats.total,
            "todo_count": stats.todo,
            "in_progress_count": stats.in_progress,
            "review_count": stats.review,
            "completed_count": stats.completed,
            "blocked_count": stats.blocked,
            "estimated_hours": float(stats.estimated_hours or 0),
            "actual_hours": float(stats.actual_hours or 0),
        }

    async def complete_project(self, project_id: str, actor: Optional[str] = None) -> Project:
        """Mark a project as completed."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        project.status = "completed"
        project.actual_end_date = date.today()

        await self.log_activity(
            project_id=project_id,
            action="completed",
            actor=actor,
            details={"completed_at": datetime.now().isoformat()},
        )

        await self.db.flush()
        return project

    async def complete_task(self, task_id: str, actor: Optional[str] = None) -> Task:
        """Mark a task as completed and update project progress."""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = "completed"
        task.completed_at = datetime.now()

        # Log activity
        await self.log_activity(
            project_id=task.project_id,
            task_id=task_id,
            action="task_completed",
            actor=actor,
            details={"task_title": task.title},
        )

        # Update project progress
        await self.update_project_progress(task.project_id)

        await self.db.flush()
        return task

    async def duplicate_project(
        self,
        project_id: str,
        new_title: Optional[str] = None,
        include_tasks: bool = True,
    ) -> Project:
        """
        Duplicate an existing project with optional task copying.
        Returns the new project.
        """
        # Get original project with tasks
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        original = result.scalar_one_or_none()

        if not original:
            raise ValueError(f"Project {project_id} not found")

        # Generate new project number
        project_number = await self.generate_project_number()

        # Create new project
        new_project = Project(
            id=str(uuid.uuid4()),
            project_number=project_number,
            contact_id=original.contact_id,
            organization_id=original.organization_id,
            title=new_title or f"{original.title} (Copy)",
            description=original.description,
            project_type=original.project_type,
            status="planning",
            budget_amount=original.budget_amount,
            estimated_hours=original.estimated_hours,
            template_id=original.template_id,
        )
        self.db.add(new_project)
        await self.db.flush()

        # Copy tasks if requested
        if include_tasks:
            for original_task in original.tasks:
                task_number = await self.generate_task_number()
                new_task = Task(
                    id=str(uuid.uuid4()),
                    task_number=task_number,
                    project_id=new_project.id,
                    title=original_task.title,
                    description=original_task.description,
                    status="todo",
                    priority=original_task.priority,
                    estimated_hours=original_task.estimated_hours,
                    order_index=original_task.order_index,
                )
                self.db.add(new_task)

        await self.db.flush()

        # Log activity
        await self.log_activity(
            project_id=new_project.id,
            action="created",
            details={"duplicated_from": original.project_number},
        )

        return new_project

    async def reorder_tasks(self, updates: list[dict]) -> None:
        """
        Batch update task order and status for Kanban drag-drop.
        Updates is a list of {"id": str, "status": str, "order_index": int}
        """
        for update in updates:
            result = await self.db.execute(
                select(Task).where(Task.id == update["id"])
            )
            task = result.scalar_one_or_none()

            if task:
                old_status = task.status
                task.status = update.get("status", task.status)
                task.order_index = update.get("order_index", task.order_index)

                # If status changed to completed, set completed_at
                if task.status == "completed" and old_status != "completed":
                    task.completed_at = datetime.now()
                elif task.status != "completed":
                    task.completed_at = None

        await self.db.flush()
