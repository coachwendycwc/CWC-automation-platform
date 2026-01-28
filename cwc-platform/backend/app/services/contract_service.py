"""
Contract service for number generation, merge fields, and contract operations.
"""
import re
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.contract import Contract
from app.models.contract_template import ContractTemplate
from app.models.signature_audit_log import SignatureAuditLog
from app.models.contact import Contact
from app.models.organization import Organization


# Standard merge fields with descriptions and sample values
MERGE_FIELDS = {
    # Auto-populated fields
    "client_name": {
        "description": "Client's full name",
        "category": "auto",
        "sample": "Jane Smith",
    },
    "client_email": {
        "description": "Client's email address",
        "category": "auto",
        "sample": "jane@example.com",
    },
    "client_phone": {
        "description": "Client's phone number",
        "category": "auto",
        "sample": "(555) 123-4567",
    },
    "company_name": {
        "description": "Client's organization name",
        "category": "auto",
        "sample": "Acme Corp",
    },
    "today_date": {
        "description": "Today's date (formatted)",
        "category": "auto",
        "sample": datetime.now().strftime("%B %d, %Y"),
    },
    "contract_number": {
        "description": "Generated contract number",
        "category": "auto",
        "sample": "CTR-2025-001",
    },
    # Custom fields (user fills in)
    "service_type": {
        "description": "Type of service being provided",
        "category": "custom",
        "sample": "Executive Coaching",
    },
    "start_date": {
        "description": "Engagement start date",
        "category": "custom",
        "sample": "January 15, 2025",
    },
    "end_date": {
        "description": "Engagement end date",
        "category": "custom",
        "sample": "June 15, 2025",
    },
    "total_amount": {
        "description": "Total contract value",
        "category": "custom",
        "sample": "$5,000.00",
    },
    "payment_terms": {
        "description": "Payment schedule description",
        "category": "custom",
        "sample": "50% upfront, 50% at completion",
    },
    "session_count": {
        "description": "Number of sessions included",
        "category": "custom",
        "sample": "12 sessions",
    },
    "session_duration": {
        "description": "Duration of each session",
        "category": "custom",
        "sample": "60 minutes",
    },
    "scope_of_work": {
        "description": "Description of services to be provided",
        "category": "custom",
        "sample": "Leadership coaching and development",
    },
    "custom_terms": {
        "description": "Any custom terms or conditions",
        "category": "custom",
        "sample": "Sessions can be rescheduled with 24 hours notice.",
    },
}


