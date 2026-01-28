# CWC Platform - Unified Coaching Business System
## Architecture & Scope Document v1.0

---

## Executive Summary

A custom-built platform to unify all business operations for Coaching Women of Color, replacing:
- **HoneyBook** → CRM + Client Portal + Contracts + Invoicing
- **Calendly** → Intelligent Scheduling Engine
- **DocuSign** → Native E-Signature System
- **Motion** → AI Task & Project Management
- **Wave** → Accounting & Financial Reporting

**External Integration (Keep):** Gmail Suite (Email, Google Calendar, Google Drive)

---

## Core Platform Modules

### 1. CLIENT RELATIONSHIP MANAGEMENT (CRM)

**Replaces:** HoneyBook CRM

| Feature | Description |
|---------|-------------|
| Contact Database | Organizations + Individual contacts with relationship mapping |
| Lead Pipeline | Customizable stages: Inquiry → Discovery → Proposal → Closed Won/Lost |
| Interaction History | All emails, calls, meetings, notes in one timeline |
| Tags & Segments | B2B (Organizations) vs B2C (Individual Coaching) segmentation |
| Client Portal | Branded login for clients to view contracts, invoices, schedule sessions |

**Data Model - Contacts:**
```
Organization
├── id, name, industry, size, website
├── primary_contact_id (FK → Contact)
├── billing_contact_id (FK → Contact)
├── tags[], segment, source
├── lifetime_value, status
└── created_at, updated_at

Contact
├── id, first_name, last_name, email, phone
├── organization_id (FK → Organization, nullable for B2C)
├── role, title
├── type: 'lead' | 'client' | 'past_client' | 'partner'
├── coaching_type: 'executive' | 'life' | 'group' | null
├── tags[], source
└── created_at, updated_at

Interaction
├── id, contact_id, type: 'email' | 'call' | 'meeting' | 'note'
├── subject, content, direction: 'inbound' | 'outbound'
├── gmail_message_id (for sync)
└── created_at, created_by
```

---

### 2. SCHEDULING ENGINE

**Replaces:** Calendly

| Feature | Description |
|---------|-------------|
| Booking Pages | Public URLs for different session types (Discovery, Coaching, Workshop) |
| Availability Rules | Working hours, buffer times, minimum notice, max per day |
| Calendar Sync | Two-way sync with Google Calendar |
| Smart Scheduling | AI suggestions for optimal meeting times based on energy/focus patterns |
| Intake Forms | Custom questions per booking type |
| Reminders | Automated email/SMS reminders (24hr, 1hr) |
| Rescheduling | Self-service reschedule/cancel with policies |
| Group Booking | For workshops and group coaching sessions |

**Data Model - Scheduling:**
```
BookingType
├── id, name, slug, duration_minutes
├── description, color
├── price (nullable - for paid sessions)
├── intake_form_id (FK → Form)
├── buffer_before, buffer_after
├── min_notice_hours, max_advance_days
├── max_per_day, requires_approval
└── is_active, created_at

Availability
├── id, user_id, day_of_week
├── start_time, end_time
├── is_recurring, specific_date (for overrides)
└── booking_type_ids[] (which types use this availability)

Booking
├── id, booking_type_id, contact_id
├── start_datetime, end_datetime
├── status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
├── google_event_id (for sync)
├── intake_responses (JSONB)
├── notes, cancellation_reason
├── reminder_sent_at, follow_up_sent_at
└── created_at, updated_at
```

---

### 3. CONTRACTS & E-SIGNATURES

**Replaces:** DocuSign + HoneyBook Contracts

| Feature | Description |
|---------|-------------|
| Template Library | Reusable contract templates with merge fields |
| Document Builder | WYSIWYG editor for creating/customizing contracts |
| E-Signature | Legally binding electronic signatures (audit trail) |
| Merge Fields | Auto-populate client name, dates, pricing, etc. |
| Versioning | Track document revisions |
| Countersigning | Support for multiple signers |
| Expiration | Auto-expire unsigned contracts |

