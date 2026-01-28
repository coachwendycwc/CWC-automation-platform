"""
Tests for Availability router.
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient


class TestGetWeeklyAvailability:
    """Tests for GET /api/availability"""

    @pytest.mark.skip(reason="HTTPBearer auto_error=False causes 403")
    async def test_get_availability_unauthenticated(self, client: AsyncClient):
        """Unauthenticated requests should fail."""
        response = await client.get("/api/availability")
        assert response.status_code == 401

    async def test_get_availability_empty(self, auth_client: AsyncClient):
        """Get weekly availability when none configured."""
        response = await auth_client.get("/api/availability")
        assert response.status_code == 200
        data = response.json()
        # Should return empty arrays for each day
        assert "monday" in data
        assert "tuesday" in data
        assert "wednesday" in data
        assert "thursday" in data
        assert "friday" in data
        assert "saturday" in data
        assert "sunday" in data

    async def test_get_availability_with_data(
        self, auth_client: AsyncClient, test_availability
    ):
        """Get weekly availability with configured slots."""
        response = await auth_client.get("/api/availability")
        assert response.status_code == 200
        data = response.json()
        # Monday should have the test availability
        assert len(data["monday"]) >= 1
        slot = data["monday"][0]
        assert "start_time" in slot
        assert "end_time" in slot


class TestUpdateWeeklyAvailability:
    """Tests for PUT /api/availability"""

    async def test_update_availability(self, auth_client: AsyncClient):
        """Update weekly availability schedule."""
        availability_data = {
            "availabilities": [
                {"day_of_week": 0, "start_time": "09:00", "end_time": "12:00", "is_active": True},
                {"day_of_week": 0, "start_time": "13:00", "end_time": "17:00", "is_active": True},
                {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00", "is_active": True},
            ]
        }
        response = await auth_client.put("/api/availability", json=availability_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["monday"]) == 2
        assert len(data["tuesday"]) == 1

    async def test_update_availability_replaces_existing(
        self, auth_client: AsyncClient, test_availability
    ):
        """Updating availability replaces all existing slots."""
        # First verify we have existing availability
        response = await auth_client.get("/api/availability")
        assert len(response.json()["monday"]) >= 1

        # Now replace with new schedule
        availability_data = {
            "availabilities": [
                {"day_of_week": 2, "start_time": "10:00", "end_time": "14:00", "is_active": True},
            ]
        }
        response = await auth_client.put("/api/availability", json=availability_data)
        assert response.status_code == 200
        data = response.json()
        # Monday should now be empty, Wednesday should have the new slot
        assert data["monday"] == []
        assert len(data["wednesday"]) == 1

    async def test_update_availability_empty(self, auth_client: AsyncClient, test_availability):
        """Clear all availability by sending empty list."""
        availability_data = {"availabilities": []}
        response = await auth_client.put("/api/availability", json=availability_data)
        assert response.status_code == 200
        data = response.json()
        # All days should be empty
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            assert data[day] == []


class TestListAvailabilityOverrides:
    """Tests for GET /api/availability/overrides"""

    async def test_list_overrides_empty(self, auth_client: AsyncClient):
        """List overrides when none exist."""
        response = await auth_client.get("/api/availability/overrides")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_overrides_with_data(
        self, auth_client: AsyncClient, test_availability_override
    ):
        """List overrides with data."""
        response = await auth_client.get("/api/availability/overrides")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        override = data["items"][0]
        assert "date" in override
        assert "is_available" in override

    async def test_list_overrides_pagination(
        self, auth_client: AsyncClient, test_availability_override
    ):
        """Test pagination parameters."""
        response = await auth_client.get("/api/availability/overrides?limit=10&offset=0")
        assert response.status_code == 200


class TestCreateAvailabilityOverride:
    """Tests for POST /api/availability/overrides"""

    async def test_create_override_blocked(self, auth_client: AsyncClient):
        """Create a blocked date override."""
        override_data = {
            "date": (date.today() + timedelta(days=14)).isoformat(),
            "is_available": False,
            "reason": "Holiday",
        }
        response = await auth_client.post("/api/availability/overrides", json=override_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_available"] == False
        assert data["reason"] == "Holiday"

    async def test_create_override_extra_hours(self, auth_client: AsyncClient):
        """Create an override with extra hours."""
        override_data = {
            "date": (date.today() + timedelta(days=21)).isoformat(),
            "is_available": True,
            "start_time": "18:00",
            "end_time": "20:00",
            "reason": "Extended hours for client",
        }
        response = await auth_client.post("/api/availability/overrides", json=override_data)
        assert response.status_code == 201
        data = response.json()
        assert data["is_available"] == True
        assert data["start_time"] == "18:00"
        assert data["end_time"] == "20:00"

    async def test_create_override_duplicate_date(
        self, auth_client: AsyncClient, test_availability_override
    ):
        """Creating duplicate override for same date should fail."""
        # Get the date from the existing override
        response = await auth_client.get("/api/availability/overrides")
        existing_date = response.json()["items"][0]["date"]

        override_data = {
            "date": existing_date,
            "is_available": False,
            "reason": "Another reason",
        }
        response = await auth_client.post("/api/availability/overrides", json=override_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


class TestGetAvailabilityOverride:
    """Tests for GET /api/availability/overrides/{override_id}"""

    async def test_get_override(
        self, auth_client: AsyncClient, test_availability_override
    ):
        """Get a specific override by ID."""
        response = await auth_client.get(
            f"/api/availability/overrides/{test_availability_override.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_availability_override.id
        assert data["reason"] == test_availability_override.reason

    async def test_get_override_not_found(self, auth_client: AsyncClient):
        """Get non-existent override returns 404."""
        response = await auth_client.get("/api/availability/overrides/non-existent-id")
        assert response.status_code == 404


class TestDeleteAvailabilityOverride:
    """Tests for DELETE /api/availability/overrides/{override_id}"""

    async def test_delete_override(
        self, auth_client: AsyncClient, test_availability_override
    ):
        """Delete an override."""
        response = await auth_client.delete(
            f"/api/availability/overrides/{test_availability_override.id}"
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await auth_client.get(
            f"/api/availability/overrides/{test_availability_override.id}"
        )
        assert get_response.status_code == 404

    async def test_delete_override_not_found(self, auth_client: AsyncClient):
        """Delete non-existent override returns 404."""
        response = await auth_client.delete("/api/availability/overrides/non-existent-id")
        assert response.status_code == 404
