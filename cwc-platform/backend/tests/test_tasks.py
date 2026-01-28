"""
Tests for Tasks router.
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient


class TestListProjectTasks:
    """Tests for GET /api/projects/{project_id}/tasks"""

    async def test_list_tasks_empty(self, auth_client: AsyncClient, test_project):
        """List tasks when project has none."""
        response = await auth_client.get(f"/api/projects/{test_project.id}/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_tasks_with_data(
        self, auth_client: AsyncClient, test_project, test_task
    ):
        """List tasks for a project with tasks."""
        response = await auth_client.get(f"/api/projects/{test_project.id}/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        task = data[0]
        assert "id" in task
        assert "title" in task
        assert "status" in task
        assert "priority" in task

    async def test_list_tasks_filter_by_status(
        self, auth_client: AsyncClient, test_project, test_task
    ):
        """Filter tasks by status."""
        response = await auth_client.get(
            f"/api/projects/{test_project.id}/tasks?status=todo"
        )
        assert response.status_code == 200
        data = response.json()
        assert all(task["status"] == "todo" for task in data)

    async def test_list_tasks_filter_by_priority(
        self, auth_client: AsyncClient, test_project, test_task
    ):
        """Filter tasks by priority."""
        response = await auth_client.get(
            f"/api/projects/{test_project.id}/tasks?priority=high"
        )
        assert response.status_code == 200
        data = response.json()
        assert all(task["priority"] == "high" for task in data)

    async def test_list_tasks_project_not_found(self, auth_client: AsyncClient):
        """List tasks for non-existent project returns 404."""
        response = await auth_client.get("/api/projects/non-existent-id/tasks")
        assert response.status_code == 404


class TestCreateTask:
    """Tests for POST /api/projects/{project_id}/tasks"""

    async def test_create_task(self, auth_client: AsyncClient, test_project):
        """Create a new task."""
        task_data = {
            "title": "New Test Task",
            "description": "Task description",
            "priority": "medium",
            "project_id": test_project.id,  # Required by schema
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        response = await auth_client.post(
            f"/api/projects/{test_project.id}/tasks", json=task_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Test Task"
        assert data["status"] == "todo"  # Default status
        assert data["priority"] == "medium"
        assert "task_number" in data

    async def test_create_task_with_assignment(
        self, auth_client: AsyncClient, test_project
    ):
        """Create a task with assignment."""
        task_data = {
            "title": "Assigned Task",
            "assigned_to": "team@example.com",
            "priority": "high",
            "project_id": test_project.id,  # Required by schema
        }
        response = await auth_client.post(
            f"/api/projects/{test_project.id}/tasks", json=task_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["assigned_to"] == "team@example.com"

    async def test_create_task_project_not_found(self, auth_client: AsyncClient):
        """Create task for non-existent project returns 404."""
        task_data = {
            "title": "Should fail",
            "priority": "medium",
            "project_id": "non-existent-id",  # Required by schema
        }
        response = await auth_client.post(
            "/api/projects/non-existent-id/tasks", json=task_data
        )
        assert response.status_code == 404


class TestGetTaskStats:
    """Tests for GET /api/tasks/stats"""

    async def test_get_stats_empty(self, auth_client: AsyncClient):
        """Get task stats when no tasks exist."""
        response = await auth_client.get("/api/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "todo_count" in data
        assert "completed_count" in data

    async def test_get_stats_with_data(self, auth_client: AsyncClient, test_task):
        """Get task stats with tasks."""
        response = await auth_client.get("/api/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] >= 1

    async def test_get_stats_filter_by_project(
        self, auth_client: AsyncClient, test_project, test_task
    ):
        """Get stats filtered by project."""
        response = await auth_client.get(f"/api/tasks/stats?project_id={test_project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] >= 1


class TestGetTask:
    """Tests for GET /api/tasks/{task_id}"""

    async def test_get_task(self, auth_client: AsyncClient, test_task):
        """Get a task by ID."""
        response = await auth_client.get(f"/api/tasks/{test_task.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["title"] == test_task.title
        assert "time_entries" in data
        assert "project_title" in data

    async def test_get_task_not_found(self, auth_client: AsyncClient):
        """Get non-existent task returns 404."""
        response = await auth_client.get("/api/tasks/non-existent-id")
        assert response.status_code == 404


class TestUpdateTask:
    """Tests for PUT /api/tasks/{task_id}"""

    async def test_update_task_title(self, auth_client: AsyncClient, test_task):
        """Update task title."""
        update_data = {"title": "Updated Task Title"}
        response = await auth_client.put(f"/api/tasks/{test_task.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task Title"

    async def test_update_task_status(self, auth_client: AsyncClient, test_task):
        """Update task status."""
        update_data = {"status": "in_progress"}
        response = await auth_client.put(f"/api/tasks/{test_task.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_update_task_complete(self, auth_client: AsyncClient, test_task):
        """Complete a task sets completed_at."""
        update_data = {"status": "completed"}
        response = await auth_client.put(f"/api/tasks/{test_task.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    async def test_update_task_not_found(self, auth_client: AsyncClient):
        """Update non-existent task returns 404."""
        update_data = {"title": "Should fail"}
        response = await auth_client.put("/api/tasks/non-existent-id", json=update_data)
        assert response.status_code == 404


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{task_id}"""

    async def test_delete_task(self, auth_client: AsyncClient, test_task):
        """Delete a task."""
        response = await auth_client.delete(f"/api/tasks/{test_task.id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(f"/api/tasks/{test_task.id}")
        assert get_response.status_code == 404

    async def test_delete_task_not_found(self, auth_client: AsyncClient):
        """Delete non-existent task returns 404."""
        response = await auth_client.delete("/api/tasks/non-existent-id")
        assert response.status_code == 404


class TestCompleteTask:
    """Tests for POST /api/tasks/{task_id}/complete"""

    async def test_complete_task(self, auth_client: AsyncClient, test_task):
        """Mark a task as completed."""
        response = await auth_client.post(f"/api/tasks/{test_task.id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    async def test_complete_task_not_found(self, auth_client: AsyncClient):
        """Complete non-existent task returns 404."""
        response = await auth_client.post("/api/tasks/non-existent-id/complete")
        assert response.status_code == 404


class TestListTimeEntries:
    """Tests for GET /api/tasks/{task_id}/time-entries"""

    async def test_list_time_entries_empty(self, auth_client: AsyncClient, test_task):
        """List time entries when none exist."""
        response = await auth_client.get(f"/api/tasks/{test_task.id}/time-entries")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_time_entries_with_data(
        self, auth_client: AsyncClient, test_task, test_time_entry
    ):
        """List time entries for a task."""
        response = await auth_client.get(f"/api/tasks/{test_task.id}/time-entries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        entry = data[0]
        assert "hours" in entry
        assert "description" in entry
        assert "entry_date" in entry

    async def test_list_time_entries_task_not_found(self, auth_client: AsyncClient):
        """List time entries for non-existent task returns 404."""
        response = await auth_client.get("/api/tasks/non-existent-id/time-entries")
        assert response.status_code == 404


class TestCreateTimeEntry:
    """Tests for POST /api/tasks/{task_id}/time-entries"""

    async def test_create_time_entry(self, auth_client: AsyncClient, test_task):
        """Create a time entry for a task."""
        entry_data = {
            "description": "Worked on implementation",
            "hours": 3.5,
            "entry_date": date.today().isoformat(),
            "created_by": "developer@example.com",
        }
        response = await auth_client.post(
            f"/api/tasks/{test_task.id}/time-entries", json=entry_data
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["hours"]) == 3.5
        assert data["description"] == "Worked on implementation"

    async def test_create_time_entry_task_not_found(self, auth_client: AsyncClient):
        """Create time entry for non-existent task returns 404."""
        entry_data = {
            "description": "Should fail",
            "hours": 1.0,
            "entry_date": date.today().isoformat(),
        }
        response = await auth_client.post(
            "/api/tasks/non-existent-id/time-entries", json=entry_data
        )
        assert response.status_code == 404


class TestDeleteTimeEntry:
    """Tests for DELETE /api/time-entries/{entry_id}"""

    async def test_delete_time_entry(
        self, auth_client: AsyncClient, test_time_entry
    ):
        """Delete a time entry."""
        response = await auth_client.delete(f"/api/time-entries/{test_time_entry.id}")
        assert response.status_code == 204

    async def test_delete_time_entry_not_found(self, auth_client: AsyncClient):
        """Delete non-existent time entry returns 404."""
        response = await auth_client.delete("/api/time-entries/non-existent-id")
        assert response.status_code == 404


class TestListAllTasks:
    """Tests for GET /api/tasks"""

    async def test_list_all_tasks_empty(self, auth_client: AsyncClient):
        """List all tasks when none exist."""
        response = await auth_client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_all_tasks_with_data(self, auth_client: AsyncClient, test_task):
        """List all tasks across projects."""
        response = await auth_client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_all_tasks_search(self, auth_client: AsyncClient, test_task):
        """Search tasks by title or number."""
        response = await auth_client.get(f"/api/tasks?search={test_task.title[:5]}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_all_tasks_pagination(self, auth_client: AsyncClient, test_task):
        """Test pagination parameters."""
        response = await auth_client.get("/api/tasks?skip=0&limit=10")
        assert response.status_code == 200
