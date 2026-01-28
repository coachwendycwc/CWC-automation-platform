# CLAUDE.md - CWC Platform

This file provides context for Claude Code sessions working on this project.

## Project Overview

CWC Platform is a unified business automation platform for "Coaching Women of Color" - a coaching and consulting business. It consolidates CRM, scheduling, invoicing, contracts, project management, and payments into a single application.

## Tech Stack

- **Backend:** FastAPI (Python 3.13) + SQLAlchemy 2.0 (async) + PostgreSQL
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Auth:** JWT tokens with email/password + Google OAuth
- **Email:** Gmail SMTP
- **Payments:** Stripe Checkout + Webhooks
- **Calendar:** Google Calendar API + FullCalendar
- **Video Storage:** Cloudinary (for testimonials)

## Project Structure

```
cwc-platform/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # FastAPI route handlers
│   │   ├── services/        # Business logic (email, stripe, calendar)
│   │   ├── config.py        # Settings from environment
│   │   ├── database.py      # Database connection
│   │   └── main.py          # FastAPI app entry point
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components (ui/, layout/)
│   │   ├── contexts/        # React contexts (AuthContext)
│   │   └── lib/             # Utilities (api.ts)
│   └── package.json
└── README.md
```

## Running the Project

### Backend (port 8001)
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### Frontend (port 3001)
```bash
cd frontend
npm run dev
```

## Implemented Features (Phases 1-13)

### Phase 1: CRM
- Contacts: CRUD, search, filters, contact types
- Organizations: CRUD, link to contacts
- Interactions: Notes and activity logging

### Phase 2: Scheduling
- Booking types with custom duration/price
- Weekly availability configuration
- Date-specific overrides
- Public booking pages: `/book/[slug]`
- Booking management: `/booking/[token]`

### Phase 3: Invoicing
- Invoice creation with line items
- Tax rates and discounts
- Payment recording (manual)
- Payment plans with installments
- Public invoice view: `/pay/[token]`

### Phase 4: Contracts
- Contract templates with merge fields ({{client_name}}, etc.)
- Contract generation from templates
- E-signature capture (drawn or typed)
- Audit logging for all contract events
- Public signing: `/sign/[token]`

### Phase 5: Projects & Tasks
- Projects linked to contacts/contracts/invoices
- Project templates for quick creation
- Tasks with status (todo/in_progress/review/completed)
- Time entries for task tracking
- Activity logging

### Phase 6: Authentication
- JWT-based authentication
- Email/password registration and login
- Google OAuth integration
- Password reset via email
- Dev login for testing

### Phase 7: Calendar & Integrations
- FullCalendar integration at `/calendar`
- Google Calendar OAuth connection
- Automatic sync of bookings to Google Calendar
- Zoom OAuth integration with auto-meeting creation
- Automated email reminders (24h and 1h before bookings)

### Phase 8: Stripe Payments
- Stripe Checkout for invoice payments
- Webhook handling for payment events
- Automatic invoice status updates on payment
- Payment confirmation emails
- Refund processing

### Phase 9: AI Invoice Extraction
- Fathom webhook integration for call transcripts
- Claude API (claude-3-5-sonnet) for transcript analysis
- AI extraction of client, service, package, and pricing
- Confidence scoring (high/medium/low)
- Review queue with approve/reject workflow
- Automatic draft invoice generation from approved extractions
- Pricing rules loaded from docs folder

### Phase 10: Reports & Analytics
- Dashboard with revenue stats and charts
- Monthly revenue bar chart (Recharts)
- Invoice aging report (current, 1-30, 31-60, 61-90, 90+ days)
- Project hours tracking summary
- Top clients by revenue leaderboard
- Contact engagement metrics
- CSV export for invoices, payments, time entries

### Phase 11: Client Portal
- Magic link authentication (no password required)
- Three user types with different access levels:
  - **Org Admins**: Overview, Team (coachees), Billing, Contracts (org-wide)
  - **Org Coachees** (paid by org): Home, Sessions, Messages only (no billing)
  - **Independent Coachees** (pay themselves): Home, Sessions, Messages, Resources, Billing
