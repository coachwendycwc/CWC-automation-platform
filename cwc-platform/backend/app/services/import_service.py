"""Migration importer: CSV parsing, preset detection, mapping, dedupe, commit, undo.

Presets are data, not code: a header signature identifies the source platform
and pre-fills the column mapping; the admin can always override the mapping,
so unknown export formats degrade to a manual mapping rather than failing.
"""
import csv
import io
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.organization import Organization
from app.models.import_job import ImportJob

MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_ROWS = 20_000

# Contact fields an import may set. organization_name is virtual: it resolves
# to a get-or-create Organization link at commit time.
CONTACT_FIELDS = {
    "first_name",
    "last_name",
    "full_name",
    "email",
    "phone",
    "organization_name",
    "notes",
    "source",
}

PRESETS: dict[str, dict[str, Any]] = {
    "honeybook": {
        "entity_type": "contacts",
        # Headers verified from HoneyBook's contacts-export help article
        "header_signature": ["Contact name", "Email address"],
        "mapping": {
            "Contact name": "full_name",
            "Email address": "email",
            "Phone number": "phone",
            "Notes": "notes",
        },
    },
    "dubsado": {
        "entity_type": "contacts",
        "header_signature": ["Client First Name", "Client Email"],
        "mapping": {
            "Client First Name": "first_name",
            "Client Last Name": "last_name",
            "Client Email": "email",
            "Client Phone Number": "phone",
        },
    },
}


def parse_csv(csv_text: str) -> tuple[list[str], list[dict[str, str]]]:
    if not csv_text or not csv_text.strip():
        raise ValueError("CSV file is empty")
    if len(csv_text.encode("utf-8", errors="ignore")) > MAX_CSV_BYTES:
        raise ValueError("CSV file is too large (5 MB max)")
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")
    headers = [h.strip() for h in reader.fieldnames]
    rows = []
    for raw in reader:
        rows.append({(k or "").strip(): (v or "").strip() for k, v in raw.items()})
        if len(rows) > MAX_ROWS:
            raise ValueError(f"CSV has too many rows ({MAX_ROWS} max)")
    if not rows:
        raise ValueError("CSV has no data rows")
    return headers, rows


def detect_preset(headers: list[str], entity_type: str) -> str | None:
    header_set = set(headers)
    for name, preset in PRESETS.items():
        if preset["entity_type"] != entity_type:
            continue
        if all(sig in header_set for sig in preset["header_signature"]):
            return name
    return None


