"""Migration importer: CSV parsing, preset detection, mapping, dedupe, commit, undo.

Presets are data, not code: a header signature identifies the source platform
and pre-fills the column mapping; the admin can always override the mapping,
so unknown export formats degrade to a manual mapping rather than failing.
"""
import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.organization import Organization
from app.models.invoice import Invoice
from app.models.payment import Payment
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


DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%b %d, %Y")


def _parse_date(value: str) -> date | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_money(value: str) -> Decimal | None:
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _validate_invoice(data: dict[str, str]) -> str | None:
    if not data.get("contact_email"):
        return "Missing client email"
    if _parse_money(data.get("total", "")) is None:
        return "Missing or unreadable amount"
    if data.get("issue_date") and _parse_date(data["issue_date"]) is None:
        return f"Unreadable invoice date: {data['issue_date']}"
    if data.get("due_date") and _parse_date(data["due_date"]) is None:
        return f"Unreadable due date: {data['due_date']}"
    return None


def _resolve_due_date(data: dict[str, str]) -> date:
    """Due date from the CSV, else 30 days after the invoice date, else today."""
    if data.get("due_date"):
        parsed = _parse_date(data["due_date"])
        if parsed:
            return parsed
    if data.get("issue_date"):
        issued = _parse_date(data["issue_date"])
        if issued:
            return issued + timedelta(days=30)
    return date.today()


def _invoice_key(data: dict[str, str]) -> tuple:
    """Natural key for a historical invoice: who, when due, how much."""
    return (
        data.get("contact_email", "").lower(),
        str(_resolve_due_date(data)),
        str(_parse_money(data.get("total", "")) or ""),
    )