- Session recordings with transcripts and homework (private to individual)
- Org branding (logo) for org-sponsored coachees
- Dashboard with quick stats and recent activity
- Invoice viewing and Stripe payment integration
- Contract viewing and signing
- Booking management (upcoming and past)
- Project progress tracking
- Profile management
- Content/Resources delivery system with categories
- Two-way notes/messaging between coach and clients
- Email notifications for new messages (Gmail SMTP)
- Public routes: `/client/login`, `/client/verify/[token]`
- Protected routes: `/client/dashboard`, `/client/invoices`, `/client/notes`, etc.

### Phase 12: Client Experience
- **Action Items**: Coach assigns tasks to clients
  - Admin page to create/manage action items (`/action-items`)
  - Client page to view and complete tasks (`/client/action-items`)
  - Priority levels (low/medium/high), due dates, status tracking
  - Clients can mark items as completed or skipped
- **Goal Tracking**: Goals with milestone checkpoints
  - Admin page to create goals with milestones (`/goals`)
  - Client page to view progress and check off milestones (`/client/goals`)
  - Progress auto-calculated from completed milestones
  - Categories: career, health, relationships, finance, personal, education
- **Progress Timeline**: Visual journey of client's coaching engagement
  - Aggregates: sessions, goals, milestones, action items, notes, contracts
  - Filterable by event type
  - Client page at `/client/timeline`

### Phase 13: Video Testimonials
- **Video Recording**: Browser webcam recording using MediaRecorder API
  - VideoRecorder component with camera/mic permissions
  - Start/stop/restart recording with preview
  - 2-minute max duration
  - Upload progress indicator
- **Cloudinary Integration**: Video storage and optimization
  - Auto-generated thumbnails
  - Video transformations and optimization
  - Stub mode when credentials not configured
- **Admin Management**: Full testimonial workflow
  - Request testimonials from clients (`/testimonials`)
  - Send request emails with unique recording links
  - Approve/reject submitted testimonials
  - Feature testimonials for gallery display
  - Edit quotes and transcripts
- **Public Recording Page**: Client submission (`/record/[token]`)
  - Token-based access (no login required)
  - Video recording with preview
  - Author info and permission consent
- **Public Gallery**: Showcase approved testimonials (`/gallery`)
  - Featured section at top
  - Video cards with thumbnails
  - Modal video playback
  - Quote display

### Phase 14: Offboarding & Feedback
- **Offboarding Workflows**: Manage client/project/contract endings
  - Workflow types: client, project, contract
  - Customizable checklists with completion tracking
  - Templates for reusable workflows
  - Activity logging for all events
- **Comprehensive Feedback Survey**: 6-section end-of-engagement form
  - Section 1: Overall Experience (satisfaction 1-10, NPS 0-10)
  - Section 2: Growth + Measurement (outcomes, wins, progress)
  - Section 3: Coaching Process (helpful parts, improvements)
  - Section 4: Equity, Safety, Support (psychological safety, WOC support)
  - Section 5: Testimonial (permission, written, video option)
  - Section 6: Final feedback
  - Progress indicator with section navigation
  - Video recording integrated via VideoRecorder component
- **Admin Management**: Full workflow control
  - Offboarding list page (`/offboarding`)
  - Workflow detail page (`/offboarding/[id]`)
  - New workflow creation (`/offboarding/new`)
  - Templates management (`/offboarding/templates`)
  - Send survey/testimonial/completion emails
  - View complete survey responses with all sections
  - Video testimonial playback in admin view
- **Public Survey Page**: Client submission (`/feedback/[token]`)
  - Token-based access (no login required)
  - Multi-section form with progress tracking
  - Optional video testimonial recording

### Phase 15: ICF Hours Tracker
- **Coaching Sessions Tracking**: Log and track ICF certification hours
  - Session management: date, client, type, duration, notes
  - Session types: 1-on-1 Coaching, Group Coaching, Mentor Coaching
  - Status tracking: completed, cancelled, no-show
  - ICF certification requirement tracking (100 mentor hours target)
