"""Notifications should reach people who aren't looking at CWC.

In-app notices only work for someone already in the app. An assistant who gets
assigned work or @mentioned needs to hear about it in their inbox, or the
workspace only works for whoever happens to have the tab open.

Email is best effort: a mail failure must never roll back the comment or the
assignment that triggered it.
"""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.task import Task
from app.models.task_comment import TaskComment
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


@pytest.fixture
async def teammate(db_session: AsyncSession) -> User:
    user = User(
        email="teammate@example.com",
        name="Team Mate",
        password_hash=hash_password("teampass123"),
        role="assistant",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def mock_email():
    return patch(
        "app.routers.tasks.email_service.send_task_notification",
        new_callable=AsyncMock,
        return_value=True,
    )


class TestAssignmentEmail:
    async def test_assigning_emails_the_assignee(
        self, client: AsyncClient, auth_headers: dict, test_task: Task, teammate: User
    ):
        with mock_email() as mock_send:
            response = await client.put(
                f"/api/tasks/{test_task.id}",
                json={"assignee_id": teammate.id},
                headers=auth_headers,
            )
        assert response.status_code == 200
        mock_send.assert_awaited_once()
        kwargs = mock_send.call_args.kwargs
        assert kwargs["to_email"] == teammate.email
        assert kwargs["kind"] == "assigned"
        assert test_task.title in kwargs["task_title"]

    async def test_assigning_to_yourself_sends_nothing(
        self, client: AsyncClient, auth_headers: dict, test_task: Task, test_user: User
    ):
        with mock_email() as mock_send:
            response = await client.put(
                f"/api/tasks/{test_task.id}",
                json={"assignee_id": test_user.id},
                headers=auth_headers,
            )
        assert response.status_code == 200
        mock_send.assert_not_awaited()


class TestMentionEmail:
    async def test_mention_emails_that_person(
        self, client: AsyncClient, auth_headers: dict, test_task: Task, teammate: User
    ):
        with mock_email() as mock_send:
            response = await client.post(
                f"/api/tasks/{test_task.id}/comments",
                json={"body": f"@{teammate.email} could you look at this?"},
                headers=auth_headers,
            )
        assert response.status_code == 201
        mock_send.assert_awaited_once()
        assert mock_send.call_args.kwargs["to_email"] == teammate.email
        assert mock_send.call_args.kwargs["kind"] == "mention"

    async def test_mentioning_yourself_sends_nothing(
        self, client: AsyncClient, auth_headers: dict, test_task: Task, test_user: User
    ):
        with mock_email() as mock_send:
            await client.post(
                f"/api/tasks/{test_task.id}/comments",
                json={"body": f"note to self @{test_user.email}"},
                headers=auth_headers,
            )
        mock_send.assert_not_awaited()

    async def test_unknown_mention_sends_nothing(
        self, client: AsyncClient, auth_headers: dict, test_task: Task
    ):
        with mock_email() as mock_send:
            response = await client.post(
                f"/api/tasks/{test_task.id}/comments",
                json={"body": "email me at hello@nowhere.example sometime"},
                headers=auth_headers,
            )
        assert response.status_code == 201
        mock_send.assert_not_awaited()


class TestEmailFailureIsNotFatal:
    async def test_comment_survives_email_failure(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        teammate: User,
        db_session: AsyncSession,
    ):
        """A dead SMTP server must not lose the comment."""
        with patch(
            "app.routers.tasks.email_service.send_task_notification",
            new_callable=AsyncMock,
            side_effect=Exception("SMTP is down"),
        ):
            response = await client.post(
                f"/api/tasks/{test_task.id}/comments",
                json={"body": f"@{teammate.email} still saved?"},
                headers=auth_headers,
            )
        assert response.status_code == 201

        comments = (
            await db_session.execute(
                select(TaskComment).where(TaskComment.task_id == test_task.id)
            )
        ).scalars().all()
        assert len(comments) == 1

        # The in-app notification is still recorded even though email failed
        notifications = (
            await db_session.execute(
                select(Notification).where(Notification.user_id == teammate.id)
            )
        ).scalars().all()
        assert len(notifications) == 1

    async def test_assignment_survives_email_failure(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        teammate: User,
    ):
        with patch(
            "app.routers.tasks.email_service.send_task_notification",
            new_callable=AsyncMock,
            side_effect=Exception("SMTP is down"),
        ):
            response = await client.put(
                f"/api/tasks/{test_task.id}",
                json={"assignee_id": teammate.id},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["assignee_id"] == teammate.id
