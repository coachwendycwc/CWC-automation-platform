"""
Tests for Contract service.
"""
import pytest
from datetime import datetime, timedelta
import uuid

from app.services.contract_service import ContractService, MERGE_FIELDS
from app.models.contract import Contract
from app.models.contact import Contact
from app.models.organization import Organization


class TestContractServiceMergeFields:
    """Tests for merge field utilities."""

    def test_merge_fields_defined(self):
        """Test all expected merge fields exist."""
        expected_fields = [
            "client_name", "client_email", "client_phone",
            "company_name", "today_date", "contract_number",
            "service_type", "start_date", "end_date",
            "total_amount", "payment_terms", "session_count",
        ]
        for field in expected_fields:
            assert field in MERGE_FIELDS

    def test_merge_field_has_required_keys(self):
        """Test each merge field has required metadata."""
        for field_name, info in MERGE_FIELDS.items():
            assert "description" in info
            assert "category" in info
            assert "sample" in info
            assert info["category"] in ["auto", "custom"]

    def test_get_merge_field_info(self):
        """Test merge field info retrieval."""
        result = ContractService.get_merge_field_info()

        assert "auto_fields" in result
        assert "custom_fields" in result
        assert len(result["auto_fields"]) > 0
        assert len(result["custom_fields"]) > 0

    def test_extract_merge_fields(self):
        """Test extracting merge fields from content."""
        content = """
        Dear {{client_name}},
        This agreement is between {{company_name}} and you.
        Total: {{total_amount}}
        """

        fields = ContractService.extract_merge_fields(content)

        assert "client_name" in fields
        assert "company_name" in fields
        assert "total_amount" in fields
        assert len(fields) == 3

    def test_extract_merge_fields_duplicates(self):
        """Test duplicate fields are deduplicated."""
        content = "{{client_name}} agrees that {{client_name}} will..."

        fields = ContractService.extract_merge_fields(content)

        assert fields.count("client_name") == 1

    def test_extract_merge_fields_empty(self):
        """Test extraction from content with no fields."""
        content = "This is a plain text contract."

        fields = ContractService.extract_merge_fields(content)

        assert fields == []


class TestContractServiceRender:
    """Tests for content rendering."""

    def test_render_content_basic(self):
        """Test basic content rendering."""
        content = "Hello {{client_name}}, welcome!"
        merge_data = {"client_name": "Jane Doe"}

        result = ContractService.render_content(content, merge_data)

        assert result == "Hello Jane Doe, welcome!"

    def test_render_content_multiple_fields(self):
        """Test rendering with multiple fields."""
        content = "{{client_name}} from {{company_name}}"
        merge_data = {
            "client_name": "John Smith",
            "company_name": "Acme Corp",
        }

        result = ContractService.render_content(content, merge_data)

        assert result == "John Smith from Acme Corp"

    def test_render_content_missing_field(self):
        """Test unfilled fields remain as placeholders."""
        content = "Amount: {{total_amount}}"
        merge_data = {}

        result = ContractService.render_content(content, merge_data)

        assert result == "Amount: {{total_amount}}"

    def test_render_content_partial_data(self):
        """Test rendering with some fields missing."""
        content = "{{client_name}} owes {{total_amount}}"
        merge_data = {"client_name": "Jane"}

        result = ContractService.render_content(content, merge_data)

        assert result == "Jane owes {{total_amount}}"

    def test_render_preview(self):
        """Test preview rendering with sample data."""
        content = "Dear {{client_name}}, your total is {{total_amount}}."

        result = ContractService.render_preview(content)

        assert "Jane Smith" in result
        assert "$5,000.00" in result

    def test_render_preview_unknown_field(self):
        """Test preview with unknown field."""
        content = "Field: {{unknown_field}}"

        result = ContractService.render_preview(content)

        assert "[unknown_field]" in result


class TestContractServiceContractNumber:
    """Tests for contract number generation."""

    @pytest.mark.asyncio
    async def test_generate_first_contract_number(self, db_session):
        """Test generating first contract number of the year."""
        service = ContractService(db_session)

        result = await service.generate_contract_number()

        current_year = datetime.now().year
        assert result == f"CTR-{current_year}-001"

    @pytest.mark.asyncio
    async def test_generate_sequential_number(self, db_session, test_contact: Contact):
        """Test generating sequential contract numbers."""
        service = ContractService(db_session)

        # Create an existing contract
        year = datetime.now().year
        existing = Contract(
            id=str(uuid.uuid4()),
            contract_number=f"CTR-{year}-005",
            contact_id=test_contact.id,
            title="Test Contract",
            content="Test content",
            status="draft",
        )
        db_session.add(existing)
        await db_session.commit()

        result = await service.generate_contract_number()

        assert result == f"CTR-{year}-006"