**Data Model - Contracts:**
```
ContractTemplate
├── id, name, description
├── content (HTML/Markdown with merge fields)
├── category: 'coaching' | 'workshop' | 'consulting' | 'speaking'
├── default_expiry_days
└── is_active, created_at, updated_at

Contract
├── id, template_id, contact_id, organization_id
├── title, content (rendered with merged values)
├── status: 'draft' | 'sent' | 'viewed' | 'signed' | 'expired' | 'declined'
├── sent_at, viewed_at, signed_at, expires_at
├── signer_name, signer_email, signer_ip
├── signature_data (base64 image or typed)
├── signature_hash (for verification)
├── linked_invoice_id (FK → Invoice)
├── linked_project_id (FK → Project)
└── created_at, updated_at

SignatureAuditLog
├── id, contract_id
├── action: 'created' | 'sent' | 'viewed' | 'signed' | 'declined'
├── ip_address, user_agent
├── actor_email
└── created_at
```

---

### 4. INVOICING & PAYMENTS

**Replaces:** HoneyBook Invoicing + Wave Invoicing

| Feature | Description |
|---------|-------------|
| Invoice Builder | Line items, taxes, discounts, payment terms |
| Recurring Invoices | For retainer clients and coaching packages |
| Payment Processing | Stripe integration for cards + ACH |
| Payment Plans | Split payments with automatic charging |
| Late Payment Reminders | Automated follow-ups |
| Deposits | Require deposit before booking confirmation |
| Refunds | Process full/partial refunds |
| Receipt Generation | Automatic receipts on payment |

**Data Model - Invoicing:**
```
Invoice
├── id, invoice_number, contact_id, organization_id
├── status: 'draft' | 'sent' | 'viewed' | 'partial' | 'paid' | 'overdue' | 'void'
├── issue_date, due_date
├── subtotal, tax_rate, tax_amount, discount_amount, total
├── amount_paid, balance_due
├── currency, payment_terms
├── notes, footer_text
├── contract_id (FK → Contract)
├── project_id (FK → Project)
├── sent_at, viewed_at, paid_at
└── created_at, updated_at

InvoiceLineItem
├── id, invoice_id
├── description, quantity, unit_price, amount
├── service_type: 'coaching' | 'workshop' | 'consulting' | 'speaking' | 'other'
└── sort_order

Payment
├── id, invoice_id, contact_id
├── amount, payment_method: 'card' | 'ach' | 'check' | 'cash' | 'other'
├── stripe_payment_id, stripe_charge_id
├── status: 'pending' | 'succeeded' | 'failed' | 'refunded'
├── refund_amount, refund_reason, refunded_at
├── receipt_url, receipt_sent_at
└── created_at

PaymentPlan
├── id, invoice_id
├── total_installments, installment_amount
├── frequency: 'weekly' | 'biweekly' | 'monthly'
├── next_charge_date, installments_remaining
└── stripe_subscription_id, status
```

---

### 5. PROJECT & TASK MANAGEMENT

**Replaces:** Motion

| Feature | Description |
|---------|-------------|
| Projects | Organize work by client engagement |
| Tasks | Assignable tasks with due dates, priorities |
| AI Scheduling | Auto-schedule tasks based on deadlines and capacity |
| Time Blocking | Integrate with calendar for focused work |
| Templates | Project templates for common engagements |
| Progress Tracking | Kanban boards, timelines, completion % |
| Dependencies | Task dependencies and critical path |
| Client Visibility | Optional client access to project status |

**Data Model - Projects:**
```
Project
├── id, name, description
├── contact_id, organization_id
├── project_type: 'coaching_engagement' | 'workshop' | 'consulting' | 'speaking'
├── status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled'
├── start_date, end_date, actual_end_date
├── budget, actual_spend
├── contract_id (FK → Contract)
├── template_id (FK → ProjectTemplate)
├── progress_percent
└── created_at, updated_at

Task
├── id, project_id (nullable for standalone tasks)
├── title, description
├── status: 'todo' | 'in_progress' | 'blocked' | 'done'
├── priority: 'low' | 'medium' | 'high' | 'urgent'
├── due_date, due_time
├── estimated_minutes, actual_minutes
├── assigned_to, created_by
├── parent_task_id (for subtasks)
├── dependencies[] (task IDs)
├── scheduled_start (AI-assigned time block)
├── tags[], is_recurring
└── created_at, updated_at, completed_at

ProjectTemplate
├── id, name, description
├── project_type
├── default_tasks (JSONB array of task templates)
├── default_duration_days
└── is_active
```

