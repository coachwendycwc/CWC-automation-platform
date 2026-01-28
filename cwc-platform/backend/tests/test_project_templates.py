"""
Tests for Project Templates router.
"""
import pytest
from httpx import AsyncClient


class TestListProjectTemplates:
    """Tests for GET /api/project-templates"""

    async def test_list_templates_empty(self, auth_client: AsyncClient):
        """List templates when none exist."""
        response = await auth_client.get("/api/project-templates")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_templates_with_data(
        self, auth_client: AsyncClient, test_project_template
    ):
        """List templates with data."""
        response = await auth_client.get("/api/project-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        template = data[0]
        assert "id" in template
        assert "name" in template
        assert "project_type" in template
        assert "task_count" in template
        assert "is_active" in template

    async def test_list_templates_filter_by_type(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Filter templates by project type."""
        response = await auth_client.get("/api/project-templates?project_type=coaching")
        assert response.status_code == 200
        data = response.json()
        assert all(t["project_type"] == "coaching" for t in data)

    async def test_list_templates_active_only(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Default filter shows only active templates."""
        response = await auth_client.get("/api/project-templates?active_only=true")
        assert response.status_code == 200
        data = response.json()
        assert all(t["is_active"] == True for t in data)

    async def test_list_templates_include_inactive(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Show all templates including inactive."""
        response = await auth_client.get("/api/project-templates?active_only=false")
        assert response.status_code == 200

    async def test_list_templates_search(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Search templates by name."""
        response = await auth_client.get("/api/project-templates?search=Coaching")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_templates_pagination(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Test pagination parameters."""
        response = await auth_client.get("/api/project-templates?skip=0&limit=10")
        assert response.status_code == 200


class TestGetProjectTemplate:
    """Tests for GET /api/project-templates/{template_id}"""

    async def test_get_template(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Get a template by ID."""
        response = await auth_client.get(
            f"/api/project-templates/{test_project_template.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project_template.id
        assert data["name"] == test_project_template.name
        assert "task_templates" in data
        assert len(data["task_templates"]) == 3  # Based on fixture

    async def test_get_template_not_found(self, auth_client: AsyncClient):
        """Get non-existent template returns 404."""
        response = await auth_client.get("/api/project-templates/non-existent-id")
        assert response.status_code == 404


class TestCreateProjectTemplate:
    """Tests for POST /api/project-templates"""

    async def test_create_template(self, auth_client: AsyncClient):
        """Create a new template."""
        template_data = {
            "name": "Workshop Delivery",
            "description": "Template for workshop projects",
            "project_type": "workshop",
            "default_duration_days": 7,
            "estimated_hours": 16.0,
            "task_templates": [
                {"title": "Prepare materials", "description": "Create slides and handouts", "estimated_hours": 4.0, "order_index": 0},
                {"title": "Rehearsal", "description": "Practice delivery", "estimated_hours": 2.0, "order_index": 1},
                {"title": "Deliver workshop", "description": "Run the workshop", "estimated_hours": 8.0, "order_index": 2},
            ],
        }
        response = await auth_client.post("/api/project-templates", json=template_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Workshop Delivery"
        assert data["project_type"] == "workshop"
        assert len(data["task_templates"]) == 3

    async def test_create_template_minimal(self, auth_client: AsyncClient):
        """Create a template with minimal data."""
        template_data = {
            "name": "Simple Project",
            "project_type": "consulting",
            "task_templates": [],
        }
        response = await auth_client.post("/api/project-templates", json=template_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Project"
        assert data["is_active"] == True  # Default


class TestUpdateProjectTemplate:
    """Tests for PUT /api/project-templates/{template_id}"""

    async def test_update_template_name(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Update template name."""
        update_data = {"name": "Updated Template Name"}
        response = await auth_client.put(
            f"/api/project-templates/{test_project_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"

    async def test_update_template_duration(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Update template default duration."""
        update_data = {"default_duration_days": 60}
        response = await auth_client.put(
            f"/api/project-templates/{test_project_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["default_duration_days"] == 60

    async def test_update_template_task_templates(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Update template task list."""
        update_data = {
            "task_templates": [
                {"title": "New Task 1", "description": "First task", "estimated_hours": 1.0, "order_index": 0},
                {"title": "New Task 2", "description": "Second task", "estimated_hours": 2.0, "order_index": 1},
            ]
        }
        response = await auth_client.put(
            f"/api/project-templates/{test_project_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["task_templates"]) == 2

    async def test_update_template_deactivate(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Deactivate a template."""
        update_data = {"is_active": False}
        response = await auth_client.put(
            f"/api/project-templates/{test_project_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

    async def test_update_template_not_found(self, auth_client: AsyncClient):
        """Update non-existent template returns 404."""
        update_data = {"name": "Should fail"}
        response = await auth_client.put(
            "/api/project-templates/non-existent-id",
            json=update_data,
        )
        assert response.status_code == 404


class TestDeleteProjectTemplate:
    """Tests for DELETE /api/project-templates/{template_id}"""

    async def test_delete_template(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Delete a template."""
        response = await auth_client.delete(
            f"/api/project-templates/{test_project_template.id}"
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(
            f"/api/project-templates/{test_project_template.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_template_not_found(self, auth_client: AsyncClient):
        """Delete non-existent template returns 404."""
        response = await auth_client.delete("/api/project-templates/non-existent-id")
        assert response.status_code == 404


class TestDuplicateProjectTemplate:
    """Tests for POST /api/project-templates/{template_id}/duplicate"""

    async def test_duplicate_template(
        self, auth_client: AsyncClient, test_project_template
    ):
        """Duplicate a template."""
        response = await auth_client.post(
            f"/api/project-templates/{test_project_template.id}/duplicate"
        )
        assert response.status_code == 201
        data = response.json()
        assert "(Copy)" in data["name"]
        assert data["project_type"] == test_project_template.project_type
        assert len(data["task_templates"]) == len(test_project_template.task_templates)
        # Should have different ID
        assert data["id"] != test_project_template.id
        # Should be active by default
        assert data["is_active"] == True

    async def test_duplicate_template_not_found(self, auth_client: AsyncClient):
        """Duplicate non-existent template returns 404."""
        response = await auth_client.post("/api/project-templates/non-existent-id/duplicate")
        assert response.status_code == 404
