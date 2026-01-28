# CWC Platform - Complete Features & SOP Guide

## Platform Overview
CWC Platform is a unified business automation platform for "Coaching Women of Color" - consolidating CRM, scheduling, invoicing, contracts, project management, payments, and client portal into a single application.

---

## ADMIN PORTAL (Coach Side)

### Dashboard (`/dashboard`)
| Feature | Description |
|---------|-------------|
| Revenue Stats | Monthly revenue, outstanding invoices, paid this month |
| Revenue Chart | Bar chart showing revenue trends by month |
| Recent Activity | Latest invoices, bookings, contracts |
| Quick Actions | Create invoice, schedule booking, send contract |
| Upcoming Sessions | Next scheduled coaching sessions |

---

### Calendar (`/calendar`)
| Feature | Description |
|---------|-------------|
| FullCalendar View | Monthly/weekly/daily calendar display |
| Booking Display | Shows all scheduled sessions with client info |
| Google Calendar Sync | Two-way sync with connected Google Calendar |
| Drag & Drop | Reschedule bookings by dragging |
| Click to Create | Click time slot to create new booking |

---

## CLIENTS GROUP

### Contacts (`/contacts`)
| Feature | Description |
|---------|-------------|
| Contact List | Searchable, filterable list of all contacts |
| Contact Types | Lead, Client, Partner classification |
| Coaching Types | Individual, Organization-paid tracking |
| Contact Detail | Full profile with all related data |
| Organization Link | Associate contacts with organizations |
| Tags | Custom tagging for segmentation |
| Source Tracking | How contact was acquired |
| Portal Access | Enable/disable client portal access |

**Contact Detail Page (`/contacts/[id]`):**
- Profile information (name, email, phone, role)
- Organization affiliation
- Onboarding assessment (view responses)
- Interaction history
- Bookings/sessions
- Invoices
- Contracts
- Projects
- Action items assigned
- Goals set
- Notes exchanged
- Session recordings (Fathom)

---

### Organizations (`/organizations`)
| Feature | Description |
|---------|-------------|
| Organization List | All client organizations |
| Organization Detail | Company info, industry, contacts |
| Team View | All coachees from organization |
| Billing Contact | Primary billing relationship |
| Logo Upload | Organization branding for portal |

---

### Notes (`/notes`)
| Feature | Description |
|---------|-------------|
| Two-Way Messaging | Exchange notes with clients |
| Unread Count | Badge showing unread messages |
| Reply Threading | Conversation threads |
| Email Notifications | Clients notified of new notes |
| Read Status | Track when notes are read |

---

### Action Items (`/action-items`)
| Feature | Description |
|---------|-------------|
| Create for Clients | Assign tasks/homework to clients |
| Priority Levels | Low, Medium, High priority |
| Due Dates | Set deadlines |
| Status Tracking | Pending, In Progress, Completed, Skipped |
| Session Link | Associate with coaching session |
| Client Completion | Clients mark items as done |
| **Auto Reminders** | Email 3 days before due + overdue alerts |

---

### Goals (`/goals`)
| Feature | Description |
|---------|-------------|
| Create Goals | Set goals for clients |
| Categories | Career, Health, Relationships, Finance, Personal, Education |
| Target Dates | Goal completion deadlines |
| Milestones | Breakdown goals into checkpoints |
| Progress Tracking | Auto-calculated from milestones |
| Status | Active, Completed, Abandoned |
| **Auto Reminders** | Email 7 days before target date |

---

### Assessments (`/assessments`)
| Feature | Description |
|---------|-------------|
| Onboarding Assessments | View all submitted assessments |
| Fathom Extractions | AI-extracted data from call transcripts |
| Assessment Detail | Full 6-section response view |
| Resend Email | Resend assessment link |
| Completion Status | Track who has/hasn't completed |