---

### 6. ACCOUNTING & FINANCIAL REPORTING

**Replaces:** Wave

| Feature | Description |
|---------|-------------|
| Chart of Accounts | Standard accounts for coaching business |
| Income Tracking | Auto-categorized from payments |
| Expense Tracking | Manual entry + receipt upload + bank sync |
| Bank Reconciliation | Match transactions to records |
| Financial Reports | P&L, Balance Sheet, Cash Flow |
| Tax Preparation | Quarterly estimates, annual summaries |
| Multi-Currency | USD primary, support for international clients |

**Data Model - Accounting:**
```
Account
├── id, name, code
├── type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
├── subtype, description
├── balance, is_system, is_active
└── created_at, updated_at

Transaction
├── id, date, description
├── type: 'income' | 'expense' | 'transfer' | 'adjustment'
├── amount, account_id
├── contact_id (nullable)
├── payment_id (FK → Payment, for income)
├── receipt_url, receipt_filename
├── is_reconciled, reconciled_at
├── category, tags[]
└── created_at, updated_at

BankConnection
├── id, institution_name, account_name
├── plaid_access_token, plaid_item_id
├── last_sync_at, sync_status
└── is_active

JournalEntry
├── id, date, description, reference
├── debits (JSONB: [{account_id, amount}])
├── credits (JSONB: [{account_id, amount}])
├── is_adjusting, created_by
└── created_at
```

---

### 7. EMAIL & COMMUNICATION HUB

**Integrates with:** Gmail Suite

| Feature | Description |
|---------|-------------|
| Gmail Sync | Two-way sync of client emails |
| Email Templates | Reusable templates for common communications |
| Sequences | Automated email sequences (onboarding, follow-up) |
| Tracking | Open/click tracking |
| Unified Inbox | All client communication in one view |
| SMS (Future) | Twilio integration for text messages |

**Data Model - Communications:**
```
EmailTemplate
├── id, name, subject, body (HTML)
├── category: 'inquiry' | 'onboarding' | 'reminder' | 'follow_up' | 'invoice'
├── merge_fields[]
└── is_active, created_at, updated_at

EmailSequence
├── id, name, description
├── trigger: 'manual' | 'new_lead' | 'contract_signed' | 'session_completed'
├── steps (JSONB: [{delay_days, template_id, condition}])
└── is_active

SequenceEnrollment
├── id, sequence_id, contact_id
├── current_step, status: 'active' | 'completed' | 'paused' | 'unsubscribed'
├── started_at, completed_at
├── next_email_at
└── created_at
```

---

### 8. AI INVOICE EXTRACTION (Fathom Integration)

**New Module - Replaces manual invoice creation**

| Feature | Description |
|---------|-------------|
| Fathom Webhook Receiver | Direct API integration - no Zapier needed |
| Transcript Ingestion | Receives full transcript + AI summary + action items |
| AI Extraction Engine | Claude API analyzes transcript against Pricing Rules |
| Draft Invoice Generation | Auto-creates invoice with extracted data |
| Confidence Scoring | Shows extraction confidence per field |
| Human Review Queue | All drafts require approval before sending |
| Learning Loop | Your corrections improve future extractions |
| Payment Reminder Automation | Auto-follow-up on overdue invoices |

**Data Model - AI Extraction:**
```
FathomWebhook
├── id, recording_id, meeting_title
├── transcript (full text)
├── summary (Fathom AI summary)
├── action_items (JSONB)
├── attendees (JSONB: [{name, email, is_external}])
├── duration_seconds, recorded_at
├── processed_at, processing_status
└── created_at

InvoiceExtraction
├── id, fathom_webhook_id, contact_id
├── extracted_data (JSONB)
│   ├── client_name, client_email
│   ├── service_type, scope
│   ├── price_discussed, timeline
│   └── special_requests
├── confidence_scores (JSONB: {field: score})
├── draft_invoice_id (FK → Invoice)
├── status: 'pending' | 'reviewed' | 'approved' | 'rejected'
├── corrections (JSONB: [{field, original, corrected}])
├── reviewed_at, reviewed_by
└── created_at

ExtractionRule
├── id, rule_type: 'pricing' | 'client_match' | 'service_type'
├── trigger_phrases[] 
├── extraction_pattern
├── confidence_weight
├── learned_from_corrections: integer
└── is_active, created_at, updated_at
```