async def _analyze_invoices(
    db: AsyncSession,
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Shared preview/commit analysis for invoice rows."""
    seen: set[tuple] = set()
    analyzed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        data = _map_row(row, mapping)
        error = _validate_invoice(data)
        if error:
            analyzed.append(
                {"row_index": index, "outcome": "error", "data": data, "error": error}
            )
            continue
        key = _invoice_key(data)
        outcome = "create"
        if key in seen:
            outcome = "skip_duplicate"
        else:
            # The model has no issue_date, so dedupe on (client, due date, total)
            total = _parse_money(data["total"])
            due = _resolve_due_date(data)
            existing = (
                await db.execute(
                    select(Invoice)
                    .join(Contact, Invoice.contact_id == Contact.id)
                    .where(
                        Contact.email == data["contact_email"].lower(),
                        Invoice.total == total,
                        Invoice.due_date == due,
                    )
                )
            ).scalars().first()
            if existing is not None:
                outcome = "skip_duplicate"
        seen.add(key)
        analyzed.append(
            {"row_index": index, "outcome": outcome, "data": data, "error": None}
        )
    return analyzed


def _counts(analyzed: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"create": 0, "skip_duplicate": 0, "update_existing": 0, "error": 0}
    for item in analyzed:
        counts[item["outcome"]] = counts.get(item["outcome"], 0) + 1
    return counts


SUPPORTED_ENTITIES = ("contacts", "invoices")


async def _analyze(
    db: AsyncSession,
    entity_type: str,
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    if entity_type == "invoices":
        return await _analyze_invoices(db, rows, mapping)
    return await _analyze_contacts(db, rows, mapping)


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
    if entity_type not in SUPPORTED_ENTITIES:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    headers, rows = parse_csv(csv_text)
    preset_name, effective_mapping = _resolve_mapping(headers, entity_type, mapping)
    analyzed = await _analyze(db, entity_type, rows, effective_mapping)
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
    if entity_type not in SUPPORTED_ENTITIES:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    if dedupe_strategy not in ("skip", "update"):
        raise ValueError(f"Unknown dedupe strategy: {dedupe_strategy}")
    headers, rows = parse_csv(csv_text)
    preset_name, effective_mapping = _resolve_mapping(headers, entity_type, mapping)
    analyzed = await _analyze(db, entity_type, rows, effective_mapping)

    source = f"import:{preset_name}"
    created_contacts: list[str] = []
    created_orgs: list[str] = []
    created_invoices: list[str] = []
    created_payments: list[str] = []
    updated_count = 0
    skipped_count = 0
    orgs_by_name: dict[str, Organization] = {}
    contacts_by_email: dict[str, Contact] = {}

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

    async def get_or_create_contact(email: str, name: str | None) -> Contact:
        """Invoices reference a client; create a minimal contact if unknown."""
        key = email.lower()
        if key in contacts_by_email:
            return contacts_by_email[key]
        existing = (
            await db.execute(select(Contact).where(Contact.email == key))
        ).scalars().first()
        if existing is None:
            first, last = _split_full_name(name or key.split("@")[0])
            existing = Contact(
                first_name=first, last_name=last, email=key, source=source
            )
            db.add(existing)
            await db.flush()
            created_contacts.append(existing.id)
        contacts_by_email[key] = existing
        return existing

    if entity_type == "invoices":
        # Allocate invoice numbers locally: invoice_service.generate_invoice_number
        # re-queries committed rows, so calling it per row in one transaction
        # would hand out the same number repeatedly.
        year = date.today().year
        prefix = f"IMP-{year}-"
        last = (
            await db.execute(
                select(Invoice.invoice_number)
                .where(Invoice.invoice_number.like(f"{prefix}%"))
                .order_by(Invoice.invoice_number.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        next_seq = 1
        if last:
            try:
                next_seq = int(last.split("-")[-1]) + 1
            except ValueError:
                next_seq = 1

        for item in analyzed:
            data = item["data"]
            if item["outcome"] != "create":
                if item["outcome"] == "skip_duplicate":
                    skipped_count += 1
                continue

            contact = await get_or_create_contact(
                data["contact_email"], data.get("contact_name")
            )
            total = _parse_money(data["total"]) or Decimal("0.00")
            amount_paid = _parse_money(data.get("amount_paid", "")) or Decimal("0.00")
            due = _resolve_due_date(data)
            description = data.get("description") or "Imported invoice"

            invoice = Invoice(
                invoice_number=f"{prefix}{next_seq:04d}",
                contact_id=contact.id,
                organization_id=contact.organization_id,
                line_items=[
                    {
                        "description": description,
                        "quantity": 1,
                        "unit_price": float(total),
                        "amount": float(total),
                    }
                ],
                subtotal=total,
                total=total,
                amount_paid=amount_paid,
                balance_due=total - amount_paid,
                due_date=due,
                status="paid" if amount_paid >= total and total > 0 else "sent",
                notes=data.get("notes") or f"Imported from {preset_name}",
            )
            if invoice.status == "paid":
                invoice.paid_at = datetime.utcnow()
            next_seq += 1
            db.add(invoice)
            await db.flush()
            created_invoices.append(invoice.id)

            if amount_paid > 0:
                payment = Payment(
                    invoice_id=invoice.id,
                    amount=amount_paid,
                    payment_method="other",
                    payment_date=due,
                    status="completed",
                    reference=f"import:{invoice.invoice_number}",
                    notes="Historical payment recorded during migration",
                )
                db.add(payment)
                await db.flush()
                created_payments.append(payment.id)

    for item in analyzed if entity_type == "contacts" else []:
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

    created_count = (
        len(created_invoices) if entity_type == "invoices" else len(created_contacts)
    )
    job = ImportJob(
        source=preset_name,
        entity_type=entity_type,
        status="committed",
        total_rows=len(rows),
        created_count=created_count,
        skipped_count=skipped_count,
        updated_count=updated_count,
        error_count=_counts(analyzed)["error"],
        created_ids={
            "contacts": created_contacts,
            "organizations": created_orgs,
            "invoices": created_invoices,
            "payments": created_payments,
        },
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

    undone = {"contacts": 0, "organizations": 0, "invoices": 0, "payments": 0}
    skipped: list[str] = []

    # Invoices first: contacts created by the same job can only be removed once
    # nothing references them. Payments cascade from their invoice, so count
    # them here and let the delete take them.
    for payment_id in job.created_ids.get("payments", []):
        payment = (
            await db.execute(select(Payment).where(Payment.id == payment_id))
        ).scalar_one_or_none()
        if payment is None:
            continue
        await db.delete(payment)
        undone["payments"] += 1
    await db.flush()

    for invoice_id in job.created_ids.get("invoices", []):
        invoice = (
            await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        ).scalar_one_or_none()
        if invoice is None:
            continue
        # A payment recorded after the import means this invoice is live now.
        later_payments = (
            await db.execute(
                select(Payment).where(Payment.invoice_id == invoice_id)
            )
        ).scalars().first()
        if later_payments is not None:
            skipped.append(
                f"invoice {invoice.invoice_number} has payments recorded since import"
            )
            continue
        await db.delete(invoice)
        undone["invoices"] += 1
    await db.flush()

    for contact_id in job.created_ids.get("contacts", []):
        contact = (
            await db.execute(select(Contact).where(Contact.id == contact_id))
        ).scalar_one_or_none()
        if contact is None:
            continue
        remaining_invoices = (
            await db.execute(
                select(Invoice).where(Invoice.contact_id == contact_id)
            )
        ).scalars().first()
        if remaining_invoices is not None:
            skipped.append(
                f"contact {contact.email or contact.first_name} still has invoices"
            )
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
