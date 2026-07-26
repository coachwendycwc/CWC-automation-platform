# Migration Importer v1 — Design Spec

**Date:** 2026-07-26 · **Approved by:** Rafael (chat, 2026-07-26) · **Branch:** `feat/migration-importer` (off `security/public-endpoint-hardening` — requires `require_admin`)
**Goal:** a coach switching from HoneyBook/Dubsado/Paperbell (or anything that exports CSV) imports their contacts, historical invoices, and ICF hours into CWC without re-typing. Adoption lever, Tier 0.8 in `PRODUCT_BACKLOG.md`.

## Scope (v1)
- **Entities:** Contacts (+ auto-create Organizations from a company column), historical Invoices (+ recorded payments so revenue history is queryable), ICF coaching-log sessions (Paperbell export → existing ICF bulk-import path).
- **Universal CSV wizard**, presets as conveniences: upload → detect preset by header signature → column mapping (pre-filled, editable) → dry-run preview (validation + dedupe flags) → commit → undo available.
- **Out of scope (v2):** API pulls, bookings/ICS, contracts (attach PDFs), projects/tasks, concierge-migration page.

## Verified source formats (research 2026-07-26)
- **HoneyBook contacts CSV:** contact name, email, phone, address, notes, created date ([help article](https://help.honeybook.com/en/articles/2650752)). Invoices/projects exportable via reports section (columns unverified — mapping UI is the fallback).
- **Dubsado clients+projects CSV:** client first/last name, phone, email, street address; project lead/job status, contract status, primary invoice amount, total paid, custom-mapped fields ([help article](https://help.dubsado.com/en/articles/2779503)).
- **Paperbell ICF log CSV:** full client coaching-hours history ([support article](https://paperbell.com/support/knowledge-base/icf-client-coaching-log-international-coaching-federation/)). Exact columns unverified.
- Presets ship "beta" until validated against real export files; unknown columns are simply left unmapped or hand-mapped.

## Architecture
```
frontend /import (4-step stepper)
   │  POST /api/imports/preview   {entity_type, csv_text, mapping?}
   │  POST /api/imports/commit    {entity_type, csv_text, mapping, dedupe_strategy}
   │  POST /api/imports/{id}/undo
   │  GET  /api/imports           (history)  ·  GET /api/imports/presets
   ▼
routers/imports.py (ALL require_admin)
   ▼
services/import_service.py
   parse_csv → detect_preset(headers) → apply_mapping → validate_rows
   → dedupe (contacts: by email vs DB; invoices: by invoice_number)
   → commit (single transaction) → record ImportJob{created_ids}
   ▼
models/import_job.py + migration 014
```

### ImportJob model
`id` (uuid str36) · `source` (preset name or "custom") · `entity_type` ("contacts" | "invoices" | "icf_sessions") · `status` ("committed" | "undone") · `total_rows`, `created_count`, `skipped_count`, `error_count` (ints) · `created_ids` (JSON: {model: [ids]}) · `row_errors` (JSON: [{row, error}]) · `created_by` (user id) · `created_at`.

### Behavior decisions
- **No server-side file storage** — CSV text rides in both preview and commit requests (size-capped at 5 MB / 20k rows). Dedupe makes re-commit idempotent.
- **Preview writes nothing**; returns per-row outcome (`create` / `skip_duplicate` / `update_existing` / `error`) + counts + detected preset + effective mapping.
- **Dedupe strategies** (contacts): `skip` (default) or `update` (fill blank fields only — never overwrite non-empty CWC data). Invoices always `skip` on duplicate invoice_number.
- **Contacts:** required = first_name (split "Full Name" if preset says so) + at least email or phone. `source` field set to preset name (e.g. "import:honeybook"). Company column → get-or-create Organization by exact name, link contact.
- **Invoices:** required = contact email match or inline contact-create, amount, date. Created with existing model fields: `invoice_number` (generated `IMP-####` if absent), `line_items` (single "Imported" line), `total`/`amount_paid`/`balance_due`, `status` (paid if amount_paid ≥ total), `due_date`. A Payment record is created when amount_paid > 0.
- **ICF sessions:** map to the existing ICF bulk-import service (`icf-tracker/bulk-import` path) — do not reimplement.
- **Undo:** deletes records listed in `created_ids` (child-first: payments → invoices; contacts before orgs, orgs only if created by this job AND now empty); marks job `undone`. Undo is blocked if a record has since been referenced (e.g. invoice got a new payment) — those are skipped and reported.
- **Presets = data, not code:** dict of `{name, header_signature: [required headers], mapping: {csv_col → field}, transforms: {field: transform_name}}`. Transforms are a small named set (split_name, parse_date_multi, parse_money).

### Error handling
Row-level errors never abort the batch (collected into `row_errors`, shown in preview and stored on the job). Malformed CSV / oversize / wrong encoding → 400 with a human message. Commit is one transaction: an unexpected mid-commit exception rolls back everything (no partial imports).

### Testing (TDD, fixture CSVs per preset)
- Unit: preset detection, mapping application, name-split/date/money transforms, validation failures.
- Endpoint: preview (no writes, correct outcomes), commit (records created, counts right, ImportJob recorded), idempotent re-commit (all skips), dedupe update-mode fills blanks only, undo (records gone, job undone, referenced-record skip), auth (non-admin 403, anon 401/403).
- Fixtures: honeybook_contacts.csv, dubsado_clients.csv, generic_contacts.csv, invoices.csv, paperbell_icf.csv (best-guess columns, marked beta).

### Frontend
`/import` page (admin sidebar under Settings): stepper Upload → Map (table of CSV column → CWC field selects, preset pre-applied) → Preview (counts + row table with outcome badges + errors) → Result (counts + Undo button). History list of past imports with undo. Uses existing shadcn/ui components + design tokens.
