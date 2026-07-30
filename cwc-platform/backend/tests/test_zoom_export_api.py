"""Zoom recording export endpoints — admin only (they touch client recordings)."""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

PREVIEW = {"count": 1, "total_bytes": 1024, "recordings": []}
EXPORT = {"imported": 1, "skipped": 0, "matched_to_contact": 1, "errors": []}


@pytest.fixture
async def zoom_connected(db_session: AsyncSession, test_user: User) -> User:
    test_user.zoom_token = {"access_token": "a", "refresh_token": "r"}
    await db_session.commit()
    return test_user


class TestZoomExportEndpoints:
    async def test_preview_requires_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.get(
            "/api/zoom-recordings/preview?date_from=2026-06-01&date_to=2026-06-30",
            headers=nonadmin_headers,
        )
        assert response.status_code == 403

    async def test_export_requires_admin(
        self, client: AsyncClient, nonadmin_headers: dict
    ):
        response = await client.post(
            "/api/zoom-recordings/export",
            json={"date_from": "2026-06-01", "date_to": "2026-06-30"},
            headers=nonadmin_headers,
        )
        assert response.status_code == 403

    async def test_preview_returns_listing(
        self, client: AsyncClient, auth_headers: dict, zoom_connected: User
    ):
        with patch(
            "app.routers.zoom_recordings.preview_recordings",
            new_callable=AsyncMock,
            return_value=PREVIEW,
        ):
            response = await client.get(
                "/api/zoom-recordings/preview?date_from=2026-06-01&date_to=2026-06-30",
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["count"] == 1

    async def test_export_runs(
        self, client: AsyncClient, auth_headers: dict, zoom_connected: User
    ):
        with patch(
            "app.routers.zoom_recordings.export_recordings",
            new_callable=AsyncMock,
            return_value=EXPORT,
        ):
            response = await client.post(
                "/api/zoom-recordings/export",
                json={"date_from": "2026-06-01", "date_to": "2026-06-30"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["imported"] == 1

    async def test_zoom_not_connected_is_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        with patch(
            "app.routers.zoom_recordings.preview_recordings",
            new_callable=AsyncMock,
            side_effect=ValueError("Zoom is not connected for this user"),
        ):
            response = await client.get(
                "/api/zoom-recordings/preview?date_from=2026-06-01&date_to=2026-06-30",
                headers=auth_headers,
            )
        assert response.status_code == 400
        assert "not connected" in response.json()["detail"]

    async def test_range_over_one_month_rejected(
        self, client: AsyncClient, auth_headers: dict, zoom_connected: User
    ):
        """Zoom caps a query at one month; say so instead of returning partial data."""
        response = await client.get(
            "/api/zoom-recordings/preview?date_from=2026-01-01&date_to=2026-06-30",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "month" in response.json()["detail"].lower()
