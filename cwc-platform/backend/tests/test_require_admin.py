"""Admin authorization tier: require_admin dependency."""
import pytest
from httpx import AsyncClient
from fastapi import HTTPException

from app.services.auth_service import require_admin


# (method, path) samples on the financial routers gated in this pass.
FINANCIAL_ENDPOINTS = [
    ("get", "/api/payments"),
    ("get", "/api/subscriptions"),
    ("get", "/api/invoices"),
    ("get", "/api/contractors"),
    # payment_plans mounts under /api; a non-admin must be blocked before the
    # invoice lookup, so a dummy id still yields 403 (not 404).
    ("get", "/api/invoices/nonexistent-id/payment-plan"),
    ("get", "/api/recurring-invoices"),
]


class TestFinancialRoutersRequireAdmin:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", FINANCIAL_ENDPOINTS)
    async def test_non_admin_blocked(
        self, client: AsyncClient, nonadmin_headers, method, path
    ):
        resp = await getattr(client, method)(path, headers=nonadmin_headers)
        assert resp.status_code == 403, f"{path} should be admin-only"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", FINANCIAL_ENDPOINTS)
    async def test_admin_allowed(
        self, client: AsyncClient, auth_headers, method, path
    ):
        resp = await getattr(client, method)(path, headers=auth_headers)
        assert resp.status_code != 403, f"{path} must remain open to admins"


class TestRequireAdminDependency:
    @pytest.mark.asyncio
    async def test_admin_user_passes(self, test_user):
        # test_user is role="admin" — require_admin returns the user unchanged.
        result = await require_admin(current_user=test_user)
        assert result is test_user

    @pytest.mark.asyncio
    async def test_non_admin_user_forbidden(self, nonadmin_user):
        with pytest.raises(HTTPException) as exc:
            await require_admin(current_user=nonadmin_user)
        assert exc.value.status_code == 403
