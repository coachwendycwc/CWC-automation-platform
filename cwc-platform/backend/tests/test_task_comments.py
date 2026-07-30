"""Task comments with @mentions, and the notifications they produce.

Comments are what stop a coach and assistant from discussing work in a DM
where the context is lost. An @mention has to actually reach the person, so
mentioning someone creates a notification for them.
"""
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
async def assistant_user(db_session: AsyncSession) -> User:
    user = User(
        email="assistant3@example.com",
        name="Assistant Three",
        password_hash=hash_password("assistpass123"),
        role="assistant",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def assistant_headers(assistant_user: User) -> dict:
    return {
        "Authorization": f"Bearer {create_access_token(data={'sub': str(assistant_user.id)})}"
    }


class TestTaskComments:
    async def test_post_and_list_comment(
        self, client: AsyncClient, auth_headers: dict, test_task: Task
    ):
        post = await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": "First pass is done, ready for review."},
            headers=auth_headers,
        )
        assert post.status_code == 201
        assert post.json()["body"].startswith("First pass")
        assert post.json()["author_name"]

        listing = await client.get(
            f"/api/tasks/{test_task.id}/comments", headers=auth_headers
        )
        assert listing.status_code == 200
        assert len(listing.json()) == 1

    async def test_comment_on_missing_task_is_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/tasks/no-such-task/comments",
            json={"body": "hello"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_empty_comment_rejected(
        self, client: AsyncClient, auth_headers: dict, test_task: Task
    ):
        response = await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": "   "},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_assistant_can_comment(
        self, client: AsyncClient, assistant_headers: dict, test_task: Task
    ):
        response = await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": "On it."},
            headers=assistant_headers,
        )
        assert response.status_code == 201

    async def test_plain_user_cannot_comment(
        self, client: AsyncClient, nonadmin_headers: dict, test_task: Task
    ):
        response = await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": "nope"},
            headers=nonadmin_headers,
        )
        assert response.status_code == 403


class TestMentionNotifications:
    async def test_mention_notifies_that_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        assistant_user: User,
        db_session: AsyncSession,
    ):
        response = await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": f"@{assistant_user.email} can you take this?"},
            headers=auth_headers,
        )
        assert response.status_code == 201

        notifications = (
            await db_session.execute(
                select(Notification).where(
                    Notification.user_id == assistant_user.id
                )
            )
        ).scalars().all()
        assert len(notifications) == 1
        assert notifications[0].kind == "mention"
        assert notifications[0].task_id == test_task.id

    async def test_mentioning_yourself_creates_no_notification(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        test_user: User,
        db_session: AsyncSession,
    ):
        await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": f"@{test_user.email} note to self"},
            headers=auth_headers,
        )
        notifications = (
            await db_session.execute(
                select(Notification).where(Notification.user_id == test_user.id)
            )
        ).scalars().all()
        assert notifications == []

    async def test_unknown_mention_is_ignored(
        self, client: AsyncClient, auth_headers: dict, test_task: Task,
        db_session: AsyncSession,
    ):
        response = await client.post(
            f"/api/tasks/{test_task.id}/comments",
            json={"body": "@nobody@nowhere.com hello"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        notifications = (
            await db_session.execute(select(Notification))
        ).scalars().all()
        assert notifications == []


class TestAssignmentNotification:
    async def test_assigning_a_task_notifies_the_assignee(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        assistant_user: User,
        db_session: AsyncSession,
    ):
        await client.put(
            f"/api/tasks/{test_task.id}",
            json={"assignee_id": assistant_user.id},
            headers=auth_headers,
        )
        notifications = (
            await db_session.execute(
                select(Notification).where(
                    Notification.user_id == assistant_user.id
                )
            )
        ).scalars().all()
        assert len(notifications) == 1
        assert notifications[0].kind == "assigned"


class TestNotificationFeed:
    async def test_feed_lists_and_marks_read(
        self,
        client: AsyncClient,
        assistant_headers: dict,
        assistant_user: User,
        test_task: Task,
        db_session: AsyncSession,
    ):
        db_session.add(
            Notification(
                user_id=assistant_user.id,
                kind="assigned",
                task_id=test_task.id,
                message="You were assigned a task",
            )
        )
        await db_session.commit()

        feed = await client.get("/api/notifications", headers=assistant_headers)
        assert feed.status_code == 200
        assert feed.json()["unread_count"] == 1
        notification_id = feed.json()["items"][0]["id"]

        read = await client.post(
            f"/api/notifications/{notification_id}/read", headers=assistant_headers
        )
        assert read.status_code == 200

        feed2 = await client.get("/api/notifications", headers=assistant_headers)
        assert feed2.json()["unread_count"] == 0

    async def test_feed_only_shows_my_notifications(
        self,
        client: AsyncClient,
        assistant_headers: dict,
        test_user: User,
        test_task: Task,
        db_session: AsyncSession,
    ):
        db_session.add(
            Notification(
                user_id=test_user.id,
                kind="mention",
                task_id=test_task.id,
                message="Someone else's notification",
            )
        )
        await db_session.commit()

        feed = await client.get("/api/notifications", headers=assistant_headers)
        assert feed.json()["unread_count"] == 0
        assert feed.json()["items"] == []