class TestContractServiceAutoMergeData:
    """Tests for auto merge data building."""

    @pytest.mark.asyncio
    async def test_build_auto_merge_data_contact(self, db_session, test_contact: Contact):
        """Test building merge data from contact."""
        service = ContractService(db_session)

        result = await service.build_auto_merge_data(
            contact_id=test_contact.id,
        )

        assert "client_name" in result
        assert "client_email" in result
        assert "today_date" in result

    @pytest.mark.asyncio
    async def test_build_auto_merge_data_with_org(
        self, db_session, test_contact: Contact, test_organization: Organization
    ):
        """Test building merge data with organization."""
        service = ContractService(db_session)

        result = await service.build_auto_merge_data(
            contact_id=test_contact.id,
            organization_id=test_organization.id,
        )

        assert result.get("company_name") == test_organization.name

    @pytest.mark.asyncio
    async def test_build_auto_merge_data_with_contract_number(
        self, db_session, test_contact: Contact
    ):
        """Test building merge data with contract number."""
        service = ContractService(db_session)

        result = await service.build_auto_merge_data(
            contact_id=test_contact.id,
            contract_number="CTR-2024-001",
        )

        assert result["contract_number"] == "CTR-2024-001"


class TestContractServiceAudit:
    """Tests for audit logging."""

    @pytest.mark.asyncio
    async def test_log_action(self, db_session, test_contract: Contract):
        """Test creating audit log entry."""
        service = ContractService(db_session)

        result = await service.log_action(
            contract_id=test_contract.id,
            action="viewed",
            actor_email="viewer@example.com",
            ip_address="192.168.1.1",
        )

        assert result is not None
        assert result.contract_id == test_contract.id
        assert result.action == "viewed"


class TestContractServiceStats:
    """Tests for contract statistics."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, db_session):
        """Test stats with no contracts."""
        service = ContractService(db_session)

        result = await service.get_stats()

        assert result["total_contracts"] == 0
        assert result["signed_count"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_contracts(self, db_session, test_contact: Contact):
        """Test stats with existing contracts."""
        service = ContractService(db_session)

        # Create contracts with different statuses
        for status in ["draft", "sent", "signed", "signed"]:
            contract = Contract(
                id=str(uuid.uuid4()),
                contract_number=f"CTR-TEST-{uuid.uuid4().hex[:6]}",
                contact_id=test_contact.id,
                title="Test",
                content="Test content",
                status=status,
                signed_at=datetime.now() if status == "signed" else None,
            )
            db_session.add(contract)
        await db_session.commit()

        result = await service.get_stats()

        assert result["total_contracts"] >= 4
        assert result["signed_count"] >= 2


class TestContractServiceExpiry:
    """Tests for contract expiration."""

    @pytest.mark.asyncio
    async def test_check_expired_contracts(self, db_session, test_contact: Contact):
        """Test checking and marking expired contracts."""
        service = ContractService(db_session)

        # Create an expired contract
        expired = Contract(
            id=str(uuid.uuid4()),
            contract_number="CTR-EXPIRED-001",
            contact_id=test_contact.id,
            title="Expired Contract",
            content="Test content",
            status="sent",
            expires_at=datetime.now() - timedelta(days=1),
        )
        db_session.add(expired)
        await db_session.commit()

        count = await service.check_expired_contracts()

        assert count >= 1

        # Verify status was updated
        await db_session.refresh(expired)
        assert expired.status == "expired"

    @pytest.mark.asyncio
    async def test_check_expired_contracts_none_expired(self, db_session, test_contact: Contact):
        """Test when no contracts are expired."""
        service = ContractService(db_session)

        # Create a non-expired contract
        valid = Contract(
            id=str(uuid.uuid4()),
            contract_number="CTR-VALID-001",
            contact_id=test_contact.id,
            title="Valid Contract",
            content="Test content",
            status="sent",
            expires_at=datetime.now() + timedelta(days=30),
        )
        db_session.add(valid)
        await db_session.commit()

        count = await service.check_expired_contracts()

        # Only counts newly expired, not existing ones
        await db_session.refresh(valid)
        assert valid.status == "sent"

    def test_calculate_expiry_date(self):
        """Test expiry date calculation."""
        result = ContractService.calculate_expiry_date(30)

        expected = datetime.now() + timedelta(days=30)
        # Allow 1 second tolerance
        assert abs((result - expected).total_seconds()) < 1