**Fathom API Integration:**
```
Webhook Setup:
POST https://api.fathom.ai/external/v1/webhooks
{
  "destination_url": "https://app.cwcplatform.com/api/webhooks/fathom",
  "triggered_for": ["my_recordings"],
  "include_transcript": true,
  "include_summary": true,
  "include_action_items": true
}

Webhook Payload Received:
{
  "recording_id": "123456",
  "title": "Discovery Call - Jane Smith",
  "transcript": [...],
  "default_summary": {...},
  "action_items": [...],
  "calendar_invitees": [...]
}
```

**Extraction Flow:**
```
1. Fathom webhook arrives
2. Match attendee email to existing Contact (or create new)
3. Claude API analyzes:
   - Transcript content
   - Pricing Rules document (/config/pricing-rules.md)
   - Client history (previous invoices, contracts)
4. Generate draft invoice with confidence scores
5. Queue for review if confidence < 85%
6. Notify user: "New draft invoice ready for review"
7. User approves/edits → Invoice sent
8. Corrections logged → Rules refined
```

**Reminder Automation:**
```
Invoice sent
    ↓
Due date approaching (3 days) → Friendly reminder email
    ↓
Due date passed (1 day) → "Payment due" email
    ↓
3 days overdue → "Gentle follow-up" email
    ↓
7 days overdue → "Action required" email
    ↓
14 days overdue → Flag for personal follow-up + optional late fee
```

---

### 9. FULL BOOKKEEPING (Bank/Credit Card Connections)

**Replaces:** Wave accounting backend

| Feature | Description |
|---------|-------------|
| Bank Account Connections | Plaid integration - 12,000+ institutions |
| Credit Card Feeds | Automatic transaction import |
| Auto-Categorization | AI categorizes expenses (customizable rules) |
| Receipt Capture | Upload/photograph receipts, match to transactions |
| Reconciliation | Match bank feed to recorded transactions |
| Chart of Accounts | Standard coaching business accounts |
| Tax Categories | Map expenses to Schedule C |
| Financial Reports | P&L, Balance Sheet, Cash Flow |
| Tax Prep Export | Quarterly estimates, annual summaries |

**Data Model - Bookkeeping:**
```
BankConnection
├── id, institution_name, institution_id
├── account_name, account_type: 'checking' | 'savings' | 'credit'
├── account_mask (last 4 digits)
├── plaid_access_token (encrypted)
├── plaid_item_id, plaid_account_id
├── current_balance, available_balance
├── last_sync_at, sync_status, sync_error
└── is_active, created_at

BankTransaction
├── id, bank_connection_id
├── plaid_transaction_id (for deduplication)
├── date, description, amount
├── type: 'debit' | 'credit'
├── category_id (FK → ExpenseCategory)
├── merchant_name, merchant_category
├── is_pending, is_reconciled
├── matched_transaction_id (FK → Transaction)
├── receipt_id (FK → Receipt)
├── notes, tags[]
└── created_at, updated_at

ExpenseCategory
├── id, name, parent_id (for hierarchy)
├── type: 'income' | 'expense' | 'transfer'
├── tax_category: 'advertising' | 'travel' | 'supplies' | etc.
├── is_tax_deductible, tax_line (Schedule C line)
├── auto_rules (JSONB: [{match_field, pattern, confidence}])
├── is_system, is_active
└── created_at

Receipt
├── id, file_url, file_name
├── upload_source: 'web' | 'mobile' | 'email'
├── extracted_data (JSONB: {vendor, amount, date, items})
├── extraction_confidence
├── matched_transaction_id
├── status: 'unmatched' | 'matched' | 'archived'
└── created_at

Reconciliation
├── id, bank_connection_id
├── statement_date, statement_balance
├── reconciled_balance, difference
├── status: 'in_progress' | 'completed' | 'has_discrepancy'
├── completed_at, completed_by
└── created_at
```

