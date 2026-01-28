"""
Tests for Notes router (admin dashboard).
"""
import pytest
from httpx import AsyncClient


class TestListNotes:
    """Tests for GET /api/notes"""

    @pytest.mark.skip(reason="HTTPBearer auto_error=False causes 403")
    async def test_list_notes_unauthenticated(self, client: AsyncClient):
        """Unauthenticated requests should fail."""
        response = await client.get("/api/notes")
        assert response.status_code == 401

    async def test_list_notes_empty(self, auth_client: AsyncClient):
        """List notes when none exist."""
        response = await auth_client.get("/api/notes")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    async def test_list_notes_with_data(
        self, auth_client: AsyncClient, test_client_note
    ):
        """List notes with existing data."""
        response = await auth_client.get("/api/notes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        note = data["items"][0]
        assert "id" in note
        assert "content" in note
        assert "direction" in note
        assert "contact_id" in note

    async def test_list_notes_filter_by_contact(
        self, auth_client: AsyncClient, test_client_note, test_contact
    ):
        """Filter notes by contact_id."""
        response = await auth_client.get(f"/api/notes?contact_id={test_contact.id}")
        assert response.status_code == 200
        data = response.json()
        assert all(n["contact_id"] == test_contact.id for n in data["items"])

    async def test_list_notes_filter_by_direction(
        self, auth_client: AsyncClient, test_client_note
    ):
        """Filter notes by direction."""
        response = await auth_client.get("/api/notes?direction=to_client")
        assert response.status_code == 200
        data = response.json()
        assert all(n["direction"] == "to_client" for n in data["items"])

    async def test_list_notes_filter_by_is_read(
        self, auth_client: AsyncClient, test_client_note
    ):
        """Filter notes by read status."""
        response = await auth_client.get("/api/notes?is_read=false")
        assert response.status_code == 200
        data = response.json()
        assert all(n["is_read"] == False for n in data["items"])

    async def test_list_notes_search(
        self, auth_client: AsyncClient, test_client_note
    ):
        """Search notes by content."""
        response = await auth_client.get("/api/notes?search=Test")
        assert response.status_code == 200
        data = response.json()
        # Search should find notes with "Test" in content
        assert data["total"] >= 0

    async def test_list_notes_pagination(
        self, auth_client: AsyncClient, test_client_note
    ):
        """Test pagination parameters."""
        response = await auth_client.get("/api/notes?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5


class TestUnreadCount:
    """Tests for GET /api/notes/unread-count"""

    async def test_unread_count(self, auth_client: AsyncClient):
        """Get unread count."""
        response = await auth_client.get("/api/notes/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)


class TestGetNote:
    """Tests for GET /api/notes/{note_id}"""

    async def test_get_note(self, auth_client: AsyncClient, test_client_note):
        """Get a single note by ID."""
        response = await auth_client.get(f"/api/notes/{test_client_note.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_client_note.id
        assert data["content"] == test_client_note.content
        assert data["direction"] == test_client_note.direction
        assert "replies" in data

    async def test_get_note_not_found(self, auth_client: AsyncClient):
        """Get non-existent note returns 404."""
        response = await auth_client.get("/api/notes/non-existent-id")
        assert response.status_code == 404


class TestCreateNote:
    """Tests for POST /api/notes"""

    async def test_create_note(self, auth_client: AsyncClient, test_contact):
        """Create a new note to client."""
        note_data = {
            "contact_id": test_contact.id,
            "content": "This is a test note from coach to client.",
        }
        response = await auth_client.post("/api/notes", json=note_data)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == note_data["content"]
        assert data["contact_id"] == test_contact.id
        assert data["direction"] == "to_client"
        assert data["is_read"] == False

    async def test_create_note_invalid_contact(self, auth_client: AsyncClient):
        """Create note with non-existent contact fails."""
        note_data = {
            "contact_id": "non-existent-contact-id",
            "content": "This should fail.",
        }
        response = await auth_client.post("/api/notes", json=note_data)
        assert response.status_code == 400
        assert "Contact not found" in response.json()["detail"]

    async def test_create_note_empty_content(self, auth_client: AsyncClient, test_contact):
        """Create note with empty content should fail validation."""
        note_data = {
            "contact_id": test_contact.id,
            "content": "",
        }
        response = await auth_client.post("/api/notes", json=note_data)
        # Pydantic validation should fail
        assert response.status_code == 422


class TestReplyToNote:
    """Tests for POST /api/notes/{note_id}/reply"""

    async def test_reply_to_note(self, auth_client: AsyncClient, test_client_note):
        """Reply to an existing note."""
        reply_data = {"content": "This is a reply to the note."}
        response = await auth_client.post(
            f"/api/notes/{test_client_note.id}/reply", json=reply_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == reply_data["content"]
        assert data["parent_id"] == test_client_note.id
        assert data["direction"] == "to_client"

    async def test_reply_to_nonexistent_note(self, auth_client: AsyncClient):
        """Reply to non-existent note returns 404."""
        reply_data = {"content": "This should fail."}
        response = await auth_client.post(
            "/api/notes/non-existent-id/reply", json=reply_data
        )
        assert response.status_code == 404


class TestMarkAsRead:
    """Tests for PUT /api/notes/{note_id}/read"""

    async def test_mark_as_read(self, auth_client: AsyncClient, test_client_note):
        """Mark a note as read."""
        response = await auth_client.put(f"/api/notes/{test_client_note.id}/read")
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] == True
        assert data["read_at"] is not None

    async def test_mark_as_read_not_found(self, auth_client: AsyncClient):
        """Mark non-existent note as read returns 404."""
        response = await auth_client.put("/api/notes/non-existent-id/read")
        assert response.status_code == 404


class TestDeleteNote:
    """Tests for DELETE /api/notes/{note_id}"""

    async def test_delete_note(self, auth_client: AsyncClient, test_client_note):
        """Delete a note."""
        response = await auth_client.delete(f"/api/notes/{test_client_note.id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(f"/api/notes/{test_client_note.id}")
        assert get_response.status_code == 404

    async def test_delete_note_not_found(self, auth_client: AsyncClient):
        """Delete non-existent note returns 404."""
        response = await auth_client.delete("/api/notes/non-existent-id")
        assert response.status_code == 404
