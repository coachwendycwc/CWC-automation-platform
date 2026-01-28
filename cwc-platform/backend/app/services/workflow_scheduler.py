"""
Unified workflow scheduler for email automation.
Handles all automated email sequences:
- Onboarding assessment reminders
- Welcome series after assessment
- Action item reminders
- Goal reminders
- Post-session follow-ups
- Weekly/monthly summaries
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.onboarding_assessment import OnboardingAssessment
from app.models.client_action_item import ClientActionItem
from app.models.client_goal import ClientGoal
from app.models.booking import Booking
from app.models.contact import Contact
from app.services.email_service import email_service
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WorkflowScheduler:
    """Unified scheduler for all email workflows."""

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        # Check every 15 minutes
        self.check_interval = 900

    async def start(self):
        """Start the workflow scheduler."""
        if self.is_running:
            logger.warning("Workflow scheduler already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("Workflow scheduler started")

    async def stop(self):
        """Stop the workflow scheduler."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Workflow scheduler stopped")

    async def _run_scheduler(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                await self._process_all_workflows()
            except Exception as e:
                logger.error(f"Error in workflow scheduler: {e}")

            await asyncio.sleep(self.check_interval)

    async def _process_all_workflows(self):
        """Process all workflow types."""
        async with async_session_maker() as db:
            # Onboarding workflows
            await self._process_assessment_reminders(db)
            await self._process_welcome_series(db)

            # Action item workflows
            await self._process_action_item_reminders(db)
            await self._process_overdue_action_items(db)

            # Goal workflows
            await self._process_goal_reminders(db)

            # Session workflows
            await self._process_post_session_followups(db)

            # Summary workflows (check day/time before sending)
            await self._process_weekly_summaries(db)
            await self._process_monthly_summaries(db)

    # =========================================================================
    # ONBOARDING ASSESSMENT REMINDERS
    # =========================================================================

    async def _process_assessment_reminders(self, db: AsyncSession):
        """Send reminders for incomplete assessments at Day 1, 3, 7."""
        now = datetime.utcnow()

        # Find assessments that need reminders
        result = await db.execute(
            select(OnboardingAssessment)
            .options(selectinload(OnboardingAssessment.contact))
            .where(
                and_(
                    OnboardingAssessment.completed_at.is_(None),
                    OnboardingAssessment.email_sent_at.isnot(None),
                )
            )
        )
        assessments = result.scalars().all()

        for assessment in assessments:
            if not assessment.contact or not assessment.contact.email:
                continue

            days_since_sent = (now - assessment.email_sent_at).days

            try:
                # Day 1 reminder
                if (
                    days_since_sent >= 1
                    and assessment.reminder_day1_sent_at is None
                ):
                    await self._send_assessment_reminder(assessment, day=1)
                    assessment.reminder_day1_sent_at = now
                    await db.commit()
                    logger.info(f"Sent Day 1 assessment reminder to {assessment.contact.email}")

                # Day 3 reminder
                elif (
                    days_since_sent >= 3
                    and assessment.reminder_day3_sent_at is None
                ):
                    await self._send_assessment_reminder(assessment, day=3)
                    assessment.reminder_day3_sent_at = now
                    await db.commit()
                    logger.info(f"Sent Day 3 assessment reminder to {assessment.contact.email}")

                # Day 7 reminder (final)
                elif (
                    days_since_sent >= 7
                    and assessment.reminder_day7_sent_at is None
                ):
                    await self._send_assessment_reminder(assessment, day=7)
                    assessment.reminder_day7_sent_at = now
                    await db.commit()
                    logger.info(f"Sent Day 7 assessment reminder to {assessment.contact.email}")

            except Exception as e:
                logger.error(f"Failed to send assessment reminder: {e}")
                await db.rollback()

    async def _send_assessment_reminder(self, assessment: OnboardingAssessment, day: int):
        """Send assessment reminder email."""
        contact = assessment.contact
        assessment_url = f"{settings.frontend_url}/onboarding/{assessment.token}"

        await email_service.send_assessment_reminder(
            contact=contact,
            assessment_url=assessment_url,
            day=day,
        )

    # =========================================================================
    # WELCOME SERIES (After Assessment Completed)
    # =========================================================================

    async def _process_welcome_series(self, db: AsyncSession):
        """Send welcome series emails after assessment completion."""
        now = datetime.utcnow()

        # Find completed assessments that need welcome emails
        result = await db.execute(
            select(OnboardingAssessment)
            .options(selectinload(OnboardingAssessment.contact))
            .where(OnboardingAssessment.completed_at.isnot(None))
        )
        assessments = result.scalars().all()

        for assessment in assessments:
            if not assessment.contact or not assessment.contact.email:
                continue

            days_since_completed = (now - assessment.completed_at).days

            try:
                # Day 0 welcome (immediate)
                if assessment.welcome_day0_sent_at is None:
                    await self._send_welcome_email(assessment, day=0)
                    assessment.welcome_day0_sent_at = now
                    await db.commit()
                    logger.info(f"Sent Day 0 welcome to {assessment.contact.email}")

                # Day 3 follow-up
                elif (
                    days_since_completed >= 3
                    and assessment.welcome_day3_sent_at is None
                ):
                    await self._send_welcome_email(assessment, day=3)
                    assessment.welcome_day3_sent_at = now
                    await db.commit()
                    logger.info(f"Sent Day 3 welcome to {assessment.contact.email}")

                # Day 7 check-in
                elif (
                    days_since_completed >= 7
                    and assessment.welcome_day7_sent_at is None
                ):
                    await self._send_welcome_email(assessment, day=7)
                    assessment.welcome_day7_sent_at = now
                    # Mark welcome series as completed on contact
                    assessment.contact.welcome_series_completed_at = now
                    await db.commit()
                    logger.info(f"Sent Day 7 welcome to {assessment.contact.email}")

            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")
                await db.rollback()

    async def _send_welcome_email(self, assessment: OnboardingAssessment, day: int):
        """Send welcome series email."""
        await email_service.send_welcome_series(
            contact=assessment.contact,
            day=day,
            assessment=assessment,
        )

    # =========================================================================
    # ACTION ITEM REMINDERS
    # =========================================================================

    async def _process_action_item_reminders(self, db: AsyncSession):
        """Send reminders for action items due within 3 days."""
        now = datetime.utcnow()
        today = date.today()
        reminder_window = today + timedelta(days=3)

        # Find action items due within 3 days that haven't been reminded
        result = await db.execute(
            select(ClientActionItem)
            .options(selectinload(ClientActionItem.contact))
            .where(
                and_(
                    ClientActionItem.status.in_(["pending", "in_progress"]),
                    ClientActionItem.due_date.isnot(None),
                    ClientActionItem.due_date <= reminder_window,
                    ClientActionItem.due_date >= today,
                    ClientActionItem.reminder_sent_at.is_(None),
                )
            )
        )
        action_items = result.scalars().all()

        for item in action_items:
            if not item.contact or not item.contact.email:
                continue

            try:
                days_until = (item.due_date - today).days
                await email_service.send_action_item_reminder(
                    contact=item.contact,
                    action_item=item,
                    days_until=days_until,
                )
                item.reminder_sent_at = now
                await db.commit()
                logger.info(f"Sent action item reminder to {item.contact.email} for '{item.title}'")

            except Exception as e:
                logger.error(f"Failed to send action item reminder: {e}")
                await db.rollback()

    async def _process_overdue_action_items(self, db: AsyncSession):
        """Send reminders for overdue action items."""
        now = datetime.utcnow()
        today = date.today()

        # Find overdue action items that haven't been reminded
        result = await db.execute(
            select(ClientActionItem)
            .options(selectinload(ClientActionItem.contact))
            .where(
                and_(
                    ClientActionItem.status.in_(["pending", "in_progress"]),
                    ClientActionItem.due_date.isnot(None),
                    ClientActionItem.due_date < today,
                    ClientActionItem.overdue_reminder_sent_at.is_(None),
                )
            )
        )
        action_items = result.scalars().all()

        for item in action_items:
            if not item.contact or not item.contact.email:
                continue

            try:
                days_overdue = (today - item.due_date).days
                await email_service.send_action_item_overdue(
                    contact=item.contact,
                    action_item=item,
                    days_overdue=days_overdue,
                )
                item.overdue_reminder_sent_at = now
                await db.commit()
                logger.info(f"Sent overdue reminder to {item.contact.email} for '{item.title}'")

            except Exception as e:
                logger.error(f"Failed to send overdue reminder: {e}")
                await db.rollback()

    # =========================================================================
    # GOAL REMINDERS
    # =========================================================================

    async def _process_goal_reminders(self, db: AsyncSession):
        """Send reminders for goals approaching target date."""
        now = datetime.utcnow()
        today = date.today()
        reminder_window = today + timedelta(days=7)

        # Find active goals with target dates within 7 days
        result = await db.execute(
            select(ClientGoal)
            .options(selectinload(ClientGoal.contact))
            .where(
                and_(
                    ClientGoal.status == "active",
                    ClientGoal.target_date.isnot(None),
                    ClientGoal.target_date <= reminder_window,
                    ClientGoal.target_date >= today,
                    ClientGoal.target_reminder_sent_at.is_(None),
                )
            )
        )
        goals = result.scalars().all()

        for goal in goals:
            if not goal.contact or not goal.contact.email:
                continue

            try:
                days_until = (goal.target_date - today).days
                await email_service.send_goal_reminder(
                    contact=goal.contact,
                    goal=goal,
                    days_until=days_until,
                )
                goal.target_reminder_sent_at = now
                await db.commit()
                logger.info(f"Sent goal reminder to {goal.contact.email} for '{goal.title}'")

            except Exception as e:
                logger.error(f"Failed to send goal reminder: {e}")
                await db.rollback()

    # =========================================================================
    # POST-SESSION FOLLOW-UPS
    # =========================================================================

    async def _process_post_session_followups(self, db: AsyncSession):
        """Send follow-up emails 24 hours after completed sessions."""
        now = datetime.utcnow()
        # Find sessions completed 24-48 hours ago
        window_start = now - timedelta(hours=48)
        window_end = now - timedelta(hours=24)

        result = await db.execute(
            select(Booking)
            .options(
                selectinload(Booking.contact),
                selectinload(Booking.booking_type),
            )
            .where(
                and_(
                    Booking.status == "completed",
                    Booking.end_time >= window_start,
                    Booking.end_time <= window_end,
                    Booking.post_session_sent_at.is_(None),
                )
            )
        )
        bookings = result.scalars().all()

        for booking in bookings:
            if not booking.contact or not booking.contact.email:
                continue

            try:
                await email_service.send_post_session_followup(
                    contact=booking.contact,
                    booking=booking,
                )
                booking.post_session_sent_at = now
                # Update last session date on contact
                booking.contact.last_session_at = booking.end_time
                await db.commit()
                logger.info(f"Sent post-session follow-up to {booking.contact.email}")

            except Exception as e:
                logger.error(f"Failed to send post-session follow-up: {e}")
                await db.rollback()

    # =========================================================================
    # WEEKLY SUMMARIES
    # =========================================================================

    async def _process_weekly_summaries(self, db: AsyncSession):
        """Send weekly progress summaries (Mondays at 9am)."""
        now = datetime.utcnow()

        # Only send on Mondays between 9-10am UTC
        if now.weekday() != 0 or now.hour != 9:
            return

        # Find contacts with portal enabled who haven't received summary this week
        week_ago = now - timedelta(days=7)

        result = await db.execute(
            select(Contact)
            .where(
                and_(
                    Contact.portal_enabled == True,
                    Contact.email.isnot(None),
                    or_(
                        Contact.weekly_summary_sent_at.is_(None),
                        Contact.weekly_summary_sent_at < week_ago,
                    ),
                )
            )
        )
        contacts = result.scalars().all()

        for contact in contacts:
            try:
                # Get summary data
                summary = await self._get_weekly_summary_data(db, contact)
                if summary["has_activity"]:
                    await email_service.send_weekly_summary(
                        contact=contact,
                        summary=summary,
                    )
                    contact.weekly_summary_sent_at = now
                    await db.commit()
                    logger.info(f"Sent weekly summary to {contact.email}")

            except Exception as e:
                logger.error(f"Failed to send weekly summary: {e}")
                await db.rollback()

    async def _get_weekly_summary_data(self, db: AsyncSession, contact: Contact) -> dict:
        """Gather data for weekly summary email."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        today = date.today()

        # Get action items
        action_result = await db.execute(
            select(ClientActionItem).where(
                ClientActionItem.contact_id == contact.id
            )
        )
        action_items = action_result.scalars().all()
        pending_items = [a for a in action_items if a.status in ["pending", "in_progress"]]
        completed_this_week = [a for a in action_items if a.completed_at and a.completed_at >= week_ago]
        overdue_items = [a for a in pending_items if a.due_date and a.due_date < today]

        # Get goals
        goal_result = await db.execute(
            select(ClientGoal)
            .options(selectinload(ClientGoal.milestones))
            .where(ClientGoal.contact_id == contact.id)
        )
        goals = goal_result.scalars().all()
        active_goals = [g for g in goals if g.status == "active"]

        # Get upcoming sessions
        booking_result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.booking_type))
            .where(
                and_(
                    Booking.contact_id == contact.id,
                    Booking.status == "confirmed",
                    Booking.start_time >= datetime.utcnow(),
                )
            )
            .order_by(Booking.start_time)
            .limit(1)
        )
        next_booking = booking_result.scalar_one_or_none()

        has_activity = bool(pending_items or completed_this_week or active_goals)

        return {
            "has_activity": has_activity,
            "pending_action_items": len(pending_items),
            "completed_this_week": len(completed_this_week),
            "overdue_items": len(overdue_items),
            "active_goals": len(active_goals),
            "goals_progress": [
                {"title": g.title, "progress": g.progress_percent}
                for g in active_goals
            ],
            "next_session": next_booking,
            "action_items": pending_items[:5],  # Top 5 pending items
        }

    # =========================================================================
    # MONTHLY SUMMARIES
    # =========================================================================

    async def _process_monthly_summaries(self, db: AsyncSession):
        """Send monthly progress reports (1st of month)."""
        now = datetime.utcnow()

        # Only send on 1st of month between 9-10am UTC
        if now.day != 1 or now.hour != 9:
            return

        month_ago = now - timedelta(days=30)

        result = await db.execute(
            select(Contact)
            .where(
                and_(
                    Contact.portal_enabled == True,
                    Contact.email.isnot(None),
                    or_(
                        Contact.monthly_summary_sent_at.is_(None),
                        Contact.monthly_summary_sent_at < month_ago,
                    ),
                )
            )
        )
        contacts = result.scalars().all()

        for contact in contacts:
            try:
                summary = await self._get_monthly_summary_data(db, contact)
                if summary["has_activity"]:
                    await email_service.send_monthly_summary(
                        contact=contact,
                        summary=summary,
                    )
                    contact.monthly_summary_sent_at = now
                    await db.commit()
                    logger.info(f"Sent monthly summary to {contact.email}")

            except Exception as e:
                logger.error(f"Failed to send monthly summary: {e}")
                await db.rollback()

    async def _get_monthly_summary_data(self, db: AsyncSession, contact: Contact) -> dict:
        """Gather data for monthly summary email."""
        month_ago = datetime.utcnow() - timedelta(days=30)

        # Sessions this month
        booking_result = await db.execute(
            select(Booking).where(
                and_(
                    Booking.contact_id == contact.id,
                    Booking.status == "completed",
                    Booking.end_time >= month_ago,
                )
            )
        )
        sessions_this_month = len(booking_result.scalars().all())

        # Action items completed this month
        action_result = await db.execute(
            select(ClientActionItem).where(
                and_(
                    ClientActionItem.contact_id == contact.id,
                    ClientActionItem.completed_at.isnot(None),
                    ClientActionItem.completed_at >= month_ago,
                )
            )
        )
        items_completed = len(action_result.scalars().all())

        # Goals progress
        goal_result = await db.execute(
            select(ClientGoal)
            .options(selectinload(ClientGoal.milestones))
            .where(ClientGoal.contact_id == contact.id)
        )
        goals = goal_result.scalars().all()
        completed_goals = [g for g in goals if g.status == "completed" and g.completed_at and g.completed_at >= month_ago]
        active_goals = [g for g in goals if g.status == "active"]

        has_activity = sessions_this_month > 0 or items_completed > 0 or len(goals) > 0

        return {
            "has_activity": has_activity,
            "sessions_this_month": sessions_this_month,
            "action_items_completed": items_completed,
            "goals_completed": len(completed_goals),
            "active_goals": len(active_goals),
            "goals_detail": [
                {"title": g.title, "progress": g.progress_percent, "target_date": g.target_date}
                for g in active_goals
            ],
        }


# Singleton instance
workflow_scheduler = WorkflowScheduler()
