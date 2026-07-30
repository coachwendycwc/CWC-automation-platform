# Importer presets — what they assume, and how to validate them

The migration importer detects a source platform from a CSV's header row and
pre-fills the column mapping. This document records **exactly what each preset
assumes and where that assumption came from**, so validating a preset later is
a five-minute diff rather than a re-investigation.

## Status: BETA — built from vendor documentation, not real export files

Every preset below was derived from the vendor's own help articles. **None has
been checked against an actual export downloaded from a live account.** Column
names in help docs are frequently abbreviated, reordered, or out of date, and
vendors change them without notice.

This is safe in practice because the importer degrades gracefully: if a header
signature doesn't match, no preset is applied and the admin maps columns by
hand. A wrong preset costs a few clicks, not data. But until validated, treat
an auto-detected mapping as a suggestion to check, not a guarantee.

## How to validate a preset (do this when a real export is available)

1. Export the entity from a live account in the source platform.
2. Open the CSV and copy its header row.
3. Compare against the `header_signature` and `mapping` in
   `cwc-platform/backend/app/services/import_service.py` (`PRESETS`).
4. Fix any mismatch, then run the file through `/import` and confirm the
   preview maps every column you care about.
5. Update the **Validated** column below with the date and who checked it.

## Presets

### `honeybook` — contacts
| | |
|---|---|
| Source | [Download and export your contacts list from HoneyBook](https://help.honeybook.com/en/articles/2650752-download-and-export-your-contacts-list-from-honeybook) |
| Export path in product | Clients → Contacts → triple-dot → Download spreadsheet |
| Validated against a real file | ❌ **No** |

Header signature (all must be present to auto-detect): `Contact name`, `Email address`

| CSV column | CWC field | Notes |
|---|---|---|
| `Contact name` | `full_name` | Split into first/last on first space |
| `Email address` | `email` | Dedupe key |
| `Phone number` | `phone` | |
| `Notes` | `notes` | |

The help article also mentions an address and a created-date column; neither is
mapped, because CWC has no matching contact field today.

### `dubsado` — contacts
| | |
|---|---|
| Source | [Export data from Dubsado](https://help.dubsado.com/en/articles/2779503-export-data-from-dubsado) |
| Export path in product | Reports → Exports → clients/projects → CSV |
| Validated against a real file | ❌ **No** |

Header signature: `Client First Name`, `Client Email`

| CSV column | CWC field |
|---|---|
| `Client First Name` | `first_name` |
| `Client Last Name` | `last_name` |
| `Client Email` | `email` |
| `Client Phone Number` | `phone` |

Dubsado's export is column-configurable per user, so headers vary between
accounts more than the other platforms. Expect manual mapping to be common
here even once the preset is validated.

## Entities without a preset

**Invoices** and **ICF coaching hours** import through manual column mapping
only. No vendor's invoice export was documented well enough to guess at, and
mapping four or five columns by hand is quick. Paperbell's ICF log export is
the obvious candidate for the first ICF preset — see
[Paperbell's ICF coaching log](https://paperbell.com/support/knowledge-base/icf-client-coaching-log-international-coaching-federation/).

## Adding a preset

`PRESETS` in `import_service.py` is plain data — a name, an `entity_type`, a
`header_signature` list, and a `mapping` dict. Add an entry, add a fixture CSV
and a detection test in `tests/test_import_service.py`, and record it here with
its source. No code changes are needed.
