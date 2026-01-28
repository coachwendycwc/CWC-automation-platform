"""
Tests for Contract Templates router.
"""
import pytest
from httpx import AsyncClient


class TestListContractTemplates:
    """Tests for GET /api/contract-templates"""

    async def test_list_templates_empty(self, auth_client: AsyncClient):
        """List templates when none exist."""
        response = await auth_client.get("/api/contract-templates")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_templates_with_data(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """List templates with data."""
        response = await auth_client.get("/api/contract-templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        template = data[0]
        assert "id" in template
        assert "name" in template
        assert "category" in template
        assert "merge_fields" in template
        assert "contracts_count" in template

    async def test_list_templates_filter_by_category(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Filter templates by category."""
        response = await auth_client.get("/api/contract-templates?category=coaching")
        assert response.status_code == 200
        data = response.json()
        assert all(t["category"] == "coaching" for t in data)

    async def test_list_templates_filter_by_active(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Filter templates by active status."""
        response = await auth_client.get("/api/contract-templates?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert all(t["is_active"] == True for t in data)

    async def test_list_templates_search(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Search templates by name."""
        response = await auth_client.get("/api/contract-templates?search=Coaching")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_templates_pagination(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Test pagination parameters."""
        response = await auth_client.get("/api/contract-templates?skip=0&limit=10")
        assert response.status_code == 200


class TestGetMergeFields:
    """Tests for GET /api/contract-templates/merge-fields"""

    async def test_get_merge_fields(self, auth_client: AsyncClient):
        """Get available merge fields."""
        response = await auth_client.get("/api/contract-templates/merge-fields")
        assert response.status_code == 200
        data = response.json()
        assert "auto_fields" in data
        assert "custom_fields" in data
        # Should have some auto fields
        assert len(data["auto_fields"]) > 0


class TestGetContractTemplate:
    """Tests for GET /api/contract-templates/{template_id}"""

    async def test_get_template(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Get a template by ID."""
        response = await auth_client.get(
            f"/api/contract-templates/{test_contract_template.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_contract_template.id
        assert data["name"] == test_contract_template.name
        assert "content" in data
        assert "merge_fields" in data

    async def test_get_template_not_found(self, auth_client: AsyncClient):
        """Get non-existent template returns 404."""
        response = await auth_client.get("/api/contract-templates/non-existent-id")
        assert response.status_code == 404


class TestPreviewTemplate:
    """Tests for GET /api/contract-templates/{template_id}/preview"""

    async def test_preview_template(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Preview template with sample merge data."""
        response = await auth_client.get(
            f"/api/contract-templates/{test_contract_template.id}/preview"
        )
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "content" in data
        assert "merge_fields" in data
        # Content should have merge fields replaced with sample data
        assert "{{" not in data["content"] or "sample" in data["content"].lower()

    async def test_preview_template_not_found(self, auth_client: AsyncClient):
        """Preview non-existent template returns 404."""
        response = await auth_client.get("/api/contract-templates/non-existent-id/preview")
        assert response.status_code == 404


class TestCreateContractTemplate:
    """Tests for POST /api/contract-templates"""

    async def test_create_template(self, auth_client: AsyncClient):
        """Create a new template."""
        template_data = {
            "name": "Workshop Agreement",
            "description": "Agreement for workshop participants",
            "content": "This workshop agreement is between {{client_name}} for {{workshop_name}}.",
            "category": "workshop",
            "default_expiry_days": 14,
        }
        response = await auth_client.post("/api/contract-templates", json=template_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Workshop Agreement"
        assert data["category"] == "workshop"
        # Should auto-extract merge fields
        assert "client_name" in data["merge_fields"]
        assert "workshop_name" in data["merge_fields"]

    async def test_create_template_no_merge_fields(self, auth_client: AsyncClient):
        """Create a template without merge fields."""
        template_data = {
            "name": "Simple Agreement",
            "content": "This is a simple agreement with no placeholders.",
            "category": "coaching",
        }
        response = await auth_client.post("/api/contract-templates", json=template_data)
        assert response.status_code == 201
        data = response.json()
        assert data["merge_fields"] == []


class TestUpdateContractTemplate:
    """Tests for PUT /api/contract-templates/{template_id}"""

    async def test_update_template_name(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Update template name."""
        update_data = {"name": "Updated Template Name"}
        response = await auth_client.put(
            f"/api/contract-templates/{test_contract_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"

    async def test_update_template_content(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Update template content re-extracts merge fields."""
        update_data = {
            "content": "New content with {{new_field}} and {{another_field}}."
        }
        response = await auth_client.put(
            f"/api/contract-templates/{test_contract_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "new_field" in data["merge_fields"]
        assert "another_field" in data["merge_fields"]

    async def test_update_template_deactivate(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Deactivate a template."""
        update_data = {"is_active": False}
        response = await auth_client.put(
            f"/api/contract-templates/{test_contract_template.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

    async def test_update_template_not_found(self, auth_client: AsyncClient):
        """Update non-existent template returns 404."""
        update_data = {"name": "Should fail"}
        response = await auth_client.put(
            "/api/contract-templates/non-existent-id",
            json=update_data,
        )
        assert response.status_code == 404


class TestDeleteContractTemplate:
    """Tests for DELETE /api/contract-templates/{template_id}"""

    async def test_delete_template(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Delete a template."""
        response = await auth_client.delete(
            f"/api/contract-templates/{test_contract_template.id}"
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(
            f"/api/contract-templates/{test_contract_template.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_template_not_found(self, auth_client: AsyncClient):
        """Delete non-existent template returns 404."""
        response = await auth_client.delete("/api/contract-templates/non-existent-id")
        assert response.status_code == 404

    async def test_delete_template_in_use(
        self, auth_client: AsyncClient, test_contract_template, test_contract, db_session
    ):
        """Delete template that is in use should fail."""
        # Link the contract to the template
        test_contract.template_id = test_contract_template.id
        await db_session.commit()

        response = await auth_client.delete(
            f"/api/contract-templates/{test_contract_template.id}"
        )
        assert response.status_code == 400
        assert "in use" in response.json()["detail"].lower() or "used by" in response.json()["detail"].lower()


class TestDuplicateContractTemplate:
    """Tests for POST /api/contract-templates/{template_id}/duplicate"""

    async def test_duplicate_template(
        self, auth_client: AsyncClient, test_contract_template
    ):
        """Duplicate a template."""
        response = await auth_client.post(
            f"/api/contract-templates/{test_contract_template.id}/duplicate"
        )
        assert response.status_code == 201
        data = response.json()
        assert "(Copy)" in data["name"]
        assert data["content"] == test_contract_template.content
        assert data["category"] == test_contract_template.category
        # Should have different ID
        assert data["id"] != test_contract_template.id

    async def test_duplicate_template_not_found(self, auth_client: AsyncClient):
        """Duplicate non-existent template returns 404."""
        response = await auth_client.post("/api/contract-templates/non-existent-id/duplicate")
        assert response.status_code == 404
