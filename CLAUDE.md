# CWC Automation Platform

## Project Overview
**What:** Unified business automation platform for "Coaching Women of Color" — CRM, scheduling, invoicing, contracts, project management, payments.
**Tech Stack:** FastAPI (Python) + Next.js 14 + PostgreSQL + Stripe + Google Calendar
**Repo Structure:** Main code lives in `cwc-platform/` subfolder. See `cwc-platform/CLAUDE.md` for detailed context.

## Commands
```bash
# Backend
cd cwc-platform/backend && uvicorn app.main:app --reload

# Frontend
cd cwc-platform/frontend && npm run dev
```

## Executive Leadership Lab modules (docs/executive-lab/)
This repo also hosts the Executive Leadership Lab — a 10-month coaching program (static HTML slides + talking points + worksheets, served via GitHub Pages). It is SEPARATE from the automation platform above.

**When asked to build, edit, or revise any Lab module:**
1. READ `docs/executive-lab/_MODULE-PLAYBOOK.md` first — it is the required process (the 4 gates: source-map-first/verify-at-origin → approve → locked OUTLINE → generate + verify).
2. Copy `docs/executive-lab/_TEMPLATE-OUTLINE.md` to start a new module's outline.
3. New-build onboarding for the owner is in `docs/executive-lab/_FOR-WENDY-START-HERE.md`.
NEVER state a statistic in a module without an origin-verified source (see playbook). Modules 7–10 are not yet built.

## Project-Specific Skill Routing
> Universal routing rules live in `~/.claude/CLAUDE.md` (global). Below are additions for THIS project only.

| Trigger | Skill/Tool |
|---------|-----------|
| Stripe/payments work | `1.0.0:docs` (look up Stripe SDK) |
| Google Calendar integration | `1.0.0:docs` (look up Google Calendar API) |
| Coaching workflow features | `product-management:write-spec` first |
