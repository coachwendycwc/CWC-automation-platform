"""Default-deny auth gate.

Every registered route must either:
  1. carry a recognized auth dependency (get_current_user for admin JWT,
     get_current_client for the client-portal session token) somewhere in
     its dependency tree, or
  2. be explicitly declared public in PUBLIC_ROUTES below.

enforce_auth_gate(app) is called at import time in app.main — an ungated,
undeclared route prevents the app from starting rather than shipping open.

To make a new route public: add its (METHOD, path) here with a comment
saying WHY it is safe to expose unauthenticated.
"""
from fastapi import FastAPI
from fastapi.routing import APIRoute

# Dependency function names that count as auth enforcement.
AUTH_DEPENDENCY_NAMES = {
    "get_current_user",   # admin/staff JWT (app.services.auth_service)
    "get_current_client",  # client-portal session token (app.routers.client_portal)
}

# (METHOD, route path) pairs that are ALLOWED to have no auth dependency.
# Every entry needs a reason. If you can't write one, gate the route instead.
PUBLIC_ROUTES: set[tuple[str, str]] = {
    # Liveness / root banner — no data exposed.
    ("GET", "/"),
    ("GET", "/health"),
    # Admin auth flows — must be reachable to log in at all.
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/google"),
    ("POST", "/api/auth/forgot-password"),
    ("POST", "/api/auth/reset-password"),
    # Client-portal magic-link auth flows.
    ("POST", "/api/client/auth/request-login"),
    ("POST", "/api/client/auth/verify-token"),
    ("POST", "/api/client/auth/logout"),
    # Self-enforcing: validates the session token manually via Header(...).
    ("GET", "/api/client/auth/me"),
    # Public booking pages — capability URLs (slug / unguessable token).
    ("GET", "/api/book/{slug}"),
    ("GET", "/api/book/{slug}/slots"),
    ("POST", "/api/book/{slug}"),
    ("GET", "/api/book/manage/{token}"),
    ("POST", "/api/book/manage/{token}/cancel"),
    ("POST", "/api/book/manage/{token}/reschedule"),
    # Public invoice view/pay — capability URL (view_token).
    ("GET", "/api/invoice/{token}"),
    ("POST", "/api/invoice/{token}/pay"),
    # Public contract signing — capability URL.
    ("GET", "/api/contract/{token}"),
    ("GET", "/api/contract/{token}/status"),
    ("POST", "/api/contract/{token}/sign"),
    ("POST", "/api/contract/{token}/decline"),
    # Public offboarding feedback survey — capability URL.
    ("GET", "/api/feedback/{token}"),
    ("POST", "/api/feedback/{token}"),
    # Public onboarding assessment — capability URL.
    ("GET", "/api/onboarding/{token}"),
    ("POST", "/api/onboarding/{token}"),
    # Public testimonial recording — capability URL.
    ("GET", "/api/testimonial/{token}"),
    ("POST", "/api/testimonial/{token}"),
    # Approved-testimonials gallery — intentionally public marketing data.
    ("GET", "/api/testimonials/public"),
    # ⚠ Open video upload for testimonial recording. Known abuse vector
    # (unauthenticated Cloudinary uploads) — tracked as a follow-up; should
    # require the testimonial token.
    ("GET", "/api/upload/video/signature"),
    ("POST", "/api/upload/video"),
    # Public org-assessment intake form. Known spam/DoS follow-up
    # (creates Contact+Organization rows; needs rate limiting).
    ("POST", "/api/assessments/organizations/submit"),
    # Stripe: publishable key only / checkout for public pay-by-token flow.
    # ⚠ checkout also accepts raw invoice_id unauthenticated — follow-up.
    ("GET", "/api/stripe/config"),
    ("POST", "/api/stripe/checkout"),
    # Stripe webhook — authenticated by signature verification, not JWT.
    ("POST", "/api/stripe/webhook"),
    # Fathom webhook + reachability ping — signature/secret checked in handler.
    ("POST", "/api/webhooks/fathom"),
    ("GET", "/api/webhooks/fathom/test"),
    # OAuth provider redirect targets — must be reachable by browser redirect;
    # protected by state-parameter CSRF checks in the handlers.
    ("GET", "/api/integrations/google/callback"),
    ("GET", "/api/integrations/zoom/callback"),
}


def _has_auth_dependency(dependant) -> bool:
    for dep in dependant.dependencies:
        if dep.call is not None and dep.call.__name__ in AUTH_DEPENDENCY_NAMES:
            return True
        if _has_auth_dependency(dep):
            return True
    return False


def find_unprotected_routes(app: FastAPI) -> list[str]:
    """Return 'METHOD path' for every route that is neither auth-gated nor
    explicitly declared in PUBLIC_ROUTES."""
    violations = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if _has_auth_dependency(route.dependant):
            continue
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            if (method, route.path) not in PUBLIC_ROUTES:
                violations.append(f"{method} {route.path}")
    return sorted(violations)


def enforce_auth_gate(app: FastAPI) -> None:
    """Raise at startup if any route is unprotected and undeclared."""
    violations = find_unprotected_routes(app)
    if violations:
        raise RuntimeError(
            "Default-deny auth gate: the following routes have no auth "
            "dependency and are not declared in PUBLIC_ROUTES "
            "(app/auth_gate.py). Gate them or explicitly allowlist them:\n  "
            + "\n  ".join(violations)
        )
