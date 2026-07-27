"""Staff directory: who can a task be assigned to, and who can be @mentioned."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


@pytest.fixture
async def team(db_session: AsyncSession) -> dict:
    assistant = User(
        email="teamassistant@example.com",
        name="Team Assistant",
        password_hash=hash_password("pass12345"),
        role="assistant",
        is_active=True,
    )
    inactive = User(
        email="former@example.com",
        name="Former Assistant",
        password_hash=hash_password("pass12345"),
        role="assistant",
        is_active=False,
    )
    client_user = User(
        email="justauser@example.com",
        name="Plain User",
        password_hash=hash_password("pass12345"),
        role="user",
        is_active=True,
    )
    db_session.add_all([assistant, inactive, client_user])
    await db_session.commit()
    return {"assistant": assistant, "inactive": inactive, "user": client_user}


class TestStaffDirectory:
    async def test_lists_active_staff_only(
        self, client: AsyncClient, auth_headers: dict, team: dict
    ):
        response = await client.get("/api/users/staff", headers=auth_headers)
        assert response.status_code == 200
        emails = [u["email"] for u in response.json()]

        assert "teamassistant@example.com" in emails  # active assistant
        assert "test@example.com" in emails  # the admin
        assert "former@example.com" not in emails  # deactivated
        assert "justauser@example.com" not in emails  # not staff

    async def test_entries_carry_name_and_role(
        self, client: AsyncClient, auth_headers: dict, team: dict
    ):
        response = await client.get("/api/users/staff", headers=auth_headers)
        entry = next(
            u for u in response.json() if u["email"] == "teamassistant@example.com"
        )
        assert entry["name"] == "Team Assistant"
        assert entry["role"] == "assistant"
        assert "id" in entry

    async def test_assistant_can_see_the_directory(
        self, client: AsyncClient, team: dict
    ):
        token = create_access_token(data={"sub": str(team["assistant"].id)})
        response = await client.get(
            "/api/users/staff", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    async def test_plain_user_cannot(self, client: AsyncClient, nonadmin_headers: dict):
        response = await client.get("/api/users/staff", headers=nonadmin_headers)
        assert response.status_code == 403