**Onboarding Assessment Sections:**
1. Client Context (name, role, motivations)
2. Self Assessment (12 rating scales 1-10)
3. Identity & Workplace Experience
4. Goals for Coaching
5. Wellbeing & Support
6. Logistics & Preferences

---

## BUSINESS GROUP

### Bookings (`/bookings`)
| Feature | Description |
|---------|-------------|
| Booking List | All scheduled sessions |
| Status Filter | Pending, Confirmed, Completed, Cancelled, No-Show |
| Booking Types | Different session types (discovery, coaching, etc.) |
| Zoom Integration | Auto-create Zoom meetings |
| Google Calendar | Auto-add to Google Calendar |
| **Auto Reminders** | 24h and 1h email reminders |
| **Post-Session Email** | Follow-up 24h after session |

**Booking Types (`/settings` > Booking Types):**
- Custom session types with duration and price
- Public booking page slug
- Availability rules

**Availability Configuration:**
- Weekly recurring availability
- Date-specific overrides
- Buffer time between sessions

**Public Booking Page (`/book/[slug]`):**
- Client self-scheduling
- Available time slots display
- Contact info collection
- Confirmation email sent

---

### Projects (`/projects`)
| Feature | Description |
|---------|-------------|
| Project List | All client projects |
| Project Templates | Reusable project structures |
| Tasks | Todo, In Progress, Review, Completed |
| Time Tracking | Log hours on tasks |
| Link to Contact | Associate with client |
| Link to Contract | Connect to signed contract |
| Link to Invoice | Connect to payment |

---

### Invoices (`/invoices`)
| Feature | Description |
|---------|-------------|
| Invoice Creation | Line items, tax, discounts |
| Invoice Status | Draft, Sent, Paid, Overdue, Cancelled |
| Send Invoice | Email invoice to client |
| Stripe Payments | Online payment via Stripe Checkout |
| Payment Recording | Manual payment entry |
| Payment Plans | Split into installments |
| PDF Generation | Downloadable invoice PDF |
| Recurring Invoices | Auto-generate on schedule |

**Public Invoice Page (`/pay/[token]`):**
- View invoice details
- Pay with credit card (Stripe)
- Download PDF
- Payment confirmation

---

### Contracts (`/contracts`)
| Feature | Description |
|---------|-------------|
| Contract Templates | Reusable contract templates |
| Merge Fields | Auto-fill {{client_name}}, {{date}}, etc. |
| Generate from Template | Create contract from template |
| E-Signature | Drawn or typed signature |
| Audit Log | Track all contract events |
| Status | Draft, Sent, Viewed, Signed, Expired |

**Public Signing Page (`/sign/[token]`):**
- View contract
- Draw or type signature
- Agree to terms
- Signed confirmation

---

## FINANCE GROUP

### Bookkeeping (`/bookkeeping`)
| Feature | Description |
|---------|-------------|
| Expenses | Track business expenses |
| Categories | Categorize expenses |
| Receipts | Upload receipt images |
| Mileage | Track business mileage |
| Contractors | 1099 contractor payments |
| Reports | Financial summaries |

---

## GROWTH GROUP

### Content (`/content`)
| Feature | Description |
|---------|-------------|
| Resource Library | Upload files for clients |
| Categories | Organize by topic |
| Client Access | Control who sees what |
| File Types | PDF, video, audio, documents |
| Descriptions | Add context to resources |

---

### Testimonials (`/testimonials`)
| Feature | Description |
|---------|-------------|
| Request Testimonials | Email clients for testimonials |
| Video Recording | Browser webcam recording |
| Cloudinary Storage | Video hosting and optimization |
| Approval Workflow | Review before publishing |
| Feature Toggle | Mark testimonials as featured |
| Quote Editing | Edit written testimonials |

**Public Recording Page (`/record/[token]`):**
- Video recording interface
- 2-minute max duration
- Preview before submit
- Author info and permission

**Public Gallery (`/gallery`):**
- Featured testimonials section
- Video playback modals
- Quote display

---