class ContractService:
    """Service for contract operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_contract_number(self) -> str:
        """
        Generate unique contract number in format: CTR-YYYY-###
        Example: CTR-2025-001, CTR-2025-002, etc.
        """
        year = datetime.now().year
        prefix = f"CTR-{year}-"

        # Find the last contract number for this year
        result = await self.db.execute(
            select(Contract.contract_number)
            .where(Contract.contract_number.like(f"{prefix}%"))
            .order_by(Contract.contract_number.desc())
            .limit(1)
        )
        last_contract_number = result.scalar_one_or_none()

        if last_contract_number:
            last_num = int(last_contract_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:03d}"

    @staticmethod
    def get_merge_field_info() -> dict:
        """Get information about available merge fields."""
        auto_fields = []
        custom_fields = []

        for field_name, info in MERGE_FIELDS.items():
            field_info = {
                "name": field_name,
                "description": info["description"],
                "category": info["category"],
                "sample_value": info["sample"],
            }
            if info["category"] == "auto":
                auto_fields.append(field_info)
            else:
                custom_fields.append(field_info)

        return {
            "auto_fields": auto_fields,
            "custom_fields": custom_fields,
        }

    @staticmethod
    def extract_merge_fields(content: str) -> list[str]:
        """Extract merge field names from template content."""
        pattern = r"\{\{(\w+)\}\}"
        fields = re.findall(pattern, content)
        return list(set(fields))

    async def build_auto_merge_data(
        self,
        contact_id: str,
        organization_id: Optional[str] = None,
        contract_number: Optional[str] = None,
    ) -> dict:
        """Build merge data from auto-populated fields."""
        merge_data = {}

        # Get contact
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()

        if contact:
            merge_data["client_name"] = contact.full_name
            merge_data["client_email"] = contact.email or ""
            merge_data["client_phone"] = contact.phone or ""

        # Get organization
        if organization_id:
            result = await self.db.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            org = result.scalar_one_or_none()
            if org:
                merge_data["company_name"] = org.name
        elif contact and contact.organization_id:
            result = await self.db.execute(
                select(Organization).where(Organization.id == contact.organization_id)
            )
            org = result.scalar_one_or_none()
            if org:
                merge_data["company_name"] = org.name

        # Date and contract number
        merge_data["today_date"] = datetime.now().strftime("%B %d, %Y")
        if contract_number:
            merge_data["contract_number"] = contract_number

        return merge_data

    @staticmethod
    def render_content(content: str, merge_data: dict) -> str:
        """
        Replace merge fields in content with actual values.
        Unfilled fields remain as {{field_name}}.
        """
        def replace_field(match):
            field_name = match.group(1)
            return str(merge_data.get(field_name, match.group(0)))

        pattern = r"\{\{(\w+)\}\}"
        return re.sub(pattern, replace_field, content)

    @staticmethod
    def render_preview(content: str) -> str:
        """
        Render content with sample data for preview.
        """
        def replace_field(match):
            field_name = match.group(1)
            if field_name in MERGE_FIELDS:
                return MERGE_FIELDS[field_name]["sample"]
            return f"[{field_name}]"

        pattern = r"\{\{(\w+)\}\}"
        return re.sub(pattern, replace_field, content)

    async def log_action(
        self,
        contract_id: str,
        action: str,
        actor_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> SignatureAuditLog:
        """Create an audit log entry for a contract action."""
        log = SignatureAuditLog.log_action(
            contract_id=contract_id,
            action=action,
            actor_email=actor_email,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_stats(self) -> dict:
        """Get contract statistics for dashboard."""
        # Get counts by status
        count_result = await self.db.execute(
            select(
                func.count().filter(Contract.status != "void").label("total"),
                func.count().filter(Contract.status == "draft").label("draft"),
                func.count().filter(Contract.status.in_(["sent", "viewed"])).label("sent"),
                func.count().filter(Contract.status == "signed").label("signed"),
                func.count().filter(Contract.status.in_(["sent", "viewed"])).label("pending"),
                func.count().filter(Contract.status == "declined").label("declined"),
                func.count().filter(Contract.status == "expired").label("expired"),
            )
        )
        counts = count_result.one()

        # Signed this month
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        signed_month_result = await self.db.execute(
            select(func.count())
            .where(
                and_(
                    Contract.status == "signed",
                    Contract.signed_at >= first_of_month,
                )
            )
        )
        signed_this_month = signed_month_result.scalar_one()

        return {
            "total_contracts": counts.total,
            "draft_count": counts.draft,
            "sent_count": counts.sent,
            "signed_count": counts.signed,
            "pending_signature_count": counts.pending,
            "declined_count": counts.declined,
            "expired_count": counts.expired,
            "signed_this_month": signed_this_month,
        }

    async def check_expired_contracts(self) -> int:
        """
        Check for contracts past their expiration date and mark them as expired.
        Returns number of contracts marked as expired.
        """
        now = datetime.now()
        result = await self.db.execute(
            select(Contract)
            .where(
                and_(
                    Contract.status.in_(["sent", "viewed"]),
                    Contract.expires_at < now,
                )
            )
        )
        contracts = result.scalars().all()

        count = 0
        for contract in contracts:
            contract.status = "expired"
            await self.log_action(
                contract_id=contract.id,
                action="expired",
                details={"expired_at": now.isoformat()},
            )
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    @staticmethod
    def calculate_expiry_date(expiry_days: int) -> datetime:
        """Calculate expiration datetime from now."""
        return datetime.now() + timedelta(days=expiry_days)
