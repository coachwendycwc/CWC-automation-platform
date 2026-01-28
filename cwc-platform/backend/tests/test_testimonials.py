"""
Tests for Testimonials router (admin endpoints).
"""
import pytest
from httpx import AsyncClient


class TestListTestimonials:
    """Tests for GET /api/testimonials"""

    async def test_list_testimonials_empty(self, auth_client: AsyncClient):
        """List testimonials when none exist."""
        response = await auth_client.get("/api/testimonials")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["items"] == []
        assert "total" in data

    async def test_list_testimonials_with_data(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """List testimonials with data."""
        response = await auth_client.get("/api/testimonials")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        testimonial = data["items"][0]
        assert "id" in testimonial
        assert "author_name" in testimonial
        assert "status" in testimonial
        assert "quote" in testimonial

    async def test_list_testimonials_filter_by_status(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Filter testimonials by status."""
        response = await auth_client.get("/api/testimonials?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "pending" for t in data["items"])

    async def test_list_testimonials_filter_by_contact(
        self, auth_client: AsyncClient, test_testimonial, test_contact
    ):
        """Filter testimonials by contact ID."""
        response = await auth_client.get(
            f"/api/testimonials?contact_id={test_contact.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    async def test_list_testimonials_filter_featured(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Filter testimonials by featured status."""
        response = await auth_client.get("/api/testimonials?featured=false")
        assert response.status_code == 200
        data = response.json()
        assert all(t["featured"] == False for t in data["items"])

    async def test_list_testimonials_pagination(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Test pagination parameters."""
        response = await auth_client.get("/api/testimonials?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "size" in data
        assert data["page"] == 1
        assert data["size"] == 10


class TestGetTestimonial:
    """Tests for GET /api/testimonials/{testimonial_id}"""

    async def test_get_testimonial(self, auth_client: AsyncClient, test_testimonial):
        """Get a testimonial by ID."""
        response = await auth_client.get(f"/api/testimonials/{test_testimonial.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_testimonial.id
        assert data["author_name"] == test_testimonial.author_name
        assert data["quote"] == test_testimonial.quote

    async def test_get_testimonial_not_found(self, auth_client: AsyncClient):
        """Get non-existent testimonial returns 404."""
        response = await auth_client.get("/api/testimonials/non-existent-id")
        assert response.status_code == 404


class TestCreateTestimonial:
    """Tests for POST /api/testimonials"""

    async def test_create_testimonial(
        self, auth_client: AsyncClient, test_contact
    ):
        """Create a new testimonial request."""
        testimonial_data = {
            "contact_id": test_contact.id,
            "author_name": "New Client",
            "author_title": "Manager",
            "author_company": "Test Corp",
        }
        response = await auth_client.post("/api/testimonials", json=testimonial_data)
        assert response.status_code == 201
        data = response.json()
        assert data["author_name"] == "New Client"
        assert data["status"] == "pending"
        assert "request_token" in data

    async def test_create_testimonial_with_quote(
        self, auth_client: AsyncClient, test_contact
    ):
        """Create a testimonial with an initial quote."""
        testimonial_data = {
            "contact_id": test_contact.id,
            "author_name": "Quoted Client",
            "quote": "Amazing coaching experience!",
        }
        response = await auth_client.post("/api/testimonials", json=testimonial_data)
        assert response.status_code == 201
        data = response.json()
        assert data["quote"] == "Amazing coaching experience!"

    async def test_create_testimonial_invalid_contact(self, auth_client: AsyncClient):
        """Create testimonial with invalid contact returns 400."""
        testimonial_data = {
            "contact_id": "non-existent-contact",
            "author_name": "Should Fail",
        }
        response = await auth_client.post("/api/testimonials", json=testimonial_data)
        assert response.status_code == 400


class TestUpdateTestimonial:
    """Tests for PUT /api/testimonials/{testimonial_id}"""

    async def test_update_testimonial_quote(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Update testimonial quote."""
        update_data = {"quote": "Updated testimonial quote"}
        response = await auth_client.put(
            f"/api/testimonials/{test_testimonial.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quote"] == "Updated testimonial quote"

    async def test_update_testimonial_approve(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Approve a testimonial."""
        update_data = {"status": "approved"}
        response = await auth_client.put(
            f"/api/testimonials/{test_testimonial.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["reviewed_at"] is not None

    async def test_update_testimonial_reject(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Reject a testimonial."""
        update_data = {"status": "rejected"}
        response = await auth_client.put(
            f"/api/testimonials/{test_testimonial.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    async def test_update_testimonial_feature(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Feature a testimonial."""
        update_data = {"featured": True}
        response = await auth_client.put(
            f"/api/testimonials/{test_testimonial.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["featured"] == True

    async def test_update_testimonial_author_info(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Update testimonial author info."""
        update_data = {
            "author_name": "Updated Author",
            "author_title": "New Title",
            "author_company": "New Company",
        }
        response = await auth_client.put(
            f"/api/testimonials/{test_testimonial.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["author_name"] == "Updated Author"
        assert data["author_title"] == "New Title"
        assert data["author_company"] == "New Company"

    async def test_update_testimonial_not_found(self, auth_client: AsyncClient):
        """Update non-existent testimonial returns 404."""
        update_data = {"quote": "Should fail"}
        response = await auth_client.put(
            "/api/testimonials/non-existent-id", json=update_data
        )
        assert response.status_code == 404


class TestDeleteTestimonial:
    """Tests for DELETE /api/testimonials/{testimonial_id}"""

    async def test_delete_testimonial(
        self, auth_client: AsyncClient, test_testimonial
    ):
        """Delete a testimonial."""
        response = await auth_client.delete(
            f"/api/testimonials/{test_testimonial.id}"
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(
            f"/api/testimonials/{test_testimonial.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_testimonial_not_found(self, auth_client: AsyncClient):
        """Delete non-existent testimonial returns 404."""
        response = await auth_client.delete("/api/testimonials/non-existent-id")
        assert response.status_code == 404


class TestSendTestimonialRequest:
    """Tests for POST /api/testimonials/{testimonial_id}/send"""

    @pytest.mark.skip(reason="Requires email service mocking")
    async def test_send_testimonial_request(
        self, auth_client: AsyncClient, test_testimonial, test_contact
    ):
        """Send testimonial request email."""
        response = await auth_client.post(
            f"/api/testimonials/{test_testimonial.id}/send",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["request_sent_at"] is not None

    async def test_send_testimonial_request_not_found(self, auth_client: AsyncClient):
        """Send request for non-existent testimonial returns 404."""
        response = await auth_client.post(
            "/api/testimonials/non-existent-id/send",
            json={}
        )
        assert response.status_code == 404
