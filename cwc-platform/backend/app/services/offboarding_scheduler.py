"""Background scheduler for offboarding automation."""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.offboarding import OffboardingWorkflow
from app.services.offboarding_service import OffboardingService


def make_naive(dt: datetime) -> datetime:
    """Convert datetime to timezone-naive UTC."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


class OffboardingScheduler:
    """Background scheduler for automated offboarding tasks."""

    def __init__(self):
        self.running = False
        self.task = None
        self.check_interval = 3600  # Check every hour

    async def start(self):
        """Start the scheduler."""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        print("Offboarding scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("Offboarding scheduler stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_and_send_surveys()
                await self._check_and_request_testimonials()
            except Exception as e:
                print(f"Error in offboarding scheduler: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_and_send_surveys(self):
        """Check for workflows that need survey emails sent."""
        async with async_session_maker() as db:
            service = OffboardingService(db)

            # Find workflows where:
            # - send_survey is True
            # - survey not yet sent
            # - initiated_at + delay_days has passed
            # - status is in_progress or pending
            now = datetime.utcnow()

            query = select(OffboardingWorkflow).where(
                and_(
                    OffboardingWorkflow.send_survey == True,
                    OffboardingWorkflow.survey_sent_at.is_(None),
                    OffboardingWorkflow.status.in_(["pending", "in_progress"]),
                )
            )

            result = await db.execute(query)
            workflows = result.scalars().all()

            for workflow in workflows:
                # Default delay is 3 days
                delay_days = 3

                # Check if enough time has passed (handle timezone-naive/aware comparison)
                initiated = make_naive(workflow.initiated_at)
                send_after = initiated + timedelta(days=delay_days)
                if now >= send_after:
                    try:
                        await service.send_survey(workflow.id)
                        print(f"Auto-sent survey for workflow {workflow.id}")
                    except Exception as e:
                        print(f"Failed to auto-send survey for {workflow.id}: {e}")

    async def _check_and_request_testimonials(self):
        """Check for workflows that need testimonial requests sent."""
        async with async_session_maker() as db:
            service = OffboardingService(db)

            # Find workflows where:
            # - request_testimonial is True
            # - testimonial not yet requested
            # - survey completed (we wait for survey first)
            # - initiated_at + delay_days has passed
            # - status is in_progress
            now = datetime.utcnow()

            query = select(OffboardingWorkflow).where(
                and_(
                    OffboardingWorkflow.request_testimonial == True,
                    OffboardingWorkflow.testimonial_requested_at.is_(None),
                    OffboardingWorkflow.survey_completed_at.isnot(None),  # Survey done first
                    OffboardingWorkflow.status.in_(["pending", "in_progress"]),
                )
            )

            result = await db.execute(query)
            workflows = result.scalars().all()

            for workflow in workflows:
                # Default delay is 7 days from initiation
                delay_days = 7

                # Check if enough time has passed (handle timezone-naive/aware comparison)
                initiated = make_naive(workflow.initiated_at)
                send_after = initiated + timedelta(days=delay_days)
                if now >= send_after:
                    try:
                        await service.request_testimonial(workflow.id)
                        print(f"Auto-requested testimonial for workflow {workflow.id}")
                    except Exception as e:
                        print(f"Failed to auto-request testimonial for {workflow.id}: {e}")


# Singleton instance
offboarding_scheduler = OffboardingScheduler()