**Plaid Integration Flow:**
```
1. User clicks "Connect Bank Account"
2. Plaid Link opens in modal
3. User authenticates with their bank
4. Plaid returns access_token
5. We fetch account info + initial transactions
6. Daily sync job pulls new transactions
7. AI auto-categorizes based on merchant + rules
8. User reviews/corrects categories
9. System learns from corrections
```

**Auto-Categorization Rules (Default):**
```
Business Expenses:
- "ZOOM" → Software & Subscriptions
- "CANVA", "ADOBE" → Software & Subscriptions
- "UBER", "LYFT" → Travel - Local
- "DELTA", "UNITED", "AMERICAN" → Travel - Airfare
- "MARRIOTT", "HILTON", "AIRBNB" → Travel - Lodging
- "STAPLES", "OFFICE DEPOT" → Office Supplies
- "LINKEDIN", "FACEBOOK", "GOOGLE ADS" → Advertising
- "MAILCHIMP", "CONVERTKIT" → Marketing
- etc.

Income:
- "STRIPE" → Coaching Income
- "PAYPAL" → Coaching Income (or split by source)
```

**Tax Preparation Features:**
```
Quarterly Estimate Calculator:
- Pulls income + expenses for quarter
- Applies estimated tax rate
- Generates payment voucher

Annual Summary:
- Schedule C category totals
- Mileage log (if tracked)
- Home office deduction calculator
- Export to CSV for accountant
```

---

## Tech Stack Recommendation

### Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | **FastAPI** (Python) | Async, fast, great for APIs, matches your AOP stack |
| Database | **PostgreSQL** | Robust, JSONB support, great for complex queries |
| ORM | **SQLAlchemy 2.0** | Async support, mature ecosystem |
| Task Queue | **Celery + Redis** | Background jobs (emails, reminders, syncs) |
| Caching | **Redis** | Session storage, caching, rate limiting |

### Frontend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | **React + TypeScript** | Matches your NICEHR stack |
| UI Library | **Tailwind + shadcn/ui** | Fast development, professional look |
| State | **TanStack Query** | Server state management |
| Forms | **React Hook Form + Zod** | Validation, complex forms |

### Integrations
| Service | Purpose |
|---------|---------|
| **Stripe** | Payments, subscriptions, payment plans |
| **Google APIs** | Calendar sync, Gmail sync, Drive (optional) |
| **Plaid** | Bank account connections (accounting) |
| **Twilio** | SMS reminders (Phase 2) |
| **SendGrid** | Transactional email delivery |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Hosting | **Railway** or **Render** (start), **AWS** (scale) |
| File Storage | **AWS S3** or **Cloudflare R2** |
| CDN | **Cloudflare** |
| Monitoring | **Sentry** + **Posthog** |

---

## Development Phases

### PHASE 1: Foundation (Weeks 1-4)
- [ ] Project setup, database schema, authentication
- [ ] Core CRM: Contacts, Organizations, Basic CRUD
- [ ] Client Portal: Login, dashboard shell
- [ ] Basic UI framework and navigation
- [ ] Fathom API key setup + webhook endpoint (receive only)

### PHASE 2: Scheduling (Weeks 5-8)
- [ ] Booking types and availability management
- [ ] Public booking pages
- [ ] Google Calendar two-way sync
- [ ] Intake forms
- [ ] Email confirmations and reminders

### PHASE 3: Invoicing + AI Extraction (Weeks 9-14)
- [ ] Invoice builder
- [ ] Stripe integration
- [ ] Payment processing + payment plans
- [ ] Receipts and reminders
- [ ] **Fathom transcript processing**
- [ ] **Claude API invoice extraction**
- [ ] **Pricing Rules document integration**
- [ ] **Draft review queue + approval workflow**
- [ ] **Auto-reminder sequences for overdue invoices**

### PHASE 4: Contracts (Weeks 15-18)
- [ ] Contract template builder
- [ ] E-signature capture with audit trail
- [ ] PDF generation
- [ ] Contract → Invoice → Client workflow

### PHASE 5: Bookkeeping (Weeks 19-24)
- [ ] Chart of accounts setup
- [ ] **Plaid integration + bank connections**
- [ ] **Credit card feed import**
- [ ] Transaction categorization + AI auto-categorize
- [ ] Receipt capture + matching
- [ ] Bank reconciliation
- [ ] Financial reports (P&L, Balance Sheet)
- [ ] Tax category mapping + export

