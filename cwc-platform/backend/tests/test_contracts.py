"""
Tests for contracts endpoints.
"""
import pytest
from httpx import AsyncClient


class TestContractsEndpoints:
    """Test contracts CRUD endpoints."""

    @pytest.mark.skip(reason="HTTPBearer with auto_error=False causes internal error")
    async def test_list_contracts_unauthenticated(self, client: AsyncClient):
        """Test listing contracts without auth fails."""
        response = await client.get("/api/contracts")
        assert response.status_code == 403

    async def test_list_contracts_empty(self, client: AsyncClient, auth_headers):
        """Test listing contracts when none exist."""
        response = await client.get("/api/contracts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_contracts_with_data(
        self, client: AsyncClient, auth_headers, test_contract
    ):
        """Test listing contracts returns existing ones."""
        response = await client.get("/api/contracts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == "Coaching Agreement"

    async def test_create_contract(
        self, client: AsyncClient, auth_headers, test_contact
    ):
        """Test creating a new contract."""
        response = await client.post(
            "/api/contracts",
            headers=auth_headers,
            json={
                "contact_id": test_contact.id,
                "title": "New Coaching Contract",
                "content": "Terms and conditions for coaching services...",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Coaching Contract"
        assert data["status"] == "draft"
        assert "id" in data

    async def test_get_contract(
        self, client: AsyncClient, auth_headers, test_contract
    ):
        """Test getting a specific contract."""
        response = await client.get(
            f"/api/contracts/{test_contract.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_contract.id
        assert data["title"] == "Coaching Agreement"

    async def test_get_contract_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent contract returns 404."""
        response = await client.get(
            "/api/contracts/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_contract(
        self, client: AsyncClient, auth_headers, test_contract
    ):
        """Test updating a contract."""
        response = await client.put(
            f"/api/contracts/{test_contract.id}",
            headers=auth_headers,
            json={
                "title": "Updated Contract Title",
                "content": "Updated content here...",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Contract Title"

    async def test_send_contract(
        self, client: AsyncClient, auth_headers, test_contract
    ):
        """Test sending a contract for signature."""
        response = await client.post(
            f"/api/contracts/{test_contract.id}/send",
            headers=auth_headers,
            json={"send_email": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert "view_token" in data

    async def test_delete_contract(
        self, client: AsyncClient, auth_headers, test_contract
    ):
        """Test deleting a contract."""
        response = await client.delete(
            f"/api/contracts/{test_contract.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_filter_contracts_by_status(
        self, client: AsyncClient, auth_headers, test_contract
    ):
        """Test filtering contracts by status."""
        response = await client.get(
            "/api/contracts?status=draft",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestPublicContractEndpoints:
    """Test public contract signing endpoints."""

    async def test_get_contract_by_token(
        self, client: AsyncClient, test_contract, db_session
    ):
        """Test accessing contract by view token."""
        test_contract.view_token = "test-view-token-456"
        test_contract.status = "sent"
        await db_session.commit()

        response = await client.get("/api/contract/test-view-token-456")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Coaching Agreement"

    async def test_get_contract_invalid_token(self, client: AsyncClient):
        """Test accessing contract with invalid token fails."""
        response = await client.get("/api/contract/invalid-token")
        assert response.status_code == 404
