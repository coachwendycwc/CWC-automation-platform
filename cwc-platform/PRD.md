# CWC Platform PRD

## Product

**Name:** CWC Platform

**Initial Operator:** Coaching Women of Color

**Long-Term Direction:** White-label business operating system for coaches and service-based businesses

## One-Line Purpose

Replace six or more disconnected tools with one platform for client management, scheduling, contracts, payments, delivery, bookkeeping readiness, session intelligence, and eventually community.

## Product Vision

CWC Platform should become the system a coaching business actually runs on, not just a booking tool or a client portal. It should unify front-office workflow, service delivery, and back-office operations in one place.

## Primary Users

### Current
- Wendy and the internal CWC operating team

### Near-Term
- Coaches and operators inside the CWC business

### Long-Term
- Independent coaches
- Multi-coach firms
- Service-based businesses needing white-labeled client operations

## Product Pillars

### 1. Business Operating System
- CRM
- contracts
- invoicing
- payments
- tasks
- reporting

### 2. Unified Scheduling
- one branded booking experience
- one source of truth for availability
- multiple connected calendars
- conflict prevention across calendars

### 3. Coaching Session Intelligence
- Zoom/Fathom ingestion
- session records
- ICF hours automation
- client recap delivery
- transcript and recording access controls

### 4. Finance and Bookkeeping Readiness
- unified ledger
- expenses and contractor tracking
- tax-aware categorization
- CPA-ready exports

### 5. Client Experience
- client portal
- notes
- resources
- goals
- action items
- session recap delivery

### 6. Community and Content
- content delivery
- memberships/cohorts
- discussion/community
- Kajabi/Circle/Skool replacement over time

### 7. White-Label Productization
- multi-tenant architecture
- tenant branding
- branded domains
- coach-facing SaaS onboarding

## Immediate Objective

Get Wendy successfully using the platform for daily operations as soon as possible, then expand from a live working system instead of a speculative roadmap.

## Success Criteria

- Wendy can use core workflows without major blockers
- CWC can replace the most painful current tools
- scheduling becomes unified instead of fragmented
- session intelligence reduces manual admin work
- finance workflows become CPA-ready over time
- the architecture can support white-label productization

## Current Tool-Replacement Direction

The platform should replace or absorb the need for categories of tools such as:
- scheduling tools like Calendly
- calendar coordination tools like Motion
- coaching ops tools like Paperbell
- client workflow tools like HoneyBook
- content/community tools like Kajabi, Circle, or Skool
- bookkeeping/admin spreadsheets and fragmented finance workflows

## Non-Goals

- Do not build generic software for every type of business first
- Do not prioritize broad white-label SaaS before CWC itself succeeds on the platform
- Do not build a full accounting suite before tax-ready bookkeeping workflows exist
- Do not try to out-Kajabi Kajabi on creator marketing before core business operations are excellent
- Do not add features that do not reduce tool sprawl, increase operational leverage, or strengthen a long-term differentiator

## Hard Constraints

### Product
- Wendy adoption comes before broad SaaS ambition
- real workflow fit matters more than feature count
- the platform should remove admin burden, not add more setup burden

### Technical
- Backend: FastAPI + SQLAlchemy async
- Frontend: Next.js 14 + TypeScript
- Prefer additive evolution over risky rewrites
- Preserve backward compatibility when creating new platform foundations where practical

### Business
- CWC is the proving ground
- White-label is a later phase, not the first ship target
- Replacing multiple subscriptions should become part of the business case

## Architecture Principles

- Build domain foundations before UI polish for major new systems
- Treat integrations as first-class product capabilities, not side scripts
- Keep data models multi-tenant-friendly even before full tenant rollout
- Separate internal-only workflow logic from future SaaS-facing abstractions
- Use explicit workflow states and auditability for finance and client delivery

## Rollout Phases

### Phase 0
- Wendy pilot reliability

### Phase 1
- replace core operating stack

### Phase 2
- unified multi-calendar scheduling

### Phase 2.5
- coaching session intelligence

### Phase 3
- finance/bookkeeping/tax readiness

### Phase 4
- community/content layer

### Phase 5
- white-label SaaS productization

## Source of Truth

For detailed execution and sequencing, use:
- [PLATFORM_IMPLEMENTATION_CHECKLIST.md](./PLATFORM_IMPLEMENTATION_CHECKLIST.md)
- [PRIORITIZED_EXECUTION_PLAN.md](./PRIORITIZED_EXECUTION_PLAN.md)
- [PENDING_ITEMS.md](./PENDING_ITEMS.md)