### PHASE 6: Projects & Tasks (Weeks 25-28)
- [ ] Project management
- [ ] Task system with dependencies
- [ ] AI task scheduling
- [ ] Project templates

### PHASE 7: Polish & Launch (Weeks 29-32)
- [ ] Email sequences
- [ ] Dashboard analytics
- [ ] Mobile responsiveness
- [ ] Data migration from existing tools
- [ ] Testing and bug fixes
- [ ] Learning loop refinement for AI extraction

---

## Estimated Effort (Updated)

| Phase | Weeks | Core Features |
|-------|-------|---------------|
| 1 | 4 | Foundation + CRM + Fathom webhook |
| 2 | 4 | Scheduling Engine |
| 3 | 6 | Invoicing + AI Extraction + Reminders |
| 4 | 4 | Contracts + E-Sign |
| 5 | 6 | Full Bookkeeping + Bank Connections |
| 6 | 4 | Projects + Tasks |
| 7 | 4 | Polish + Launch |
| **Total** | **32 weeks** | Full Platform |

**MVP Option:** Phases 1-3 = 14 weeks for CRM + Scheduling + Invoicing with AI Extraction

---

## Monthly Infrastructure Cost Estimate

| Item | Monthly Cost |
|------|--------------|
| Railway hosting (web + worker) | ~$40/mo |
| PostgreSQL (Railway or Neon) | ~$20/mo |
| Redis (Upstash) | $0-10/mo |
| Plaid (3-4 bank/card connections) | ~$5-10/mo |
| Stripe (payment processing) | 2.9% + $0.30/txn |
| Claude API (invoice extraction) | ~$5-20/mo |
| SendGrid (transactional email) | $0 (free tier) |
| S3/R2 storage (receipts, files) | ~$2-5/mo |
| Domain + SSL | ~$1/mo |
| **TOTAL INFRASTRUCTURE** | **~$75-110/mo** |

**You keep:** Google Workspace (~$12/mo) for email/calendar

---

## Key Differentiators from Off-the-Shelf

1. **Unified Data Model** - No more duplicate entry, everything connected
2. **Coaching-Specific Workflows** - Built for B2B + B2C coaching business
3. **AI-Powered Invoice Extraction** - Transcripts → Draft invoices automatically
4. **Never Forget to Collect** - Automated payment reminders
5. **Full Ownership** - Your data, your platform, no monthly SaaS fees
6. **Learning System** - Gets smarter from your corrections over time
7. **True Bookkeeping** - Bank/credit card connections, not just invoicing

---

## Required Setup (Before We Build)

### You Need to Get:

| Item | Where | Notes |
|------|-------|-------|
| Fathom API Key | Fathom Settings → API Access | For transcript integration |
| Stripe Account | stripe.com | For payment processing |
| Plaid Account | plaid.com | For bank connections (we'll set up) |
| Google Cloud Project | console.cloud.google.com | For Calendar/Gmail API |
| Domain Name | Your registrar | e.g., app.coachingwomenofcolor.com |

### Documents to Prepare:

| Document | Status | Notes |
|----------|--------|-------|
| Pricing Rules (pricing-rules.md) | Template created | Fill in checklist |
| Contract Templates | Needed | Your existing contracts |
| Email Templates | Needed | Welcome, reminder, follow-up emails |
| Branding Assets | Needed | Logo, colors, fonts |

---

## Next Steps

1. ✅ Architecture document created
2. ✅ Pricing Rules template created  
3. ✅ Pricing Checklist created (for you to complete)
4. ⬜ **You:** Complete pricing checklist (send back sections as you finish)
5. ⬜ **You:** Get Fathom API key
6. ⬜ **You:** Create Stripe account (if not existing)
7. ⬜ **Claude:** Initialize project repository
8. ⬜ **Claude:** Set up database schema for Phase 1
9. ⬜ **Claude:** Build authentication system
10. ⬜ **Claude:** Create first CRM screens

---

*Document created: December 28, 2025*
*Version: 1.1 - Added AI Invoice Extraction + Full Bookkeeping*
