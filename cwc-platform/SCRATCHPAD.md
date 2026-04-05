# Scratchpad

## 2026-04-04

- Added multi-calendar backend foundation with `calendar_connections` and Google OAuth persistence.
- Added unified external busy-time conflict checking in scheduling.
- Added Settings > Integrations UI for connected calendars.
- Added profile-level booking page branding fields and migration `012_booking_page_branding`.
- Added Settings > Profile page for booking branding controls.
- Updated public booking page to render branded title, description, accent color, host name, and optional logo.
- Seeded dev branding defaults for `dev@cwcplatform.com` and verified `/api/book/strategy-session` returns branding fields.
- Added `BookingCalendarService` to sync bookings to the selected primary Google calendar connection with legacy token fallback.
- Added `calendar_connection_id` to bookings via migration `013_booking_calendar_connection`.
- Wired internal and public booking create/cancel flows, plus public reschedule, to the calendar write-back service.
- Added focused backend tests for booking calendar write-back and public/internal booking creation via connected calendars.
- Added direct image upload support for profile photo and booking logo through `/api/users/me/upload-image`.
- Reused Cloudinary service for image uploads and added frontend upload buttons/previews in Settings > Profile.
- Added `BrandColorService` using Pillow to detect a dominant non-neutral color from uploaded logos.
- Booking-logo uploads now automatically update `booking_page_brand_color` while still allowing manual override.
- Added booking type duplication, starter templates, and cleaner copy/preview actions in Settings > Booking Types.
- Added paid public booking flow that creates an invoice, redirects to `/pay/{token}`, and confirms the pending booking after Stripe checkout.
- Upgraded the public payment page and success page to feel booking-aware rather than generic invoice screens.
- Extended public invoice responses with related booking summary data, including meeting link context.
- Added a public `/book/manage/{token}` page and wired payment success to a `Manage booking` action for post-payment self-service.
- Exposed `confirmation_token` through public booking and invoice responses so both free and paid bookings can land in the same self-service management flow.
- Added invoice collections tracking fields and migration `017_invoice_collection_tracking`.
- Added `/api/invoices/{id}/send-reminder` for manual due-soon, overdue, and final notice collections emails.
- Added workflow scheduler automation for due-soon reminders, overdue reminders, and final notices.
- Upgraded the invoice detail page with collection activity visibility and one-click reminder sending.

## 2026-04-05

- Upgraded booking confirmation emails so free, paid, admin-created, and rescheduled bookings can include meeting links, booking instructions, and a `Manage booking` CTA.
- Wired paid-booking confirmation delivery into Stripe checkout completion after the booking is actually confirmed and provisioned.
- Upgraded reminder emails to include a richer HTML template and direct clients back to `/book/manage/{token}`.
- Added public self-service rescheduling controls on `/book/manage/{token}` with date-based slot loading and one-click reschedule actions.
- Verified the booking email and self-service management slice with focused backend tests and a live `200` response from `/book/manage/test-token`.
- Added collections visibility metadata to invoice list responses, including reminder timestamps, collection stage, and a follow-up attention flag.
- Expanded invoice stats with `collections_attention_count` so the invoice screen can show follow-up workload at a glance.
- Updated the invoice list UI to surface collection badges and last-email timestamps directly in the table.
- Verified the collections-visibility slice with focused invoice tests, backend compile checks, and a live `200` response from `/invoices`.
