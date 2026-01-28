# CWC Platform

Unified business platform for Coaching Women of Color.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+) + PostgreSQL + SQLAlchemy 2.0
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **Auth:** JWT + Google OAuth + Email/Password
- **Integrations:** Stripe (payments), Google Calendar, Gmail SMTP (email)

## Project Structure

```
cwc-platform/
├── backend/          # FastAPI application
├── frontend/         # Next.js application
└── docs/             # Documentation
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your settings
npm run dev
```

## Development

- Backend API: http://localhost:8001
- Frontend: http://localhost:3001
- API Docs: http://localhost:8001/docs

## Implemented Phases

### Phase 1: Foundation & CRM
- Contacts management (CRUD, search, filters)
- Organizations management
- Contact-Organization relationships
- Interactions/notes logging

### Phase 2: Scheduling
- Booking types configuration
- Weekly availability settings
- Date-specific overrides
- Public booking pages (`/book/[slug]`)
- Booking confirmation emails

### Phase 3: Invoicing
- Invoice creation with line items
- Tax and discount support
- Payment tracking and history
- Payment plans
- Public invoice pages (`/pay/[token]`)

### Phase 4: Contracts
- Contract templates with merge fields
- E-signature capture (drawn/typed)
- Contract sending and tracking
- Audit logging
- Public signing pages (`/sign/[token]`)

### Phase 5: Projects & Tasks
- Project management with templates
- Task tracking (list & Kanban views)
- Time entries and logging
- Progress tracking
- Activity logs

### Phase 6: Authentication & Email
- JWT authentication
- Email/password login
- Google OAuth integration
- Password reset flow
- Gmail SMTP email integration

### Phase 7: Calendar Integration
- FullCalendar dashboard view
- Google Calendar OAuth
- Automatic booking sync to Google Calendar
- Zoom OAuth integration

### Phase 8: Payments (Stripe)
- Stripe Checkout integration
- Webhook handling for payment events
- Automatic invoice status updates
- Payment confirmation emails
- Refund support

### Phase 9: AI Invoice Extraction
- Fathom webhook integration for call transcripts
- Claude AI for transcript analysis
- Automatic pricing extraction
- Review and approval workflow

### Phase 10: Reports & Analytics
- Dashboard with revenue stats
- Invoice aging reports
- Project hours tracking
- CSV exports

### Phase 11: Client Portal
- Magic link authentication
- Three user types (Org Admin, Org Coachee, Independent)
- Session recordings with transcripts
- Content/Resources delivery
- Two-way messaging with email notifications
- Invoice viewing and payments
- Contract signing

### Phase 12: Client Experience
- Action Items: Coach assigns tasks, clients complete them
- Goal Tracking: Goals with milestone checkpoints and progress bars
- Progress Timeline: Visual journey of coaching engagement

### Phase 13: Video Testimonials
- Browser webcam recording (MediaRecorder API)
- Cloudinary video storage and optimization
- Testimonial request workflow with email
- Admin approval/reject/feature workflow
- Public gallery page (`/gallery`)

### Phase 14: Offboarding & Feedback
- Offboarding workflow management
- Customizable checklists and templates
- 6-section comprehensive feedback survey
- Video testimonial in survey
- Public survey page (`/feedback/[token]`)

### Phase 15: ICF Hours Tracker
- Coaching session logging for ICF certification
- Dashboard with progress toward 100 mentor hours
- Session types: 1-on-1, Group, Mentor Coaching
- Client statistics and monthly trends
- Bulk import from Google Calendar

### Phase 16: Executive Leadership Lab
- Interactive slide decks for 10-month program
- Fillable worksheets (Career Roadmap, Plateau Diagnostic, etc.)
- GitHub Pages hosting
- [View Live](https://mdxvision.github.io/cwc-executive-lab/)

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/cwc
SECRET_KEY=your-secret-key
FRONTEND_URL=http://localhost:3001

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Gmail SMTP
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
COACH_EMAIL=your-email@gmail.com

# Stripe
STRIPE_SECRET_KEY=
STRIPE_PUBLIC_KEY=
STRIPE_WEBHOOK_SECRET=

# Claude AI (optional)
ANTHROPIC_API_KEY=
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
```

## Test Credentials

- **Email:** test@cwcplatform.com
- **Password:** TestPass123

Or use Dev Login (no password required):
- **Email:** dev@cwcplatform.com
