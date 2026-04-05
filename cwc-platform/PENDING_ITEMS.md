# CWC Platform Pending Items

## Summary

This file tracks active execution items, blockers, and verification work.

## Active Build Priorities

### Wendy Pilot
- [ ] Confirm pilot scope for week 1
- [ ] Confirm exact workflows Wendy will use inside the platform
- [ ] Confirm which workflows remain in old tools during pilot
- [ ] Create Wendy quick-start guide
- [ ] Verify login and session reliability in the environment Wendy uses
- [x] Add profile settings page for booking-page branding
- [x] Seed visible dev branding for Wendy-facing booking page
- [x] Add direct image uploads for profile photo and booking logo
- [x] Auto-detect booking-page accent color from uploaded logo
- [x] Add branded booking confirmation emails with meeting links, instructions, and manage-booking CTA
- [x] Add public manage-booking reschedule UI for self-service changes

### Scheduling Stack Replacement
- [x] Add backend foundation for multi-calendar connections
- [x] Add `calendar_connections` model and schema
- [x] Update integrations API to store/list Google calendar connections
- [x] Apply `011_calendar_connections` migration in the active environment
- [x] Add tests for calendar connection model and integration endpoints
- [x] Add initial calendar connection management UI in settings
- [x] Add backend set-primary-calendar workflow
- [x] Add backend disconnect per-calendar workflow
- [x] Add frontend set-primary-calendar workflow
- [x] Add frontend disconnect per-calendar workflow
- [x] Add unified busy-time service across active calendar connections
- [x] Add unified availability conflict checking across calendar connections
- [x] Add booking-page branding fields to user profile and public booking payload
- [x] Add public booking-page UI customization layer for title, description, accent color, and logo
- [x] Apply `012_booking_page_branding` migration in the active environment
- [x] Add primary write-back calendar selection in scheduling/bookings flow
- [x] Track booking-to-calendar ownership with `calendar_connection_id`
- [x] Sync public booking create/reschedule/cancel flows to the selected calendar connection
- [x] Sync internal booking create/cancel flows to the selected calendar connection
- [x] Apply `013_booking_calendar_connection` migration in the active environment
- [ ] Define Motion compatibility approach
- [ ] Define Calendly migration path

### Coaching Session Intelligence
- [ ] Design Zoom ingestion flow
- [ ] Human review: add real Google and Zoom OAuth credentials in [HUMAN_REVIEW.md](/Users/rafaelrodriguez/projects/CWC/CWC-automation-platform/cwc-platform/HUMAN_REVIEW.md)
- [ ] Design Fathom ingestion flow
- [ ] Match sessions to bookings and contacts
- [ ] Auto-create internal session records
- [ ] Define client-visible session delivery rules
- [ ] Define coach-only vs client-visible permissions
- [ ] Define ICF auto-logging workflow

### Finance Foundation
- [ ] Define unified ledger model
- [ ] Define chart-of-accounts-lite for coaching businesses
- [ ] Define expense and contractor workflow
- [ ] Define CPA export package
- [ ] Define reconciliation workflow
- [x] Add invoice collection tracking fields for reminder cadence
- [x] Add manual invoice reminder / collections trigger on invoice detail page
- [x] Add automated due-soon reminders in workflow scheduler
- [x] Add automated overdue and final notice collections emails in workflow scheduler

## Blocked / Depends On

- [ ] Microsoft calendar support depends on provider integration design
- [ ] Motion integration depends on API and practical compatibility path
- [ ] White-label architecture depends on CWC internal workflow validation
- [ ] Finance implementation should follow clear ledger/domain design, not ad hoc fields

## Manual Verification Needed

- [ ] Wendy login flow in real environment
- [ ] Google calendar connect flow after new calendar connection migration
- [ ] `/api/integrations/calendar-connections` returns expected connected accounts
- [ ] Booking flow end-to-end from public page to calendar entry
- [ ] Verify public booking create writes a Google event to the selected primary calendar
- [ ] Verify public booking cancel removes the Google event from the selected primary calendar
- [ ] Verify seeded test booking page at `/book/strategy-session`
- [ ] Verify paid booking flow lands on `/pay/{token}/success` with live booking summary and `Manage booking` action
- [ ] Verify `/book/manage/{token}` loads session details and allows self-service cancellation
- [ ] Verify `/book/manage/{token}` loads available slots and completes self-service rescheduling
- [ ] Verify free booking confirmation screen links to `/book/manage/{token}`
- [ ] Verify booking confirmation emails include meeting link, instructions, and `Manage booking` CTA for free, paid, and rescheduled bookings
- [ ] Verify booking branding edits persist from `/settings/profile` to `/book/strategy-session`
- [ ] Verify direct profile-photo and booking-logo uploads persist from `/settings/profile`
- [ ] Verify uploaded booking logo auto-updates `booking_page_brand_color`
- [ ] Invoice and contract flow with real pilot data
- [ ] Verify invoice detail page collections card reflects live reminder timestamps
- [ ] Verify automated due-soon, overdue, and final notice emails in a real configured environment
- [ ] Client portal access for post-session assets
- [ ] Pilot readiness for active CWC workflows

## Technical Debt / Cleanup

- [ ] Consolidate legacy single-calendar assumptions
- [ ] Remove or phase out direct integration token dependence on `User`
- [ ] Align docs with new multi-calendar direction
- [ ] Backfill legacy Google token records into `calendar_connections` if needed
- [ ] Add tests for new calendar connection APIs

## Next Up After Current Slice

- [ ] Google calendar conflict verification with a live connected account
- [ ] Add branded follow-up reminder emails beyond confirmation/cancellation
- [ ] Add collections cadence controls and custom reminder templates
- [ ] Session intelligence domain model expansion
- [ ] Finance ledger domain design doc