### ICF Tracker (`/icf-tracker`)
| Feature | Description |
|---------|-------------|
| Session Logging | Track coaching sessions for ICF hours |
| Session Types | 1-on-1, Group, Mentor Coaching |
| Hour Calculation | Auto-sum hours by type |
| Progress Dashboard | Percentage toward certification goals |
| Client Stats | Hours per client breakdown |
| Monthly Trends | Bar chart of session activity |
| Certification Journey | Checklist for ACC/PCC/MCC requirements |
| Bulk Import | Import from calendar or CSV |

---

## ADMIN GROUP

### Offboarding (`/offboarding`)
| Feature | Description |
|---------|-------------|
| Workflow Types | Client, Project, Contract offboarding |
| Checklist Templates | Reusable offboarding checklists |
| Feedback Survey | 6-section end-of-engagement survey |
| Testimonial Request | Request video/written testimonial |
| Completion Email | Send completion/certificate email |
| Activity Log | Track all offboarding events |

**Feedback Survey Sections:**
1. Overall Experience (satisfaction, NPS)
2. Growth & Measurement (outcomes, wins)
3. Coaching Process (helpful parts, improvements)
4. Equity, Safety, Support (psychological safety)
5. Testimonial (permission, written, video)
6. Final Feedback

**Public Survey Page (`/feedback/[token]`):**
- Multi-section form
- Progress indicator
- Video recording option

---

### AI Extractions (`/extractions`)
| Feature | Description |
|---------|-------------|
| Fathom Integration | Receive call transcripts via webhook |
| AI Analysis | Claude extracts client, service, pricing |
| Confidence Scoring | High/Medium/Low confidence |
| Review Queue | Approve or reject extractions |
| Draft Invoice | Auto-generate invoice from approved extraction |

---

## SETTINGS (`/settings`)

| Feature | Description |
|---------|-------------|
| Profile | Update name, email |
| Booking Types | Manage session types |
| Availability | Set weekly schedule |
| Integrations | Connect Google, Zoom, Stripe |
| Templates | Contract and project templates |

---

## CLIENT PORTAL (Coachee Side)

### Portal Access Types
| Type | Access |
|------|--------|
| **Org Admin** | Overview, Team (coachees), Billing, Contracts |
| **Org Coachee** | Home, Sessions, Messages only (no billing) |
| **Independent** | Home, Sessions, Messages, Resources, Billing |

### Magic Link Login (`/client/login`)
- Enter email address
- Receive magic link email
- Click link to authenticate (no password)

---

### Client Dashboard (`/client/dashboard`)
| Feature | Description |
|---------|-------------|
| Welcome Message | Personalized greeting |
| Quick Stats | Sessions, action items, goals |
| Next Session | Upcoming booking with Zoom link |
| Recent Activity | Latest notes, items, goals |
| Incomplete Assessment | Alert if assessment not done |

---

### Sessions (`/client/sessions`)
| Feature | Description |
|---------|-------------|
| Upcoming Sessions | Scheduled bookings with details |
| Past Sessions | Completed session history |
| Session Recordings | Fathom recordings and transcripts |
| Homework | Action items from each session |
| Zoom Links | Direct meeting access |

---

### Action Items (`/client/action-items`)
| Feature | Description |
|---------|-------------|
| Task List | All assigned action items |
| Mark Complete | Check off finished items |
| Mark Skipped | Skip irrelevant items |
| Due Dates | See upcoming deadlines |
| Priority | See task importance |

---

### Goals (`/client/goals`)
| Feature | Description |
|---------|-------------|
| Goal Cards | Visual goal display |
| Progress Bars | Milestone completion percentage |
| Check Milestones | Mark milestones complete |
| Target Dates | Goal deadlines |
| Categories | Goal categorization |

---

### Messages (`/client/notes`)
| Feature | Description |
|---------|-------------|
| Send Notes | Message coach |
| Receive Notes | Get messages from coach |
| Email Alerts | Notified of new messages |
| Read Status | Know when coach has read |

