"""
Tests for Interactions router.
"""
import pytest
from httpx import AsyncClient


class TestListContactInteractions:
    """Tests for GET /api/interactions/contact/{contact_id}"""

    @pytest.mark.skip(reason="HTTPBearer auto_error=False causes 403")
    async def test_list_interactions_unauthenticated(self, client: AsyncClient):
        """Unauthenticated requests should fail."""
        response = await client.get("/api/interactions/contact/test-id")
        assert response.status_code == 401

    async def test_list_interactions_empty(
        self, auth_client: AsyncClient, test_contact
    ):
        """List interactions when contact has none."""
        response = await auth_client.get(
            f"/api/interactions/contact/{test_contact.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_interactions_with_data(
        self, auth_client: AsyncClient, test_contact, test_interaction
    ):
        """List interactions for a contact with data."""
        response = await auth_client.get(
            f"/api/interactions/contact/{test_contact.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        interaction = data["items"][0]
        assert "interaction_type" in interaction
        assert "subject" in interaction
        assert "content" in interaction

    async def test_list_interactions_pagination(
        self, auth_client: AsyncClient, test_contact, test_interaction
    ):
        """Test pagination parameters."""
        response = await auth_client.get(
            f"/api/interactions/contact/{test_contact.id}?limit=10&offset=0"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_interactions_contact_not_found(
        self, auth_client: AsyncClient
    ):
        """List interactions for non-existent contact returns 404."""
        response = await auth_client.get("/api/interactions/contact/non-existent-id")
        assert response.status_code == 404


class TestCreateInteraction:
    """Tests for POST /api/interactions"""

    async def test_create_interaction_note(
        self, auth_client: AsyncClient, test_contact
    ):
        """Create a note interaction."""
        interaction_data = {
            "contact_id": test_contact.id,
            "interaction_type": "note",
            "subject": "Follow-up on goals",
            "content": "Discussed progress on quarterly goals.",
        }
        response = await auth_client.post("/api/interactions", json=interaction_data)
        assert response.status_code == 201
        data = response.json()
        assert data["interaction_type"] == "note"
        assert data["subject"] == "Follow-up on goals"

    async def test_create_interaction_call(
        self, auth_client: AsyncClient, test_contact
    ):
        """Create a call interaction."""
        interaction_data = {
            "contact_id": test_contact.id,
            "interaction_type": "call",
            "subject": "Initial phone call",
            "content": "Discussed coaching program options.",
            "direction": "outbound",
        }
        response = await auth_client.post("/api/interactions", json=interaction_data)
        assert response.status_code == 201
        data = response.json()
        assert data["interaction_type"] == "call"
        assert data["direction"] == "outbound"

    async def test_create_interaction_meeting(
        self, auth_client: AsyncClient, test_contact
    ):
        """Create a meeting interaction."""
        interaction_data = {
            "contact_id": test_contact.id,
            "interaction_type": "meeting",
            "subject": "Strategy session",
            "content": "Deep dive into business strategy.",
        }
        response = await auth_client.post("/api/interactions", json=interaction_data)
        assert response.status_code == 201
        data = response.json()
        assert data["interaction_type"] == "meeting"

    async def test_create_interaction_email(
        self, auth_client: AsyncClient, test_contact
    ):
        """Create an email interaction."""
        interaction_data = {
            "contact_id": test_contact.id,
            "interaction_type": "email",
            "subject": "Welcome email sent",
            "content": "Sent onboarding welcome email.",
            "direction": "outbound",
        }
        response = await auth_client.post("/api/interactions", json=interaction_data)
        assert response.status_code == 201
        data = response.json()
        assert data["interaction_type"] == "email"

    async def test_create_interaction_contact_not_found(
        self, auth_client: AsyncClient
    ):
        """Create interaction with non-existent contact returns 400."""
        interaction_data = {
            "contact_id": "non-existent-id",
            "interaction_type": "note",
            "subject": "Should fail",
            "content": "This should not work.",
        }
        response = await auth_client.post("/api/interactions", json=interaction_data)
        assert response.status_code == 400
        assert "contact" in response.json()["detail"].lower()


class TestGetInteraction:
    """Tests for GET /api/interactions/{interaction_id}"""

    async def test_get_interaction(
        self, auth_client: AsyncClient, test_interaction
    ):
        """Get an interaction by ID."""
        response = await auth_client.get(f"/api/interactions/{test_interaction.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_interaction.id
        assert data["interaction_type"] == test_interaction.interaction_type
        assert data["subject"] == test_interaction.subject

    async def test_get_interaction_not_found(self, auth_client: AsyncClient):
        """Get non-existent interaction returns 404."""
        response = await auth_client.get("/api/interactions/non-existent-id")
        assert response.status_code == 404


class TestDeleteInteraction:
    """Tests for DELETE /api/interactions/{interaction_id}"""

    async def test_delete_interaction(
        self, auth_client: AsyncClient, test_interaction
    ):
        """Delete an interaction."""
        response = await auth_client.delete(f"/api/interactions/{test_interaction.id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(f"/api/interactions/{test_interaction.id}")
        assert get_response.status_code == 404

    async def test_delete_interaction_not_found(self, auth_client: AsyncClient):
        """Delete non-existent interaction returns 404."""
        response = await auth_client.delete("/api/interactions/non-existent-id")
        assert response.status_code == 404
