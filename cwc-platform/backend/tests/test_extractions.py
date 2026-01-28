"""
Tests for AI invoice extraction from Fathom transcripts.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from decimal import Decimal
import uuid

from httpx import AsyncClient
from sqlalchemy import select

from app.models.fathom_webhook import FathomWebhook
from app.models.fathom_extraction import FathomExtraction
from app.models.contact import Contact
from app.models.invoice import Invoice
from app.models.user import User


@pytest.fixture
async def test_fathom_webhook(db_session) -> FathomWebhook:
    """Create a test Fathom webhook record."""
    webhook = FathomWebhook(
        id=str(uuid.uuid4()),
        recording_id=f"rec_{uuid.uuid4().hex[:8]}",
        meeting_title="Discovery Call with Potential Client",
        transcript="Coach: Welcome! Let's discuss your goals.\nClient: I'm interested in the Executive Coaching package.\nCoach: That's $2,500 for 3 months.\nClient: Sounds good, my email is client@example.com",
        summary={"key_points": ["Executive coaching", "3-month package", "$2,500"]},
        action_items=[{"task": "Send contract"}],
        attendees=[{"email": "client@example.com", "name": "Jane Doe"}],
        duration_seconds=1800,
        recorded_at=datetime(2024, 1, 15, 10, 0, 0),
        processing_status="pending",
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)
    return webhook


@pytest.fixture
async def test_extraction(
    db_session, test_fathom_webhook: FathomWebhook, test_contact: Contact
) -> FathomExtraction:
    """Create a test extraction record."""
    extraction = FathomExtraction(
        id=str(uuid.uuid4()),
        fathom_webhook_id=test_fathom_webhook.id,
        contact_id=test_contact.id,
        extracted_data={
            "client_name": "John Doe",
            "client_email": "john.doe@example.com",
            "service_type": "executive_coaching",
            "package_name": "3-Month Executive Package",
            "total_amount": 2500.00,
            "is_billable": True,
            "key_topics": ["Leadership", "Career Growth"],
        },
        confidence_scores={
            "client_name": 0.95,
            "service_type": 0.85,
            "total_amount": 0.90,
        },
        status="pending",
    )
    db_session.add(extraction)
    await db_session.commit()
    await db_session.refresh(extraction)
    return extraction


class TestExtractionStats:
    """Tests for extraction statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_unauthenticated(self, client: AsyncClient):
        """Test stats endpoint requires authentication."""
        response = await client.get("/api/extractions/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, auth_client: AsyncClient):
        """Test stats with no extractions."""
        response = await auth_client.get("/api/extractions/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["pending_webhooks"] == 0
        assert data["pending_extractions"] == 0
        assert data["approved_today"] == 0
        assert data["total_extracted_value"] == 0.0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(
        self, auth_client: AsyncClient, test_fathom_webhook, test_extraction
    ):
        """Test stats with existing data."""
        response = await auth_client.get("/api/extractions/stats")
        assert response.status_code == 200
        data = response.json()
        # Should count the pending webhook and extraction
        assert data["pending_extractions"] >= 1


class TestListWebhooks:
    """Tests for listing Fathom webhooks."""

    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self, auth_client: AsyncClient):
        """Test listing webhooks when none exist."""
        response = await auth_client.get("/api/extractions/webhooks")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_webhooks_pending(
        self, auth_client: AsyncClient, test_fathom_webhook
    ):
        """Test listing pending webhooks."""
        response = await auth_client.get(
            "/api/extractions/webhooks",
            params={"status_filter": "pending"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["processing_status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_webhooks_all(
        self, auth_client: AsyncClient, test_fathom_webhook
    ):
        """Test listing all webhooks."""
        response = await auth_client.get(
            "/api/extractions/webhooks",
            params={"status_filter": "all"}
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestProcessWebhook:
    """Tests for processing webhooks with AI extraction."""

    @pytest.mark.asyncio
    async def test_process_webhook_not_found(self, auth_client: AsyncClient):
        """Test processing non-existent webhook."""
        response = await auth_client.post(
            f"/api/extractions/process/{uuid.uuid4()}"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_process_webhook_no_transcript(
        self, db_session, auth_client: AsyncClient
    ):
        """Test processing webhook without transcript."""
        webhook = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id="rec_no_transcript",
            meeting_title="Empty Call",
            transcript=None,  # No transcript
            processing_status="pending",
        )
        db_session.add(webhook)
        await db_session.commit()

        response = await auth_client.post(
            f"/api/extractions/process/{webhook.id}"
        )
        assert response.status_code == 400
        assert "transcript" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_process_webhook_already_processed(
        self, db_session, auth_client: AsyncClient, test_fathom_webhook, test_extraction
    ):
        """Test processing already-processed webhook."""
        response = await auth_client.post(
            f"/api/extractions/process/{test_fathom_webhook.id}"
        )
        assert response.status_code == 400
        assert "already processed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_process_webhook_success(
        self, db_session, auth_client: AsyncClient
    ):
        """Test successful webhook processing."""
        webhook = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id=f"rec_process_{uuid.uuid4().hex[:8]}",
            meeting_title="Sales Call",
            transcript="Coach: Let's discuss coaching options.\nClient: I need help with leadership.",
            processing_status="pending",
        )
        db_session.add(webhook)
        await db_session.commit()

        with patch("app.routers.extractions.ai_extraction_service") as mock_ai:
            mock_ai.extract_from_transcript = AsyncMock(return_value={
                "extraction": {
                    "client_name": "Test Client",
                    "client_email": "test@example.com",
                    "service_type": "leadership_coaching",
                    "is_billable": True,
                },
                "confidence": {
                    "client_name": 0.85,
                    "service_type": 0.75,
                },
            })

            response = await auth_client.post(
                f"/api/extractions/process/{webhook.id}"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["extracted_data"]["client_name"] == "Test Client"

    @pytest.mark.asyncio
    async def test_process_webhook_ai_error(
        self, db_session, auth_client: AsyncClient
    ):
        """Test handling AI extraction error."""
        webhook = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id=f"rec_error_{uuid.uuid4().hex[:8]}",
            meeting_title="Error Call",
            transcript="Some transcript content",
            processing_status="pending",
        )
        db_session.add(webhook)
        await db_session.commit()

        with patch("app.routers.extractions.ai_extraction_service") as mock_ai:
            mock_ai.extract_from_transcript = AsyncMock(return_value={
                "error": "AI service unavailable"
            })

            response = await auth_client.post(
                f"/api/extractions/process/{webhook.id}"
            )
            assert response.status_code == 500


class TestListExtractions:
    """Tests for listing extractions."""

    @pytest.mark.asyncio
    async def test_list_extractions_empty(self, auth_client: AsyncClient):
        """Test listing extractions when none exist."""
        response = await auth_client.get("/api/extractions")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_extractions_with_data(
        self, auth_client: AsyncClient, test_extraction
    ):
        """Test listing extractions with existing data."""
        response = await auth_client.get("/api/extractions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["pending_count"] >= 1

    @pytest.mark.asyncio
    async def test_list_extractions_filter_by_status(
        self, auth_client: AsyncClient, test_extraction
    ):
        """Test filtering extractions by status."""
        response = await auth_client.get(
            "/api/extractions",
            params={"status_filter": "pending"}
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "pending"


class TestGetExtraction:
    """Tests for getting a single extraction."""

    @pytest.mark.asyncio
    async def test_get_extraction_not_found(self, auth_client: AsyncClient):
        """Test getting non-existent extraction."""
        response = await auth_client.get(f"/api/extractions/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_extraction_success(
        self, auth_client: AsyncClient, test_extraction
    ):
        """Test getting extraction details."""
        response = await auth_client.get(f"/api/extractions/{test_extraction.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_extraction.id
        assert data["status"] == "pending"
        assert "extracted_data" in data
        assert "confidence_scores" in data


class TestReviewExtraction:
    """Tests for reviewing/approving extractions."""

    @pytest.mark.asyncio
    async def test_review_not_found(self, auth_client: AsyncClient):
        """Test reviewing non-existent extraction."""
        response = await auth_client.post(
            f"/api/extractions/{uuid.uuid4()}/review",
            json={"action": "approve"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_review_already_reviewed(
        self, db_session, auth_client: AsyncClient, test_extraction
    ):
        """Test reviewing already-reviewed extraction."""
        test_extraction.status = "approved"
        await db_session.commit()

        response = await auth_client.post(
            f"/api/extractions/{test_extraction.id}/review",
            json={"action": "approve"}
        )
        assert response.status_code == 400
        assert "already reviewed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_review_invalid_action(
        self, auth_client: AsyncClient, test_extraction
    ):
        """Test review with invalid action."""
        response = await auth_client.post(
            f"/api/extractions/{test_extraction.id}/review",
            json={"action": "invalid_action"}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_review_approve_success(
        self, db_session, auth_client: AsyncClient, test_extraction
    ):
        """Test approving an extraction."""
        with patch("app.routers.extractions.ai_extraction_service") as mock_ai:
            mock_ai.build_invoice_line_items.return_value = [
                {
                    "description": "Executive Coaching Package",
                    "quantity": 1,
                    "unit_price": Decimal("2500.00"),
                }
            ]

            response = await auth_client.post(
                f"/api/extractions/{test_extraction.id}/review",
                json={"action": "approve", "notes": "Looks good"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["extraction_status"] == "approved"

    @pytest.mark.asyncio
    async def test_review_reject_success(
        self, auth_client: AsyncClient, test_extraction
    ):
        """Test rejecting an extraction."""
        response = await auth_client.post(
            f"/api/extractions/{test_extraction.id}/review",
            json={"action": "reject", "notes": "Not a sales call"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["extraction_status"] == "rejected"

    @pytest.mark.asyncio
    async def test_review_edit_with_corrections(
        self, db_session, auth_client: AsyncClient, test_extraction
    ):
        """Test editing extraction with corrections."""
        with patch("app.routers.extractions.ai_extraction_service") as mock_ai:
            mock_ai.build_invoice_line_items.return_value = [
                {
                    "description": "Updated Coaching Package",
                    "quantity": 1,
                    "unit_price": Decimal("3000.00"),
                }
            ]

            response = await auth_client.post(
                f"/api/extractions/{test_extraction.id}/review",
                json={
                    "action": "edit",
                    "corrections": [
                        {
                            "field": "total_amount",
                            "original": 2500.00,
                            "corrected": 3000.00
                        }
                    ],
                    "notes": "Adjusted price"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["extraction_status"] == "approved"


class TestCreateInvoiceFromExtraction:
    """Tests for creating invoice from extraction."""

    @pytest.mark.asyncio
    async def test_create_invoice_not_found(self, auth_client: AsyncClient):
        """Test creating invoice from non-existent extraction."""
        response = await auth_client.post(
            f"/api/extractions/{uuid.uuid4()}/create-invoice"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invoice_already_exists(
        self, db_session, auth_client: AsyncClient, test_extraction, test_contact
    ):
        """Test creating invoice when one already exists."""
        # Create existing invoice
        invoice = Invoice(
            id=str(uuid.uuid4()),
            contact_id=test_contact.id,
            invoice_number="INV-EXIST-001",
            status="draft",
            line_items=[{"description": "Test", "quantity": 1, "unit_price": 100}],
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            due_date=datetime.utcnow().date(),
        )
        db_session.add(invoice)
        test_extraction.draft_invoice_id = invoice.id
        await db_session.commit()

        response = await auth_client.post(
            f"/api/extractions/{test_extraction.id}/create-invoice"
        )
        assert response.status_code == 400
        assert "already created" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_invoice_success(
        self, db_session, auth_client: AsyncClient, test_extraction
    ):
        """Test successfully creating invoice from extraction."""
        with patch("app.routers.extractions.ai_extraction_service") as mock_ai:
            mock_ai.build_invoice_line_items.return_value = [
                {
                    "description": "Coaching Package",
                    "quantity": 1,
                    "unit_price": Decimal("2500.00"),
                    "service_type": "coaching",
                }
            ]

            response = await auth_client.post(
                f"/api/extractions/{test_extraction.id}/create-invoice"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "invoice_id" in data


class TestFathomExtractionModel:
    """Tests for FathomExtraction model."""

    @pytest.mark.asyncio
    async def test_extraction_confidence_level_high(
        self, db_session, test_fathom_webhook
    ):
        """Test high confidence level calculation."""
        extraction = FathomExtraction(
            id=str(uuid.uuid4()),
            fathom_webhook_id=test_fathom_webhook.id,
            extracted_data={"is_billable": True},
            confidence_scores={
                "client_name": 0.95,
                "service_type": 0.90,
                "total_amount": 0.92,
            },
            status="pending",
        )
        db_session.add(extraction)
        await db_session.commit()
        await db_session.refresh(extraction)

        # Average is ~0.92, should be "high"
        assert extraction.get_confidence_level() == "high"

    @pytest.mark.asyncio
    async def test_extraction_confidence_level_medium(
        self, db_session, test_fathom_webhook
    ):
        """Test medium confidence level calculation."""
        extraction = FathomExtraction(
            id=str(uuid.uuid4()),
            fathom_webhook_id=test_fathom_webhook.id,
            extracted_data={"is_billable": True},
            confidence_scores={
                "client_name": 0.75,
                "service_type": 0.65,
                "total_amount": 0.70,
            },
            status="pending",
        )
        db_session.add(extraction)
        await db_session.commit()

        # Average is ~0.70, should be "medium"
        assert extraction.get_confidence_level() == "medium"

    @pytest.mark.asyncio
    async def test_extraction_add_correction(
        self, db_session, test_fathom_webhook
    ):
        """Test adding corrections to extraction."""
        extraction = FathomExtraction(
            id=str(uuid.uuid4()),
            fathom_webhook_id=test_fathom_webhook.id,
            extracted_data={"total_amount": 2500.00},
            confidence_scores={},
            status="pending",
        )
        db_session.add(extraction)
        await db_session.commit()

        extraction.add_correction(
            field="total_amount",
            original=2500.00,
            corrected=3000.00
        )
        await db_session.commit()
        await db_session.refresh(extraction)

        assert len(extraction.corrections) == 1
        assert extraction.corrections[0]["field"] == "total_amount"
        assert extraction.corrections[0]["corrected"] == 3000.00
