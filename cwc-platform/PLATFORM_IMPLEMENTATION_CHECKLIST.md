# CWC Platform Implementation Checklist

This checklist is the working product plan for evolving CWC from an internal operating system into a white-label business platform for coaches and service-based businesses.

## Product Goal

Build a true all-in-one platform so coaches do not need six disconnected tools for CRM, scheduling, payments, contracts, client delivery, bookkeeping, community, and operations.

## Success Criteria

- Wendy can use core workflows daily without friction
- CWC can replace the highest-friction parts of the current tool stack
- Scheduling works across multiple calendars with one availability view
- Finance workflows are good enough for bookkeeping readiness and CPA handoff
- The platform is extensible into white-label multi-tenant SaaS

## Phase 0: Wendy Can Start Tomorrow

### Access and Stability
- [ ] Confirm reliable login flow
- [ ] Confirm production-like pilot environment for Wendy
- [ ] Confirm backups for pilot data
- [ ] Confirm fallback process if one module fails
- [ ] Create a short Wendy quick-start guide

### Day-1 Core Workflows
- [ ] Create and update client records
- [ ] View active clients and pipeline
- [ ] Create and send invoices
- [ ] Track invoice/payment status
- [ ] Create and send contracts
- [ ] Capture notes and follow-up tasks
- [ ] View schedule in one dashboard

### Pilot Readiness
- [ ] Import a small set of active clients
- [ ] Preconfigure booking types Wendy actually uses
- [ ] Preconfigure contract templates Wendy actually uses
- [ ] Preconfigure invoice defaults and payment settings
- [ ] Identify which workflows stay in old tools during pilot week

## Phase 1: Replace The Current Tool Stack

### CRM and Client Operations
- [ ] Leads, clients, and organizations managed in one place
- [ ] Interaction history and notes
- [ ] Tasks and follow-up reminders
- [ ] Simple pipeline or status views
- [ ] Search and filtering that is fast enough for daily use

### Scheduling and Booking
- [ ] Booking types with duration, price, buffers, and notice rules
- [ ] Public booking links
- [ ] Reschedule and cancellation flows
- [ ] Availability settings UI
- [ ] Booking reminders and confirmation messaging

### Contracts and Payments
- [ ] Reusable contract templates
- [ ] E-signature flow
- [ ] Invoice creation from client workflow
- [ ] Payment collection and status tracking
- [ ] Recurring invoices and subscriptions where relevant

### Client Delivery
- [ ] Client portal
- [ ] Goals and action items
- [ ] Notes/resources sharing
- [ ] Session notes and recaps visible in client portal
- [ ] Session recordings visible in client portal where permitted
- [ ] Session transcripts visible in client portal where permitted
- [ ] Immediate post-session delivery workflow for clients
- [ ] Offboarding and feedback workflows
- [ ] Testimonials and social proof capture

## Phase 2: Scheduling Differentiator

### Unified Availability Engine
- [ ] Support multiple connected calendars per coach
- [ ] Aggregate busy time across all connected calendars
- [ ] Show one unified availability view
- [ ] Prevent conflicts across all connected calendars
- [ ] Choose a primary write-back calendar for bookings
- [ ] Optional mirror/block behavior for secondary calendars

### Calendar Integrations
- [ ] Google personal calendar support
- [ ] Google Workspace calendar support
- [ ] Microsoft personal calendar support
- [ ] Microsoft 365 business calendar support
- [ ] ICS/import fallback where direct sync is not available
- [ ] Calendar connection management UI

### Tool Replacement / Migration
- [ ] Calendly migration plan
- [ ] Import or recreate booking types from existing tools
- [ ] Redirect or replace old booking links
- [ ] Motion integration strategy
- [ ] Unified busy-time compatibility with task-based calendar tools

### White-Label Booking Experience
- [ ] Tenant-specific booking page branding
- [ ] Logo, brand colors, and typography controls
- [ ] Custom page sections and messaging
- [ ] Custom confirmation emails
- [ ] Custom domains or branded subdomains
- [ ] Multi-coach routing instead of single-user assumptions

## Phase 2.5: Coaching Session Intelligence

### Meeting Platform Ingestion
- [ ] Zoom integration for meeting ingestion
- [ ] Fathom integration for transcript and note ingestion
- [ ] Session-to-client matching logic
- [ ] Session-to-booking matching logic
- [ ] Support internal session records from meeting data
- [ ] Back-burner roadmap for Google Meet
- [ ] Back-burner roadmap for Microsoft Teams
- [ ] Back-burner roadmap for other meeting platforms

### ICF Hours Automation
- [ ] Auto-log ICF coaching hours from completed sessions
- [ ] Classify session type for ICF tracking
- [ ] Review/override workflow for incorrectly classified sessions
- [ ] ICF reporting dashboard fed by meeting data
- [ ] Session completion reconciliation for certification accuracy

### Client Session Delivery
- [ ] Publish approved Fathom notes to client portal immediately
- [ ] Publish approved video/recording links to client portal immediately
- [ ] Publish approved transcripts to client portal immediately
- [ ] Generate and publish session summaries
- [ ] Generate and publish homework/action items
- [ ] Generate and publish next-step recommendations

### Permissions and Sharing Controls
- [ ] Coach-only internal notes
- [ ] Client-visible summary
- [ ] Client-visible transcript
- [ ] Client-visible recording
- [ ] Approval controls before auto-sharing session assets
- [ ] Per-program or per-client sharing defaults

## Phase 3: Finance, Bookkeeping, and Tax Readiness

