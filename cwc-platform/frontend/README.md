# CWC Platform Frontend

Next.js frontend for the CWC Platform.

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
# Edit .env.local with your settings
```

### 3. Start Development Server

```bash
npm run dev
```

Open http://localhost:3000

## Pages

- `/` - Login page
- `/dashboard` - Main dashboard
- `/contacts` - Contact list
- `/contacts/new` - Create contact
- `/contacts/[id]` - Contact detail
- `/organizations` - Organization list
- `/organizations/new` - Create organization
- `/organizations/[id]` - Organization detail

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **State:** TanStack Query (ready)
- **Forms:** React Hook Form + Zod (ready)

## Development

### Adding shadcn components

This project uses a manual shadcn/ui setup. Add components by copying from:
https://ui.shadcn.com/docs/components

### API Integration

API client is in `src/lib/api.ts`. All endpoints use the token stored in localStorage.

### Authentication

Currently using dev login for development. Google OAuth will work once you configure:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

in both `.env.local` (frontend) and `.env` (backend).