---

### Resources (`/client/resources`)
| Feature | Description |
|---------|-------------|
| Content Library | Access shared resources |
| Categories | Browse by topic |
| Download | Download files |
| View | View in browser |

---

### Billing (`/client/invoices`)
| Feature | Description |
|---------|-------------|
| Invoice List | All invoices |
| Pay Online | Stripe payment |
| Payment History | Past payments |
| Download | PDF invoices |

---

### Contracts (`/client/contracts`)
| Feature | Description |
|---------|-------------|
| View Contracts | See all contracts |
| Sign Contracts | E-signature |
| Download | PDF contracts |

---

### Onboarding Assessment (`/client/onboarding`)
| Feature | Description |
|---------|-------------|
| View Responses | See submitted assessment |
| Completion Status | Assessment complete/pending |

---

### Timeline (`/client/timeline`)
| Feature | Description |
|---------|-------------|
| Progress Timeline | Visual journey of coaching engagement |
| Event Types | Sessions, goals, milestones, items, notes |
| Filters | Filter by event type |

---

## AUTOMATED EMAIL WORKFLOWS

### Onboarding Sequence
| Email | Trigger | Timing |
|-------|---------|--------|
| Assessment Request | Payment confirmed | Immediate |
| Assessment Reminder 1 | Assessment incomplete | Day 1 |
| Assessment Reminder 2 | Assessment incomplete | Day 3 |
| Assessment Reminder 3 | Assessment incomplete | Day 7 |
| Welcome Email | Assessment completed | Immediate |
| Welcome Follow-up 1 | Assessment completed | Day 3 |
| Welcome Follow-up 2 | Assessment completed | Day 7 |

### Session Emails
| Email | Trigger | Timing |
|-------|---------|--------|
| Booking Confirmation | Booking created | Immediate |
| 24h Reminder | Before session | 24 hours before |
| 1h Reminder | Before session | 1 hour before |
| Post-Session Follow-up | Session completed | 24 hours after |

### Task & Goal Reminders
| Email | Trigger | Timing |
|-------|---------|--------|
| Action Item Due | Due date approaching | 3 days before |
| Action Item Overdue | Past due date | When overdue |
| Goal Reminder | Target date approaching | 7 days before |

### Engagement Emails
| Email | Trigger | Timing |
|-------|---------|--------|
| Weekly Summary | Active client | Mondays 9am |
| Monthly Report | Active client | 1st of month 9am |

---

## INTEGRATIONS

| Integration | Purpose |
|-------------|---------|
| **Gmail SMTP** | Send all emails |
| **Google Calendar** | Sync bookings |
| **Google OAuth** | Admin login |
| **Zoom** | Auto-create meeting links |
| **Stripe** | Payment processing |
| **Fathom** | Session recordings and transcripts |
| **Cloudinary** | Video testimonial storage |
| **Claude AI** | Transcript analysis and extraction |

---

## PUBLIC PAGES (No Login Required)

| Page | Purpose |
|------|---------|
| `/book/[slug]` | Public booking/scheduling |
| `/pay/[token]` | Invoice payment |
| `/sign/[token]` | Contract signing |
| `/record/[token]` | Video testimonial recording |
| `/feedback/[token]` | Feedback survey |
| `/onboarding/[token]` | Onboarding assessment |
| `/gallery` | Public testimonial gallery |
| `/client/login` | Client portal login |
| `/client/verify/[token]` | Magic link verification |

---

## TECH STACK

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.13) + SQLAlchemy 2.0 |
| Frontend | Next.js 14 (App Router) + TypeScript |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Styling | Tailwind CSS + shadcn/ui |
| Auth | JWT + Magic Links |
| Payments | Stripe Checkout + Webhooks |
| Email | Gmail SMTP |
| Video | Cloudinary |
| AI | Claude API (claude-3-5-sonnet) |

---

*Last Updated: January 2026*