### Finance MVP
- [ ] Unified money ledger for invoices, payments, refunds, expenses, and contractor payouts
- [ ] Chart-of-accounts-lite for coaches
- [ ] Expense tracking workflow
- [ ] Receipt/document attachment support
- [ ] Contractor payment tracking
- [ ] Mileage and reimbursement workflow
- [ ] Monthly P&L dashboard
- [ ] Cash flow view

### Tax-Ready Operations
- [ ] Tax-aware category defaults
- [ ] Quarterly tax estimate view
- [ ] Year-end contractor totals
- [ ] CPA-ready export package
- [ ] Clean CSV export for financial handoff
- [ ] Audit log for financial record changes

### Bookkeeping Workflow
- [ ] Manual transaction entry
- [ ] Bank import support
- [ ] Reconciliation workflow
- [ ] Matched/unmatched transaction states
- [ ] Close-the-month checklist
- [ ] Owner dashboard for revenue, expenses, profit, taxes

## Phase 4: Community and Content Layer

### Kajabi/Circle/Skool Replacement Direction
- [ ] Community space inside the platform
- [ ] Cohort or membership groups
- [ ] Content library and course delivery
- [ ] Events and live-session access
- [ ] Discussion threads or community feed
- [ ] Member progress and engagement tracking

### Business Integration
- [ ] Community tied to client records and purchases
- [ ] Access control based on offer/program membership
- [ ] Billing linked to content/community access
- [ ] Upsell/cross-sell flows from CRM and program status
- [ ] Shared reporting across coaching, content, and revenue

## Phase 5: White-Label SaaS Productization

### Multi-Tenant Architecture
- [ ] Tenant/workspace model
- [ ] Strict data isolation between brands
- [ ] Role and permission model per tenant
- [ ] Tenant-level settings
- [ ] Tenant-level templates and workflows
- [ ] Tenant-level branding and domains

### SaaS Operations
- [ ] Subscription and billing plans for tenants
- [ ] Self-serve onboarding for new coaches
- [ ] Trial/demo workspace flow
- [ ] Usage limits and feature gating
- [ ] Support/admin tooling
- [ ] Analytics for tenant health and adoption

### White-Label Experience
- [ ] Brandable login and portal
- [ ] Brandable client emails
- [ ] Brandable booking links
- [ ] Brandable invoices/contracts/client portal
- [ ] Optional custom domain setup flow

## Phase 6: Marketing, Funnels, and Email Growth

### Mailchimp / Kajabi-Style Growth Layer
- [ ] Audience lists tied to CRM contacts and lead sources
- [ ] Tags and segments based on lifecycle stage, offer, and engagement
- [ ] Opt-in forms and lead capture flows
- [ ] Landing pages for lead magnets, webinars, and offers
- [ ] Email template builder for campaigns and nurture sequences
- [ ] Broadcast emails for announcements and launches
- [ ] Automated email sequences for nurture, onboarding, follow-up, and re-engagement
- [ ] Funnel tracking from opt-in to booking to purchase
- [ ] Conversion reporting for campaigns, landing pages, and offers
- [ ] Suppression/unsubscribe management and email preferences

### Business Integration
- [ ] Funnel entry points tied to booking links and CRM records
- [ ] Contact timeline showing campaign activity and engagement
- [ ] Purchase and program access automation from funnel outcomes
- [ ] Trigger sequences from contracts, invoices, bookings, and portal events
- [ ] Shared reporting across marketing, scheduling, revenue, and delivery

### Positioning Rule
- [ ] Do not build a generic email-marketing platform first
- [ ] Build funnel and campaign capability that reduces tool sprawl for coaching businesses
- [ ] Keep the product anchored in CRM, booking, payment, delivery, and business operations

## Phase 7: Migration and Cost-Savings Story

### Migration Infrastructure
- [ ] CSV imports for contacts, invoices, bookings, and tasks
- [ ] Migration helpers for Calendly
- [ ] Migration helpers for HoneyBook
- [ ] Migration helpers for Kajabi/community exports
- [ ] Migration helpers for bookkeeping spreadsheets

### Business Case
- [ ] Tool replacement calculator
- [ ] Cost comparison vs multi-tool stack
- [ ] Time-saved dashboard
- [ ] “What you can cancel now” migration checklist

## Competitive Positioning Checklist

### Against Paperbell
- [ ] Match core coaching booking/payment/contract basics
- [ ] Exceed on CRM depth
- [ ] Exceed on operations and workflow automation
- [ ] Exceed on finance and bookkeeping readiness

### Against HoneyBook
- [ ] Match core clientflow and invoicing workflows
- [ ] Exceed on coaching-specific delivery workflows
- [ ] Exceed on client progress, portal, and coaching operations
- [ ] Exceed on coach-specific scheduling and program management

### Against Kajabi
- [ ] Match enough content/community value to reduce tool sprawl
- [ ] Exceed on service-business operations
- [ ] Tie content, coaching, billing, and CRM together
- [ ] Avoid becoming “just another course platform”

## Immediate Priorities

### Must Decide Now
- [ ] Define Wendy pilot scope for week 1
- [ ] Define the exact current tool stack being replaced
- [ ] Rank modules by pain, not by ambition
- [ ] Choose which features are internal-only vs SaaS-ready now

### Must Build Soon
- [ ] Unified availability across multiple calendars
- [ ] Booking page branding system
- [ ] Finance ledger foundation
- [ ] CPA export workflow
- [ ] White-label architecture plan
- [ ] Migration/import tooling

## Operating Rhythm

- [ ] Review this checklist weekly
- [ ] Mark each item as `not started`, `in progress`, `blocked`, or `done`
- [ ] Convert top priorities into implementation tickets
- [ ] Keep Wendy feedback separate from long-term SaaS ideas
- [ ] Re-rank backlog after each real usage milestone
