"""Task assignment to a real user, and the My Tasks view built on it.

The existing assigned_to column is free text, so nothing can be queried by it.
assignee_id is the keystone the workspace needs: My Tasks, workload, and
notifications all key off a real user reference.
"""
import pytest
from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


@pytest.fixture
async def assistant_user(db_session: AsyncSession) -> User:
    user = User(
        email="assistant2@example.com",
        name="Assistant Two",
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


class TestAssignTask:
    async def test_assign_task_to_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        assistant_user: User,
    ):
        response = await client.put(
            f"/api/tasks/{test_task.id}",
            json={"assignee_id": assistant_user.id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["assignee_id"] == assistant_user.id

    async def test_unassign_task(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        assistant_user: User,
        db_session: AsyncSession,
    ):
        test_task.assignee_id = assistant_user.id
        await db_session.commit()

        response = await client.put(
            f"/api/tasks/{test_task.id}",
            json={"assignee_id": None},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["assignee_id"] is None

    async def test_assignee_name_included_in_response(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_task: Task,
        assistant_user: User,
        db_session: AsyncSession,
    ):
        test_task.assignee_id = assistant_user.id
        await db_session.commit()

        response = await client.get(
            f"/api/tasks/{test_task.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["assignee_name"] == "Assistant Two"


class TestMyTasks:
    async def test_my_tasks_returns_only_mine(
        self,
        client: AsyncClient,
        assistant_headers: dict,
        assistant_user: User,
        test_task: Task,
        db_session: AsyncSession,
    ):
        test_task.assignee_id = assistant_user.id
        await db_session.commit()

        response = await client.get("/api/tasks/my-tasks", headers=assistant_headers)
        assert response.status_code == 200
        data = response.json()
        ids = [t["id"] for group in data.values() for t in group]
        assert test_task.id in ids

    async def test_my_tasks_excludes_others_tasks(
        self,
        client: AsyncClient,
        assistant_headers: dict,
        test_task: Task,
        test_user: User,
        db_session: AsyncSession,
    ):
        test_task.assignee_id = test_user.id  # assigned to the admin, not me
        await db_session.commit()

        response = await client.get("/api/tasks/my-tasks", headers=assistant_headers)
        assert response.status_code == 200
        ids = [t["id"] for group in response.json().values() for t in group]
        assert test_task.id not in ids

    async def test_my_tasks_groups_by_urgency(
        self,
        client: AsyncClient,
        assistant_headers: dict,
        assistant_user: User,
        test_task: Task,
        db_session: AsyncSession,
    ):
        test_task.assignee_id = assistant_user.id
        test_task.due_date = date.today() - timedelta(days=2)
        test_task.status = "todo"
        await db_session.commit()

        response = await client.get("/api/tasks/my-tasks", headers=assistant_headers)
        data = response.json()
        assert set(data.keys()) == {"overdue", "today", "upcoming", "no_due_date"}
        assert test_task.id in [t["id"] for t in data["overdue"]]

    async def test_completed_tasks_excluded(
        self,
        client: AsyncClient,
        assistant_headers: dict,
        assistant_user: User,
        test_task: Task,
        db_session: AsyncSession,
    ):
        test_task.assignee_id = assistant_user.id
        test_task.status = "completed"
        await db_session.commit()

        response = await client.get("/api/tasks/my-tasks", headers=assistant_headers)
        ids = [t["id"] for group in response.json().values() for t in group]
        assert test_task.id not in ids

    async def test_my_tasks_requires_staff(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get("/api/tasks/my-tasks", headers=nonadmin_headers)
        assert response.status_code == 403
