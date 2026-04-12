# CWC Automation Platform

## Project Overview
**What:** Unified business automation platform for "Coaching Women of Color" — CRM, scheduling, invoicing, contracts, project management, payments.
**Tech Stack:** FastAPI (Python) + Next.js 14 + PostgreSQL + Stripe + Google Calendar
**Repo Structure:** Main code lives in `cwc-platform/` subfolder. See `cwc-platform/AGENTS.md` for detailed context.

## Commands
```bash
# Backend
cd cwc-platform/backend && uvicorn app.main:app --reload

# Frontend
cd cwc-platform/frontend && npm run dev
```

## Project-Specific Skill Routing
> Universal routing rules live in `~/.Codex/AGENTS.md` (global). Below are additions for THIS project only.

| Trigger | Skill/Tool |
|---------|-----------|
| Stripe/payments work | `1.0.0:docs` (look up Stripe SDK) |
| Google Calendar integration | `1.0.0:docs` (look up Google Calendar API) |
| Coaching workflow features | `product-management:write-spec` first |
