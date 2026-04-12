# Human Review

## OAuth Setup Deferred

These items are intentionally deferred so product development can continue without blocking on third-party account setup.

### Google Calendar + Google Meet
- Status: waiting on real OAuth app credentials
- Needed env vars in [backend/.env](/Users/rafaelrodriguez/projects/CWC/CWC-automation-platform/cwc-platform/backend/.env)
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REDIRECT_URI=http://localhost:8001/api/integrations/google/callback`
- Human action required:
  - create or locate the Google OAuth app
  - add the redirect URI above in Google Cloud Console
  - paste the client ID and client secret into `backend/.env`

### Zoom
- Status: waiting on real OAuth app credentials
- Needed env vars in [backend/.env](/Users/rafaelrodriguez/projects/CWC/CWC-automation-platform/cwc-platform/backend/.env)
  - `ZOOM_CLIENT_ID`
  - `ZOOM_CLIENT_SECRET`
  - `ZOOM_REDIRECT_URI=http://localhost:8001/api/integrations/zoom/callback`
- Human action required:
  - create or locate the Zoom OAuth app
  - add the redirect URI above in the Zoom app config
  - paste the client ID and client secret into `backend/.env`

### Expected User Flow After Setup
- Wendy clicks `Connect Google Calendar + Meet` in [frontend/src/app/settings/integrations/page.tsx](/Users/rafaelrodriguez/projects/CWC/CWC-automation-platform/cwc-platform/frontend/src/app/settings/integrations/page.tsx)
- Wendy signs into her own Google account and approves access
- Wendy clicks `Connect Zoom`
- Wendy signs into her own Zoom account and approves access

### Local Restart After Credentials Are Added
```bash
cd /Users/rafaelrodriguez/projects/CWC/CWC-automation-platform/cwc-platform/backend
./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Notes
- The app wiring is already in place.
- Current blocker is provider credentials, not product code.
