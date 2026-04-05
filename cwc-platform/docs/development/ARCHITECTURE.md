# CWC Platform Architecture

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python, SQLAlchemy 2.0 async |
| Database | PostgreSQL in intended architecture, SQLite used in some local/dev flows |
| Auth | JWT, email/password, Google OAuth, client magic links |
| Payments | Stripe |
| Calendar | Google Calendar today, expanding to multi-calendar foundation |
| Session Intelligence | Fathom ingestion, expanding toward Zoom/Fathom workflow |

## Repository Layout

```text
cwc-platform/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── alembic/
│   └── tests/
├── frontend/
│   ├── src/app/
│   ├── src/components/
│   ├── src/contexts/
│   └── src/lib/
└── docs/
```

## Core Domain Areas

### Business Operations
- users
- contacts
- organizations
- interactions
- tasks
- projects

### Revenue Operations
- invoices
- payments
- subscriptions
- recurring invoices
- contractors
- expenses
- mileage

### Scheduling
- booking types
- availability
- availability overrides
- bookings
- integrations
- calendar connections

### Client Experience
- client sessions
- client portal
- notes
- content
- goals
- action items
- feedback
- testimonials

### Coaching Intelligence
- Fathom webhook ingestion
- coaching sessions
- ICF tracking
- session intelligence roadmap

## Current Architecture Reality

The platform already has broad feature coverage. The next phase is not basic CRUD expansion. The next phase is strengthening the structural layers that support:
- unified scheduling
- session intelligence
- finance operations
- white-label productization

## Scheduling Architecture Direction

### Current
- booking types
- weekly availability
- date overrides
- public booking pages
- single-user assumptions in some public booking flows
- direct Google token storage on `User`

### In Progress
- first-class `calendar_connections` model for multiple calendar accounts

### Target
- multiple connected calendars per coach
- aggregated busy-time calculation
- primary write-back calendar
- multi-coach routing
- branded white-label booking experience

## Session Intelligence Architecture Direction

### Current
- Fathom ingestion exists for invoice extraction workflows
- coaching sessions and ICF tracking already exist

### Target
- Zoom/Fathom meeting ingestion
- session-to-booking matching
- session-to-client matching
- automatic internal session records
- immediate client portal delivery for approved session assets
- permissioned sharing of notes/transcripts/recordings

## Finance Architecture Direction

### Current
- invoices
- payments
- recurring invoices
- expenses
- mileage
- contractors
- reporting

### Target
- unified ledger
- tax-aware categorization
- reconciliation workflow
- CPA-ready exports
- finance dashboard that reflects real business operations

## White-Label Architecture Direction

### Not Yet Implemented
- tenant/workspace isolation
- tenant branding
- tenant domain management
- tenant-level billing and feature gating

### Design Rule
- new major foundations should avoid assumptions that block future multi-tenant productization

## API / Service Boundaries

### Routers
- route handlers should stay thin
- orchestration belongs in services where complexity warrants it

### Services
- integrations, scheduling, auth, finance, and session intelligence logic should be service-driven

### Models
- domain concepts should be explicit, not hidden in token blobs or overloaded generic records