def _split_full_name(full: str) -> tuple[str, str | None]:
    parts = full.strip().split()
    if not parts:
        return "", None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def _map_row(row: dict[str, str], mapping: dict[str, str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for csv_col, field in mapping.items():
        value = row.get(csv_col, "")
        if value:
            data[field] = value
    if "full_name" in data:
        first, last = _split_full_name(data.pop("full_name"))
        data.setdefault("first_name", first)
        if last:
            data.setdefault("last_name", last)
    return data


def _validate_contact(data: dict[str, str]) -> str | None:
    if not data.get("first_name"):
        return "Missing name"
    if not data.get("email") and not data.get("phone"):
        return "Row has neither email nor phone"
    return None


async def _analyze_contacts(
    db: AsyncSession,
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Shared preview/commit analysis: mapped data + outcome per row."""
    emails = set()
    analyzed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        data = _map_row(row, mapping)
        error = _validate_contact(data)
        if error:
            analyzed.append(
                {"row_index": index, "outcome": "error", "data": data, "error": error}
            )
            continue
        email = data.get("email", "").lower()
        outcome = "create"
        if email:
            if email in emails:
                outcome = "skip_duplicate"
            else:
                existing = (
                    await db.execute(
                        select(Contact).where(Contact.email == email)
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    outcome = "skip_duplicate"
            emails.add(email)
        analyzed.append(
            {"row_index": index, "outcome": outcome, "data": data, "error": None}
        )
    return analyzed


def _counts(analyzed: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"create": 0, "skip_duplicate": 0, "update_existing": 0, "error": 0}
    for item in analyzed:
        counts[item["outcome"]] = counts.get(item["outcome"], 0) + 1
    return counts


def _resolve_mapping(
    headers: list[str], entity_type: str, mapping: dict[str, str] | None
) -> tuple[str, dict[str, str]]:
    if mapping:
        return "custom", mapping
    preset_name = detect_preset(headers, entity_type)
    if preset_name is None:
        raise ValueError(
            "Could not detect the source platform — provide a column mapping"
        )
    return preset_name, PRESETS[preset_name]["mapping"]


async def run_preview(
    db: AsyncSession,
    entity_type: str,
    csv_text: str,
    mapping: dict[str, str] | None = None,
    dedupe_strategy: str = "skip",
) -> dict[str, Any]:
    if entity_type != "contacts":
        raise ValueError(f"Unsupported entity type: {entity_type}")
    headers, rows = parse_csv(csv_text)
    preset_name, effective_mapping = _resolve_mapping(headers, entity_type, mapping)
    analyzed = await _analyze_contacts(db, rows, effective_mapping)
    if dedupe_strategy == "update":
        for item in analyzed:
            if item["outcome"] == "skip_duplicate":
                item["outcome"] = "update_existing"
    return {
        "preset": preset_name if preset_name != "custom" else None,
        "mapping": effective_mapping,
        "rows": analyzed,
        "counts": _counts(analyzed),
    }


async def run_commit(
    db: AsyncSession,
    entity_type: str,
    csv_text: str,
    mapping: dict[str, str] | None = None,
    dedupe_strategy: str = "skip",
    user_id: str | None = None,
) -> ImportJob:
    if entity_type != "contacts":
        raise ValueError(f"Unsupported entity type: {entity_type}")
    if dedupe_strategy not in ("skip", "update"):
        raise ValueError(f"Unknown dedupe strategy: {dedupe_strategy}")
    headers, rows = parse_csv(csv_text)
    preset_name, effective_mapping = _resolve_mapping(headers, entity_type, mapping)
    analyzed = await _analyze_contacts(db, rows, effective_mapping)

    source = f"import:{preset_name}"
    created_contacts: list[str] = []
    created_orgs: list[str] = []
    updated_count = 0
    skipped_count = 0
    orgs_by_name: dict[str, Organization] = {}

    async def get_or_create_org(name: str) -> Organization:
        if name in orgs_by_name:
            return orgs_by_name[name]
        existing = (
            await db.execute(select(Organization).where(Organization.name == name))
        ).scalar_one_or_none()
        if existing is None:
            existing = Organization(name=name)
            db.add(existing)
            await db.flush()
            created_orgs.append(existing.id)
        orgs_by_name[name] = existing
        return existing

    for item in analyzed:
        data = item["data"]
        if item["outcome"] == "error":
            continue
        if item["outcome"] == "skip_duplicate":
            if dedupe_strategy == "update":
                existing = (
                    await db.execute(
                        select(Contact).where(
                            Contact.email == data["email"].lower()
                        )
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    changed = False
                    for field in ("first_name", "last_name", "phone", "notes"):
                        if data.get(field) and not getattr(existing, field, None):
                            setattr(existing, field, data[field])
                            changed = True
                    if changed:
                        updated_count += 1
                    else:
                        skipped_count += 1
                    continue
            skipped_count += 1
            continue

        contact = Contact(
            first_name=data["first_name"],
            last_name=data.get("last_name"),
            email=data.get("email", "").lower() or None,
            phone=data.get("phone"),
            source=source,
        )
        if data.get("organization_name"):
            org = await get_or_create_org(data["organization_name"])
            contact.organization_id = org.id
        db.add(contact)
        await db.flush()
        created_contacts.append(contact.id)

    job = ImportJob(
        source=preset_name,
        entity_type=entity_type,
        status="committed",
        total_rows=len(rows),
        created_count=len(created_contacts),
        skipped_count=skipped_count,
        updated_count=updated_count,
        error_count=_counts(analyzed)["error"],
        created_ids={"contacts": created_contacts, "organizations": created_orgs},
        row_errors=[
            {"row": item["row_index"], "error": item["error"]}
            for item in analyzed
            if item["outcome"] == "error"
        ],
        created_by=user_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def run_undo(db: AsyncSession, job_id: str) -> dict[str, Any]:
    job = (
        await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    ).scalar_one_or_none()
    if job is None:
        raise ValueError("Import job not found")
    if job.status != "committed":
        raise ValueError("Import job has already been undone")

    undone = {"contacts": 0, "organizations": 0}
    skipped: list[str] = []

    for contact_id in job.created_ids.get("contacts", []):
        contact = (
            await db.execute(select(Contact).where(Contact.id == contact_id))
        ).scalar_one_or_none()
        if contact is None:
            continue
        await db.delete(contact)
        undone["contacts"] += 1
    await db.flush()

    for org_id in job.created_ids.get("organizations", []):
        org = (
            await db.execute(select(Organization).where(Organization.id == org_id))
        ).scalar_one_or_none()
        if org is None:
            continue
        remaining = (
            await db.execute(
                select(Contact).where(Contact.organization_id == org_id)
            )
        ).scalars().first()
        if remaining is not None:
            skipped.append(f"organization {org.name} still has contacts")
            continue
        await db.delete(org)
        undone["organizations"] += 1

    job.status = "undone"
    await db.commit()
    return {"undone": undone, "skipped": skipped}