- **Dashboard Analytics**: Progress toward ICF certification
  - Total hours tracked with percentage to goal
  - Breakdown by session type and status
  - Client statistics (total clients, hours per client)
  - Monthly trends with bar chart
- **Bulk Import**: Import historical sessions
  - Google Calendar sync for coaching events
  - Bulk import API for CSV/JSON data
- **Admin Page**: Full session management at `/icf-tracker`
  - Session list with search, filter, sort
  - Quick session entry form
  - Client filtering and stats

### Phase 16: Executive Leadership Lab (Content)
- **Program Structure**: 10-month leadership development program for WOC
  - Module 1 (January): Break Through Career Plateaus
  - Module 2 (February): Master Your Executive Presence
  - Module 3 (March): Build Your Strategic Brand
  - Module 4 (April): Navigate Bias and Lead Through It
  - Module 5 (May): Amplify Your Voice
  - Module 6 (June): Build Your Board of Advisors
  - Module 7 (July): Lead and Develop Teams
  - Module 8 (August): Lead Difficult Conversations
  - Module 9 (September): Get Promoted
  - Module 10 (October): Set the Table for Your Future (Capstone)
- **Content Format**: Interactive HTML slide decks
  - Click-to-advance navigation with arrow buttons
  - Keyboard navigation (← →) and touch/swipe support
  - Progress bar indicator
  - Modern Apple/enterprise design aesthetic
  - Design System: Source Serif 4 + Inter fonts, Teal (#2A7B8C), Warm Gold (#D4A574)
- **Worksheets by Module**:
  - **M1**: Career Growth Roadmap, Plateau Diagnostic, Stuck Loop, Momentum Planner, Relationship Map
  - **M2**: Presence Audit, Presence Strategy, Presence Practice Tracker
  - **M3**: Brand Discovery, Brand Statement, Visibility Planner
  - **M4**: Bias Log, Energy Protection
  - **M5**: Voice Assessment, Voice Practice
  - **M6**: Board Audit, Outreach Planner
  - **M7**: Team Development Planner
  - **M8**: Conversation Prep (PREP Framework)
  - **M9**: Promotion Planner (STAR Accomplishments)
  - **M10**: Future Vision
- **Repository**: https://github.com/mdxvision/cwc-executive-lab
- **Live Site**: https://mdxvision.github.io/cwc-executive-lab/

### Infrastructure
- Docker configuration (Dockerfile for backend and frontend)
- docker-compose.yml with PostgreSQL, backend, frontend services
- DEPLOYMENT.md with production deployment guide
- Environment variable examples

## API Patterns

### Authentication
- All authenticated endpoints require `Authorization: Bearer <token>` header
- Public endpoints (booking, invoice view, contract signing) use unique tokens in URL

### API Structure
- Base URL: `http://localhost:8001/api`
- Most routers include their own `/api` prefix
- List endpoints support `?search=`, `?status=`, etc.

### Common Endpoints
```
POST   /api/auth/login              # Email/password login
POST   /api/auth/register           # New user registration
POST   /api/auth/dev-login          # Development login (no password)
GET    /api/contacts                # List contacts
GET    /api/invoices                # List invoices
GET    /api/contracts               # List contracts
GET    /api/projects                # List projects
GET    /api/bookings                # List bookings
POST   /api/stripe/checkout         # Create Stripe checkout session
POST   /api/stripe/webhook          # Handle Stripe webhooks
```

### Client Portal Endpoints
```
POST   /api/client/request-login    # Send magic link email
POST   /api/client/verify-token     # Verify magic link, return session
GET    /api/client/me               # Get current client info
POST   /api/client/logout           # End session
GET    /api/client/dashboard        # Dashboard stats
GET    /api/client/invoices         # List client's invoices
GET    /api/client/contracts        # List client's contracts
GET    /api/client/sessions         # List session recordings
GET    /api/client/projects         # List client's projects
GET    /api/client/resources        # List available content/resources
GET    /api/client/notes            # List notes (both directions)
POST   /api/client/notes            # Send note to coach
GET    /api/client/organization     # Org stats (org admins only)
GET    /api/client/action-items     # List client's action items
PUT    /api/client/action-items/{id}/status  # Update status
GET    /api/client/goals            # List client's goals
PUT    /api/client/goals/{id}/milestones/{mid}/complete  # Complete milestone
GET    /api/client/timeline         # Get timeline events
```

### Admin Action Items Endpoints
```
GET    /api/action-items            # List all action items
POST   /api/action-items            # Create action item for client
PUT    /api/action-items/{id}       # Update action item
DELETE /api/action-items/{id}       # Delete action item
```

### Admin Goals Endpoints
```
GET    /api/goals                   # List all goals
POST   /api/goals                   # Create goal for client
PUT    /api/goals/{id}              # Update goal
DELETE /api/goals/{id}              # Delete goal
POST   /api/goals/{id}/milestones   # Add milestone
PUT    /api/goals/{id}/milestones/{mid}  # Update milestone
DELETE /api/goals/{id}/milestones/{mid}  # Delete milestone
```

### Admin Notes Endpoints
```
GET    /api/notes                   # List all client notes
GET    /api/notes/unread-count      # Unread count for badge
POST   /api/notes                   # Send note to client
POST   /api/notes/{id}/reply        # Reply to a note
PUT    /api/notes/{id}/read         # Mark as read
```

### Testimonials Endpoints (Admin)
```
GET    /api/testimonials            # List all testimonials
POST   /api/testimonials            # Create testimonial request
GET    /api/testimonials/{id}       # Get testimonial details
PUT    /api/testimonials/{id}       # Update (approve/reject/feature)
DELETE /api/testimonials/{id}       # Delete testimonial
POST   /api/testimonials/{id}/send  # Send request email
```

### Testimonials Endpoints (Public)
```
GET    /api/testimonials/public     # List approved for gallery
GET    /api/testimonial/{token}     # Get request info by token
POST   /api/testimonial/{token}     # Submit testimonial
GET    /api/upload/video/signature  # Get Cloudinary upload signature
POST   /api/upload/video            # Upload video file
```

### Offboarding Endpoints (Admin)
```
GET    /api/offboarding             # List all workflows
GET    /api/offboarding/stats       # Get offboarding statistics
POST   /api/offboarding/initiate    # Start new workflow
GET    /api/offboarding/{id}        # Get workflow details
PUT    /api/offboarding/{id}        # Update workflow
POST   /api/offboarding/{id}/checklist/{index}  # Toggle checklist item
POST   /api/offboarding/{id}/complete  # Mark workflow complete
POST   /api/offboarding/{id}/cancel    # Cancel workflow
GET    /api/offboarding/{id}/activity  # Get activity log
POST   /api/offboarding/{id}/send-survey  # Send survey email
POST   /api/offboarding/{id}/request-testimonial  # Send testimonial request
POST   /api/offboarding/{id}/send-completion-email  # Send completion email
```

### Offboarding Templates Endpoints
```
GET    /api/offboarding-templates   # List templates
POST   /api/offboarding-templates   # Create template
GET    /api/offboarding-templates/{id}  # Get template
PUT    /api/offboarding-templates/{id}  # Update template
DELETE /api/offboarding-templates/{id}  # Delete template
```

### ICF Hours Tracker Endpoints
```
GET    /api/icf-tracker/sessions                  # List all coaching sessions
POST   /api/icf-tracker/sessions                  # Create session
GET    /api/icf-tracker/sessions/{id}             # Get session details
PUT    /api/icf-tracker/sessions/{id}             # Update session
DELETE /api/icf-tracker/sessions/{id}             # Delete session
GET    /api/icf-tracker/dashboard                 # Dashboard stats
GET    /api/icf-tracker/clients                   # List clients with hours
POST   /api/icf-tracker/bulk-import               # Bulk import from CSV/calendar
POST   /api/icf-tracker/sync-google-calendar      # Sync from Google Calendar
```

### Feedback Endpoints (Public)
```
GET    /api/feedback/{token}        # Get survey data
POST   /api/feedback/{token}        # Submit survey response
```

## Database

Using SQLite for development (auto-created), PostgreSQL for production.

### Key Models
- User, Contact, Organization
- BookingType, Booking, Availability
- Invoice, Payment, PaymentPlan
- ContractTemplate, Contract
- Project, Task, TimeEntry, ProjectTemplate
- FathomWebhook, FathomExtraction
- ClientSession (client portal magic link sessions)
- ClientContent (resources/content delivery)
- ClientNote (two-way messaging)
- ClientActionItem (coach-assigned tasks)
- ClientGoal, GoalMilestone (goal tracking with progress)
- Testimonial (video testimonials with Cloudinary storage)
- OffboardingWorkflow, OffboardingTemplate, OffboardingActivity (end-of-engagement workflows)

## Environment Variables

### Backend Required
- `SECRET_KEY` - JWT signing key
- `FRONTEND_URL` - For email links

### Backend Optional
- `GMAIL_EMAIL` - Gmail address for sending emails
- `GMAIL_APP_PASSWORD` - Gmail app password (not regular password)
- `COACH_EMAIL` - Email to receive client note notifications
- `STRIPE_SECRET_KEY` - Stripe API
- `STRIPE_WEBHOOK_SECRET` - Webhook verification
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth
- `ANTHROPIC_API_KEY` - Claude AI for invoice extraction
- `ZOOM_CLIENT_ID` / `ZOOM_CLIENT_SECRET` - Zoom meeting creation
- `ZOOM_REDIRECT_URI` - Zoom OAuth callback URL
- `CLOUDINARY_CLOUD_NAME` - Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend URL
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID` - Google OAuth

## Test Credentials

### Admin Dashboard
- **Dev Login:** dev@cwcplatform.com (no password, use Dev Login)
- **Test User:** test@cwcplatform.com / TestPass123

### Client Portal (magic link auth)
- **Org Admin:** testclient@example.com
- **Org Coachee:** mike@example.com (no billing visible)
- **Independent Coachee:** sarah@example.com (full billing access)

## Common Tasks

### Add a new API endpoint
1. Create/update model in `backend/app/models/`
2. Create schema in `backend/app/schemas/`
3. Add router in `backend/app/routers/`
4. Register in `backend/app/routers/__init__.py`
5. Include in `backend/app/main.py`

### Add a new frontend page
1. Create page in `frontend/src/app/[route]/page.tsx`
2. Add API client in `frontend/src/lib/api.ts`
3. Update sidebar if needed: `frontend/src/components/layout/Sidebar.tsx`

## Testing

### Current Test Status (January 2026)

```
Total: 954 tests | Passed: 847 (89%) | Failed: 31 | Skipped: 69 | Errors: 7
```

Recent fixes (January 10, 2026):
- Fixed auth_service to handle None credentials for unauthenticated requests
- Fixed booking_types router to prevent deleting types with existing bookings
- Fixed client_portal to use zoom_meeting_url instead of meeting_link
- Fixed webhooks router to use dependency injection for database session
- Fixed public_contract and public_invoice test URL paths and model attributes
- Made TestimonialSubmit video fields optional for text-only testimonials

Known remaining issues:
- test_extractions.py: AI extraction model field mismatches
- test_testimonial_public.py: Route conflict between public and admin endpoints
- test_stripe.py, test_reminders.py: Webhook/scheduling service issues

### Backend Tests (pytest)

The backend uses pytest with async support for comprehensive API and service testing.

#### Running Backend Tests
```bash
cd backend
source venv/bin/activate
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest tests/test_stripe.py         # Run specific test file
pytest -k "test_checkout"           # Run tests matching pattern
pytest --cov=app                    # Run with coverage report
```

#### Test Configuration
- **Config file:** `backend/pytest.ini`
- **Fixtures:** `backend/tests/conftest.py` (40+ reusable fixtures)
- **Test database:** In-memory SQLite (`sqlite+aiosqlite:///:memory:`)
- **Async mode:** `asyncio_mode=auto`

#### Backend Test Files

| Test File | Coverage Area |
|-----------|--------------|
| `test_auth.py` | Authentication, login, registration |
| `test_contacts.py` | Contact CRUD, search, filters |
| `test_organizations.py` | Organization management |
| `test_invoices.py` | Invoice CRUD, filtering |
| `test_payments.py` | Payment recording |
| `test_payment_plans.py` | Payment plan scheduling |
| `test_contracts.py` | Contract generation |
| `test_contract_templates.py` | Template management, merge fields |
| `test_projects.py` | Project management |
| `test_tasks.py` | Task CRUD, time entries |
| `test_stripe.py` | Stripe checkout, webhooks, payments |
| `test_client_auth.py` | Magic link authentication |
| `test_webhooks.py` | Fathom webhook handling |
| `test_integrations.py` | Google Calendar, Zoom OAuth |
| `test_extractions.py` | AI invoice extraction |
| `test_email_service.py` | Email service functionality |
| `test_public_booking.py` | Public booking pages |
| `test_public_contract.py` | Public contract signing |
| `test_public_invoice.py` | Public invoice pages |
| `test_icf_tracker.py` | ICF hours tracking |
| `test_reminders.py` | Reminder scheduler |
| `test_booking_types.py` | Booking type CRUD |
| `test_testimonials.py` | Video testimonials |
| `test_offboarding.py` | Offboarding workflows |
| `test_goals.py` | Goal tracking |
| `test_action_items.py` | Client action items |

### Frontend Tests

#### Unit Tests (Vitest)
```bash
cd frontend
npm run test              # Run all unit tests
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage
```

**Config:** `frontend/vitest.config.ts`
**Setup:** `frontend/tests/setup.ts`
**Location:** `frontend/tests/unit/`

Unit test files:
- `components/Button.test.tsx` - Button component variants
- `components/Input.test.tsx` - Input component behavior
- `lib/utils.test.ts` - Utility functions (cn)
- `lib/api.test.ts` - API client behavior

#### E2E Tests (Playwright)
```bash
cd frontend
npm run test:e2e           # Run all E2E tests
npm run test:e2e:ui        # UI mode (interactive)
npm run test:e2e:headed    # Headed browser
npm run test:e2e:report    # View test report
```

**Config:** `frontend/playwright.config.ts`
**Location:** `frontend/tests/e2e/`

E2E test files:
- `auth.spec.ts` - Login/logout flows
- `dashboard.spec.ts` - Dashboard navigation
- `client-portal.spec.ts` - Client portal access
- `public-pages.spec.ts` - Public pages
- `invoices.spec.ts` - Invoice management
- `contracts.spec.ts` - Contract management
- `bookings.spec.ts` - Booking/calendar
- `projects.spec.ts` - Project/task management
- `reports.spec.ts` - Reports and analytics

### Writing Tests

#### Backend Test Pattern
```python
import pytest
from httpx import AsyncClient

class TestFeatureName:
    @pytest.mark.asyncio
    async def test_feature_behavior(
        self, auth_client: AsyncClient, test_contact
    ):
        response = await auth_client.get("/api/endpoint")
        assert response.status_code == 200
        assert response.json()["field"] == "expected"
```

#### Frontend Unit Test Pattern
```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Component } from '@/components/Component'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component prop="value" />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })
})
```

#### E2E Test Pattern
```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    // Login...
  })

  test('should work correctly', async ({ page }) => {
    await page.goto('/feature')
    await expect(page.locator('h1')).toContainText('Feature')
  })
})
```

## Notes

- bcrypt must be pinned to <5.0.0 for passlib compatibility
- Stripe webhooks require proper signature verification
- Google Calendar sync is automatic when user has connected their account
