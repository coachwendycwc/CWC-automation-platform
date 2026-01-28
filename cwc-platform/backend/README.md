# CWC Platform Backend

FastAPI backend for the CWC Platform.

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Set Up Database

**Option A: Use SQLite for development (simpler)**

Edit `.env`:
```
DATABASE_URL=sqlite+aiosqlite:///./cwc_platform.db
```

Install SQLite driver:
```bash
pip install aiosqlite
```

**Option B: Use PostgreSQL**

Create database:
```bash
createdb cwc_platform
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start Server

```bash
uvicorn app.main:app --reload --port 8001
```

## API Docs

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Endpoints

### Auth
- `POST /api/auth/google` - Google OAuth login
- `POST /api/auth/dev-login` - Dev login (no auth required)
- `GET /api/auth/me` - Get current user

### Organizations
- `GET /api/organizations` - List organizations
- `POST /api/organizations` - Create organization
- `GET /api/organizations/{id}` - Get organization
- `PUT /api/organizations/{id}` - Update organization
- `DELETE /api/organizations/{id}` - Delete organization

### Contacts
- `GET /api/contacts` - List contacts
- `POST /api/contacts` - Create contact
- `GET /api/contacts/{id}` - Get contact
- `PUT /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete contact

### Interactions
- `GET /api/interactions/contact/{contact_id}` - List contact interactions
- `POST /api/interactions` - Create interaction
- `DELETE /api/interactions/{id}` - Delete interaction

### Webhooks
- `POST /api/webhooks/fathom` - Receive Fathom webhook
- `GET /api/webhooks/fathom/test` - Test webhook endpoint
