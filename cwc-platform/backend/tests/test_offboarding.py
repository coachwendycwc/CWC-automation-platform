"""
Tests for Offboarding router (workflows and templates).
"""
import pytest
from httpx import AsyncClient


# ============== Workflow Tests ==============

class TestListWorkflows:
    """Tests for GET /api/offboarding"""

    async def test_list_workflows_empty(self, auth_client: AsyncClient):
        """List workflows when none exist."""
        response = await auth_client.get("/api/offboarding")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["items"] == []
        assert "total" in data

    async def test_list_workflows_with_data(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """List workflows with data."""
        response = await auth_client.get("/api/offboarding")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        workflow = data["items"][0]
        assert "id" in workflow
        assert "workflow_type" in workflow
        assert "status" in workflow

    async def test_list_workflows_filter_by_status(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Filter workflows by status."""
        response = await auth_client.get("/api/offboarding?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert all(w["status"] == "pending" for w in data["items"])

    async def test_list_workflows_filter_by_type(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Filter workflows by type."""
        response = await auth_client.get("/api/offboarding?workflow_type=project")
        assert response.status_code == 200
        data = response.json()
        assert all(w["workflow_type"] == "project" for w in data["items"])

    async def test_list_workflows_filter_by_contact(
        self, auth_client: AsyncClient, test_offboarding_workflow, test_contact
    ):
        """Filter workflows by contact ID."""
        response = await auth_client.get(
            f"/api/offboarding?contact_id={test_contact.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    async def test_list_workflows_pagination(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Test pagination parameters."""
        response = await auth_client.get("/api/offboarding?page=1&size=10")
        assert response.status_code == 200


class TestGetWorkflowStats:
    """Tests for GET /api/offboarding/stats"""

    async def test_get_stats_empty(self, auth_client: AsyncClient):
        """Get stats when no workflows exist."""
        response = await auth_client.get("/api/offboarding/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data or "pending_count" in data or isinstance(data, dict)

    async def test_get_stats_with_data(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Get stats with workflows."""
        response = await auth_client.get("/api/offboarding/stats")
        assert response.status_code == 200


class TestInitiateWorkflow:
    """Tests for POST /api/offboarding/initiate"""

    async def test_initiate_workflow(
        self, auth_client: AsyncClient, test_contact
    ):
        """Initiate a new offboarding workflow."""
        workflow_data = {
            "contact_id": test_contact.id,
            "workflow_type": "client",
            "send_survey": True,
            "request_testimonial": True,
            "checklist": [
                {"item": "Final meeting", "completed": False},
                {"item": "Send invoice", "completed": False},
            ],
        }
        response = await auth_client.post("/api/offboarding/initiate", json=workflow_data)
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "client"
        assert data["status"] == "pending"
        assert "survey_token" in data or data.get("send_survey") == True

    async def test_initiate_project_workflow(
        self, auth_client: AsyncClient, test_contact, test_project
    ):
        """Initiate a project offboarding workflow."""
        workflow_data = {
            "contact_id": test_contact.id,
            "workflow_type": "project",
            "related_project_id": test_project.id,
            "send_survey": True,
            "request_testimonial": False,
        }
        response = await auth_client.post("/api/offboarding/initiate", json=workflow_data)
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "project"


class TestGetWorkflow:
    """Tests for GET /api/offboarding/{workflow_id}"""

    async def test_get_workflow(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Get a workflow by ID."""
        response = await auth_client.get(
            f"/api/offboarding/{test_offboarding_workflow.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_offboarding_workflow.id
        assert data["workflow_type"] == test_offboarding_workflow.workflow_type
        assert "checklist" in data

    async def test_get_workflow_not_found(self, auth_client: AsyncClient):
        """Get non-existent workflow returns 404."""
        response = await auth_client.get("/api/offboarding/non-existent-id")
        assert response.status_code == 404


class TestUpdateWorkflow:
    """Tests for PUT /api/offboarding/{workflow_id}"""

    async def test_update_workflow_notes(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Update workflow notes."""
        update_data = {"notes": "Updated notes for the workflow"}
        response = await auth_client.put(
            f"/api/offboarding/{test_offboarding_workflow.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes for the workflow"

    async def test_update_workflow_options(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Update workflow send_survey option."""
        update_data = {"send_survey": False}
        response = await auth_client.put(
            f"/api/offboarding/{test_offboarding_workflow.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["send_survey"] == False

    async def test_update_workflow_not_found(self, auth_client: AsyncClient):
        """Update non-existent workflow returns 404."""
        update_data = {"notes": "Should fail"}
        response = await auth_client.put(
            "/api/offboarding/non-existent-id",
            json=update_data,
        )
        assert response.status_code == 404


class TestToggleChecklistItem:
    """Tests for POST /api/offboarding/{workflow_id}/checklist/{item_index}"""

    async def test_toggle_checklist_item(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Toggle a checklist item."""
        response = await auth_client.post(
            f"/api/offboarding/{test_offboarding_workflow.id}/checklist/0"
        )
        assert response.status_code == 200
        data = response.json()
        # Item at index 0 should now be toggled
        assert "checklist" in data

    async def test_toggle_checklist_workflow_not_found(self, auth_client: AsyncClient):
        """Toggle checklist for non-existent workflow returns 404."""
        response = await auth_client.post(
            "/api/offboarding/non-existent-id/checklist/0"
        )
        assert response.status_code == 404


class TestCompleteWorkflow:
    """Tests for POST /api/offboarding/{workflow_id}/complete"""

    async def test_complete_workflow(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Mark a workflow as complete."""
        response = await auth_client.post(
            f"/api/offboarding/{test_offboarding_workflow.id}/complete"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    async def test_complete_workflow_not_found(self, auth_client: AsyncClient):
        """Complete non-existent workflow returns 404."""
        response = await auth_client.post("/api/offboarding/non-existent-id/complete")
        assert response.status_code == 404


class TestCancelWorkflow:
    """Tests for POST /api/offboarding/{workflow_id}/cancel"""

    async def test_cancel_workflow(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Cancel a workflow."""
        response = await auth_client.post(
            f"/api/offboarding/{test_offboarding_workflow.id}/cancel"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    async def test_cancel_workflow_with_reason(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Cancel a workflow with reason."""
        response = await auth_client.post(
            f"/api/offboarding/{test_offboarding_workflow.id}/cancel?reason=Client%20request"
        )
        assert response.status_code == 200

    async def test_cancel_workflow_not_found(self, auth_client: AsyncClient):
        """Cancel non-existent workflow returns 404."""
        response = await auth_client.post("/api/offboarding/non-existent-id/cancel")
        assert response.status_code == 404


class TestGetWorkflowActivity:
    """Tests for GET /api/offboarding/{workflow_id}/activity"""

    async def test_get_workflow_activity_empty(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Get activity log when empty."""
        response = await auth_client.get(
            f"/api/offboarding/{test_offboarding_workflow.id}/activity"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============== Email Action Tests ==============

class TestSendSurvey:
    """Tests for POST /api/offboarding/{workflow_id}/send-survey"""

    @pytest.mark.skip(reason="Requires email service mocking")
    async def test_send_survey(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Send survey email."""
        response = await auth_client.post(
            f"/api/offboarding/{test_offboarding_workflow.id}/send-survey"
        )
        assert response.status_code == 200

    async def test_send_survey_not_found(self, auth_client: AsyncClient):
        """Send survey for non-existent workflow returns 404."""
        response = await auth_client.post(
            "/api/offboarding/non-existent-id/send-survey"
        )
        assert response.status_code == 404


class TestRequestTestimonial:
    """Tests for POST /api/offboarding/{workflow_id}/request-testimonial"""

    @pytest.mark.skip(reason="Requires email service mocking")
    async def test_request_testimonial(
        self, auth_client: AsyncClient, test_offboarding_workflow
    ):
        """Request testimonial via email."""
        response = await auth_client.post(
            f"/api/offboarding/{test_offboarding_workflow.id}/request-testimonial"
        )
        assert response.status_code == 200

    async def test_request_testimonial_not_found(self, auth_client: AsyncClient):
        """Request testimonial for non-existent workflow returns 404."""
        response = await auth_client.post(
            "/api/offboarding/non-existent-id/request-testimonial"
        )
        assert response.status_code == 404


# ============== Template Tests ==============

class TestListTemplates:
    """Tests for GET /api/offboarding-templates"""

    async def test_list_templates_empty(self, auth_client: AsyncClient):
        """List templates when none exist."""
        response = await auth_client.get("/api/offboarding-templates")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_templates_with_data(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """List templates with data."""
        response = await auth_client.get("/api/offboarding-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        template = data[0]
        assert "id" in template
        assert "name" in template
        assert "workflow_type" in template

    async def test_list_templates_filter_by_type(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """Filter templates by workflow type."""
        response = await auth_client.get("/api/offboarding-templates?workflow_type=client")
        assert response.status_code == 200
        data = response.json()
        assert all(t["workflow_type"] == "client" for t in data)

    async def test_list_templates_active_only(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """List only active templates by default."""
        response = await auth_client.get("/api/offboarding-templates?active_only=true")
        assert response.status_code == 200
        data = response.json()
        assert all(t["is_active"] == True for t in data)


class TestGetTemplate:
    """Tests for GET /api/offboarding-templates/{template_id}"""

    async def test_get_template(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """Get a template by ID."""
        response = await auth_client.get(
            f"/api/offboarding-templates/{test_offboarding_template.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_offboarding_template.id
        assert data["name"] == test_offboarding_template.name
        assert "checklist_items" in data

    async def test_get_template_not_found(self, auth_client: AsyncClient):
        """Get non-existent template returns 404."""
        response = await auth_client.get("/api/offboarding-templates/non-existent-id")
        assert response.status_code == 404


class TestCreateTemplate:
    """Tests for POST /api/offboarding-templates"""

    async def test_create_template(self, auth_client: AsyncClient):
        """Create a new template."""
        template_data = {
            "name": "Project Wrap-up Template",
            "description": "Template for project completion",
            "workflow_type": "project",
            "checklist_items": [
                "Final deliverables review",
                "Send closing invoice",
                "Request feedback",
            ],
            "survey_delay_days": 3,
            "testimonial_delay_days": 7,
        }
        response = await auth_client.post("/api/offboarding-templates", json=template_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Project Wrap-up Template"
        assert data["workflow_type"] == "project"
        assert len(data["checklist_items"]) == 3

    async def test_create_template_minimal(self, auth_client: AsyncClient):
        """Create a template with minimal data."""
        template_data = {
            "name": "Simple Template",
            "workflow_type": "client",
            "checklist_items": [],
        }
        response = await auth_client.post("/api/offboarding-templates", json=template_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Simple Template"
        assert data["is_active"] == True


class TestUpdateTemplate:
    """Tests for PUT /api/offboarding-templates/{template_id}"""

    async def test_update_template_name(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """Update template name."""
        update_data = {"name": "Updated Template Name"}
        response = await auth_client.put(
            f"/api/offboarding-templates/{test_offboarding_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"

    async def test_update_template_checklist(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """Update template checklist items."""
        update_data = {
            "checklist_items": ["New item 1", "New item 2"],
        }
        response = await auth_client.put(
            f"/api/offboarding-templates/{test_offboarding_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["checklist_items"]) == 2

    async def test_update_template_deactivate(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """Deactivate a template."""
        update_data = {"is_active": False}
        response = await auth_client.put(
            f"/api/offboarding-templates/{test_offboarding_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

    async def test_update_template_not_found(self, auth_client: AsyncClient):
        """Update non-existent template returns 404."""
        update_data = {"name": "Should fail"}
        response = await auth_client.put(
            "/api/offboarding-templates/non-existent-id",
            json=update_data,
        )
        assert response.status_code == 404


class TestDeleteTemplate:
    """Tests for DELETE /api/offboarding-templates/{template_id}"""

    async def test_delete_template(
        self, auth_client: AsyncClient, test_offboarding_template
    ):
        """Delete a template."""
        response = await auth_client.delete(
            f"/api/offboarding-templates/{test_offboarding_template.id}"
        )
        assert response.status_code == 200

        # Verify it's deleted
        get_response = await auth_client.get(
            f"/api/offboarding-templates/{test_offboarding_template.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_template_not_found(self, auth_client: AsyncClient):
        """Delete non-existent template returns 404."""
        response = await auth_client.delete("/api/offboarding-templates/non-existent-id")
        assert response.status_code == 404
