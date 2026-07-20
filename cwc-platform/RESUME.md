# CWC Platform — Session Resume / Handoff

**Last updated:** 2026-07-20
**Repo:** `~/projects/CWC/CWC-automation-platform` · GitHub `coachwendycwc/CWC-automation-platform`
**Scope of all this work:** `cwc-platform/` only (backend FastAPI + frontend Next.js). The Executive Leadership Lab content (`docs/executive-lab/`, root Module decks) is a SEPARATE system — never touched.

> Purpose of this file: restart the machine / a fresh chat and pick up exactly here. Read this top-to-bottom first, then the two linked files, then decide the next move with Rafael.

---

## TL;DR — where we are right now

A multi-session security + reliability hardening of the CWC Platform. **PR #3 is MERGED to `main`** (merge commit `77c6c32`, merged 2026-07-16). The branch `security/auth-financial-hardening` is deleted. We are currently on `main` at `77c6c32`.

**The critical stuff is fixed and shipped.** What remains is lower-severity hardening + test debt, all captured as open GitHub issues. Nothing is mid-edit — the working tree is clean except an intentional `.gitignore` tweak (adds `venv-new/`).

---

## What SHIPPED in PR #3 (merged, done)

1. **`POST /api/auth/dev-login` deleted** — was minting an admin JWT for any email, no credential, no env gate.
2. **`register()` → `role="user"`** (was hardcoded `admin`).
3. **Google OAuth admin hole closed** — `auth_service.get_or_create_user` was ALSO hardcoding `role=admin` (the register fix had missed it; worse once OAuth un-stubbed). This was the top code-review finding. Now `role=user`.
4. **15 admin routers gated** with `Depends(get_current_user)` (invoices, payments, payment_plans, recurring_invoices, subscriptions, contracts, contract_templates, projects, tasks, project_templates, expenses, mileage, contractors, offboarding + templates). `organizational_assessments` gated per-endpoint to keep its public submit open.
5. **`environment` setting + fail-closed guard** — app refuses to start in production if `SECRET_KEY` is still the built-in default. Gates `/docs`, `/redoc`, SQL echo, and Fathom stub-secret skip to non-prod.
6. **Stripe payment recording fixed** — `Payment()` used non-existent `transaction_id`/`status` kwargs + no `payment_date` → threw on every real payment. Fixed field mapping, added `payment_date`, new nullable `status` column (**Alembic migration 011**), fixed a cascading Decimal/float TypeError, and fixed 6 `.get(k,0)` → `.get(k) or 0` amount-None crashes; added refund idempotency guard; added `status` to PaymentRead/PaymentList schemas.
7. **Admin bootstrap** — `backend/scripts/seed_dev_user.py` creates `test@cwcplatform.com` / `TestPass123` via the real password path (signup/OAuth are user-only now). Guarded from minting a weak-password admin in prod unless `SEED_PASSWORD` is set.
8. **Frontend dead dev-login flow removed** (api.ts, AuthContext, login page); e2e specs converted to real password login; `npm run build` fixed (pre-existing `afterEach` import + test-config typecheck excludes); docs de-referenced dev-login.
9. **TEST SUITE DEADLOCK FIXED** — the suite hung FOREVER at shutdown (leaked aiosqlite worker thread blocked `threading._shutdown`; tests passed in ms but the process never exited). Fix: `pytest_sessionfinish` engine dispose in `conftest.py` (commit `ab16667`). Suite now finishes: **854/954 passing**.

---

## STILL OPEN — the next-session work (all are GitHub issues)

**Open issues (as of last check):**
- **#4** `[security]` Production deploy config: set `ENVIRONMENT=production` + real `SECRET_KEY`, run migration 011 — **DO THIS BEFORE ANY DEPLOY** (the startup guard now enforces it).
- **#5** `[legal]` E-signature evidentiary gaps — **needs counsel**, not engineering: no immutable snapshot of signed body; content_hash computed at sign-time not send-time; consent (`agreed_to_terms`) not persisted; signed contract content still editable.
- **#6** `[security]` Dependency CVE bumps — python-jose 3.3.0, python-multipart 0.0.9, fastapi 0.109.2, next 14.1.0. Needs its own tested pass.
- **#7** `[bug]` Stripe webhook replay/idempotency (dedup by `event.id`).
- **#8** `[bug]` 10 stale e2e content assertions (pre-existing; UI-copy drift, NOT auth).

**Additional lower-severity findings documented but NOT yet ticketed as their own issues** (from the audit note — consider filing or folding into a "harden auth wiring" issue):
- `integrations.py` OAuth callbacks (`/google/callback`, `/zoom/callback`) reachable unauthenticated (has state-CSRF, so lower risk).
- `organizational_assessments POST /organizations/submit` fully open → spam/DoS (creates Contact+Org rows).
- `subscriptions.py` is gated but ANY authed user (not admin-only) can CRUD billing.
- **Row-level IDOR**: an authed user can read ANY booking/content/extraction (no owner filter on those object routes).
- `get_current_user` does NOT check `is_active` — disabled users still authenticate.
- **Auth wiring is inconsistent** (router-level vs per-endpoint vs none) — no default-deny, so the next new router can ship unauthenticated. **Consider a global auth gate** as the real fix.

**Test debt (~28 failures):** NOT prod bugs — triaged in `cwc-platform/backend/tests/FAILING_TESTS_TRIAGE.md` (schema/field drift, test-isolation FK cycle, stale assertions, unmocked Stripe calls). Read that file before touching tests.

---

## How to run things (ENVIRONMENT GOTCHA — read before running the backend/tests)

- The old backend `venv` was BROKEN (dead Homebrew py3.13 symlink). It was **rebuilt as `venv-new` on Python 3.12** (pinned pydantic 2.6.1 / asyncpg 0.29 won't build on 3.13). Use `venv-new`.
- Backend server: from `cwc-platform/backend/`, activate `venv-new`, then `uvicorn app.main:app --reload --port 8001`.
- Backend tests: `pytest` (now finishes thanks to the deadlock fix). Expect ~854 passing / ~28 failing (the triaged debt).
- Seed the login account: from `backend/`, `python -m scripts.seed_dev_user` → `test@cwcplatform.com` / `TestPass123` (role=admin). Log in at `/login`.
- Frontend: from `cwc-platform/frontend/`, `npm run dev` (port 3001). `npm run build` passes clean. e2e: `npx playwright test` (needs backend up + seeded account; auto-starts frontend).
- Ports: backend 8001, frontend 3001.

---

## Suggested next move (pick with Rafael)

The highest-value next chunk is either:
- **(a) Ship-readiness**: do #4 (deploy config) so the merged fixes can actually go live, OR
- **(b) Finish the auth story**: tackle the "auth wiring inconsistent / global auth gate" item, which subsumes several of the open lower-severity findings (IDOR, is_active check, unauthenticated callbacks) into one coherent default-deny pass.

Route #5 (e-sign) to counsel in parallel — it's not blocked on engineering.

---

## Key files to re-read on resume
- This file (`cwc-platform/RESUME.md`)
- `cwc-platform/backend/tests/FAILING_TESTS_TRIAGE.md` — the test-debt map
- Memory: `~/.claude/.../memory/cwc-audit-2026-07-07.md` — the running audit log (has the full history incl. the merge)
- GitHub: PR #3 (merged) + open issues #4–#8
