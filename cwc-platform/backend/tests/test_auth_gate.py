"""Default-deny auth gate.

Every route in the app must either carry a recognized auth dependency
(get_current_user / get_current_client) or be explicitly declared in
PUBLIC_ROUTES. A new router that ships without auth fails these tests
AND fails app startup (enforce_auth_gate is called in app.main).
"""
import re

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import AsyncClient

from app.auth_gate import PUBLIC_ROUTES, enforce_auth_gate, find_unprotected_routes
from app.main import app


def _all_route_keys(target_app: FastAPI) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in target_app.routes
        if isinstance(route, APIRoute)
        for method in route.methods - {"HEAD", "OPTIONS"}
    }


class TestAuthGateAudit:
    def test_no_unprotected_routes(self):
        """Every route is either auth-gated or explicitly allowlisted."""
        assert find_unprotected_routes(app) == []

    def test_gate_catches_ungated_route(self):
        """An app with an ungated, non-allowlisted route fails the audit."""
        rogue_app = FastAPI()

        @rogue_app.get("/api/leaky-endpoint")
        async def leaky():  # pragma: no cover - never called
            return {}

        violations = find_unprotected_routes(rogue_app)
        assert any("/api/leaky-endpoint" in v for v in violations)

        with pytest.raises(RuntimeError, match="leaky-endpoint"):
            enforce_auth_gate(rogue_app)

    def test_public_allowlist_has_no_stale_entries(self):
        """Every PUBLIC_ROUTES entry matches a real registered route."""
        stale = PUBLIC_ROUTES - _all_route_keys(app)
        assert stale == set()


def _fill_path_params(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "1", path)


def _rejected_for_missing_auth(response) -> bool:
    """401/403, or a 422 whose validation errors include the missing
    Authorization header (the client-portal dependency uses Header(...))."""
    if response.status_code in (401, 403):
        return True
    if response.status_code == 422:
        try:
            detail = response.json().get("detail", [])
        except ValueError:
            return False
        return any(
            "authorization" in [str(loc).lower() for loc in err.get("loc", [])]
            for err in detail
            if isinstance(err, dict)
        )
    return False


class TestUnauthenticatedRejection:
    @pytest.mark.asyncio
    async def test_every_gated_route_rejects_unauthenticated_requests(
        self, client: AsyncClient
    ):
        """Runtime proof of default-deny: hit every non-public route with no
        credentials and require a rejection."""
        failures = []
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            for method in route.methods - {"HEAD", "OPTIONS"}:
                if (method, route.path) in PUBLIC_ROUTES:
                    continue
                url = _fill_path_params(route.path)
                response = await client.request(method, url)
                if not _rejected_for_missing_auth(response):
                    failures.append(
                        f"{method} {route.path} -> {response.status_code}"
                    )
        assert failures == [], (
            "Routes accessible without credentials:\n" + "\n".join(failures)
        )
