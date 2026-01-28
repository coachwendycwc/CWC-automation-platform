"""
Tests for Fathom webhook handling.
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime
import uuid
import json
import hmac
import hashlib

from httpx import AsyncClient
from sqlalchemy import select

from app.models.fathom_webhook import FathomWebhook


class TestFathomWebhookEndpoint:
    """Tests for Fathom webhook receiver endpoint."""

    @pytest.mark.asyncio
    async def test_webhook_test_endpoint(self, client: AsyncClient):
        """Test the webhook test endpoint is reachable."""
        response = await client.get("/api/webhooks/fathom/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "active" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self, client: AsyncClient):
        """Test webhook with invalid signature is rejected."""
        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "real-secret-key"

            payload = {
                "recording_id": "rec_123",
                "title": "Test Call",
                "transcript": [{"speaker": "Host", "text": "Hello"}],
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "invalid-signature"}
            )
            assert response.status_code == 401
            assert "signature" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_webhook_valid_signature_stubbed(
        self, db_session, client: AsyncClient
    ):
        """Test webhook with stubbed signature verification."""
        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"  # Skip verification

            payload = {
                "recording_id": f"rec_{uuid.uuid4().hex[:8]}",
                "title": "Discovery Call with Client",
                "transcript": [
                    {"speaker": "Coach", "text": "Welcome to our call."},
                    {"speaker": "Client", "text": "Thank you for having me."},
                ],
                "duration_seconds": 1800,
                "recorded_at": "2024-01-15T10:30:00Z",
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "any-signature"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "received"
            assert data["recording_id"] == payload["recording_id"]

    @pytest.mark.asyncio
    async def test_webhook_stores_data_correctly(
        self, db_session, client: AsyncClient
    ):
        """Test webhook stores all data fields correctly."""
        recording_id = f"rec_store_{uuid.uuid4().hex[:8]}"

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"

            payload = {
                "recording_id": recording_id,
                "title": "Coaching Session",
                "transcript": [
                    {"speaker": "Coach", "text": "Let's discuss your goals."},
                    {"speaker": "Client", "text": "I want to improve leadership."},
                ],
                "default_summary": {"key_points": ["Goal setting", "Leadership"]},
                "action_items": [{"task": "Complete assessment", "assignee": "Client"}],
                "calendar_invitees": [{"email": "client@example.com", "name": "Client"}],
                "duration_seconds": 3600,
                "recorded_at": "2024-01-20T14:00:00Z",
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "test-sig"}
            )
            assert response.status_code == 200

        # Verify data was stored - use the test session
        result = await db_session.execute(
            select(FathomWebhook).where(FathomWebhook.recording_id == recording_id)
        )
        webhook = result.scalar_one_or_none()

        assert webhook is not None
        assert webhook.meeting_title == "Coaching Session"
        assert webhook.duration_seconds == 3600
        assert "Coach: Let's discuss" in webhook.transcript
        assert webhook.processing_status == "pending"

    @pytest.mark.asyncio
    async def test_webhook_duplicate_recording(
        self, db_session, client: AsyncClient
    ):
        """Test duplicate recording is rejected."""
        recording_id = f"rec_dup_{uuid.uuid4().hex[:8]}"

        # Create existing webhook record
        existing = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id=recording_id,
            meeting_title="Original Call",
            processing_status="pending",
        )
        db_session.add(existing)
        await db_session.commit()

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"

            payload = {
                "recording_id": recording_id,
                "title": "Duplicate Call",
                "transcript": [{"speaker": "Host", "text": "Test"}],
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "test-sig"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "duplicate"
            assert data["recording_id"] == recording_id

    @pytest.mark.asyncio
    async def test_webhook_invalid_json(self, client: AsyncClient):
        """Test webhook with invalid JSON payload."""
        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"

            response = await client.post(
                "/api/webhooks/fathom",
                content=b"not valid json",
                headers={
                    "Content-Type": "application/json",
                    "X-Fathom-Signature": "test-sig"
                }
            )
            assert response.status_code == 400
            assert "json" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_webhook_transcript_as_string(
        self, db_session, client: AsyncClient
    ):
        """Test webhook handles transcript as plain string."""
        recording_id = f"rec_str_{uuid.uuid4().hex[:8]}"

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"

            payload = {
                "recording_id": recording_id,
                "title": "String Transcript Call",
                "transcript": "This is a plain text transcript without speaker labels.",
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "test-sig"}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_no_transcript(
        self, db_session, client: AsyncClient
    ):
        """Test webhook without transcript field."""
        recording_id = f"rec_notrans_{uuid.uuid4().hex[:8]}"

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"

            payload = {
                "recording_id": recording_id,
                "title": "No Transcript Call",
                "duration_seconds": 600,
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "test-sig"}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_invalid_recorded_at(
        self, db_session, client: AsyncClient
    ):
        """Test webhook handles invalid recorded_at gracefully."""
        recording_id = f"rec_baddate_{uuid.uuid4().hex[:8]}"

        with patch("app.routers.webhooks.settings") as mock_settings:
            mock_settings.fathom_webhook_secret = "stubbed-for-now"

            payload = {
                "recording_id": recording_id,
                "title": "Bad Date Call",
                "recorded_at": "not-a-valid-date",
            }

            response = await client.post(
                "/api/webhooks/fathom",
                json=payload,
                headers={"X-Fathom-Signature": "test-sig"}
            )
            # Should still succeed, just with null recorded_at
            assert response.status_code == 200


class TestFathomSignatureVerification:
    """Tests for Fathom signature verification function."""

    def test_verify_signature_stubbed_mode(self):
        """Test signature verification in stubbed mode."""
        from app.routers.webhooks import verify_fathom_signature

        result = verify_fathom_signature(
            payload=b"any payload",
            signature="any signature",
            secret="stubbed-for-now"
        )
        assert result is True

    def test_verify_signature_valid(self):
        """Test valid signature verification."""
        from app.routers.webhooks import verify_fathom_signature

        payload = b'{"recording_id": "test"}'
        secret = "my-secret-key"

        # Generate valid signature
        expected_sig = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_fathom_signature(payload, expected_sig, secret)
        assert result is True

    def test_verify_signature_invalid(self):
        """Test invalid signature is rejected."""
        from app.routers.webhooks import verify_fathom_signature

        payload = b'{"recording_id": "test"}'
        secret = "my-secret-key"

        result = verify_fathom_signature(payload, "wrong-signature", secret)
        assert result is False

    def test_verify_signature_empty_payload(self):
        """Test signature verification with empty payload."""
        from app.routers.webhooks import verify_fathom_signature

        payload = b''
        secret = "my-secret-key"

        expected_sig = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = verify_fathom_signature(payload, expected_sig, secret)
        assert result is True


class TestFathomWebhookModel:
    """Tests for FathomWebhook model."""

    @pytest.mark.asyncio
    async def test_create_webhook_record(self, db_session):
        """Test creating a webhook record."""
        webhook = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id="rec_model_test",
            meeting_title="Model Test Call",
            transcript="Speaker 1: Hello\nSpeaker 2: Hi there",
            summary={"key_points": ["Greeting"]},
            action_items=[{"task": "Follow up"}],
            attendees=[{"email": "test@example.com"}],
            duration_seconds=900,
            recorded_at=datetime(2024, 1, 15, 10, 0, 0),
            processing_status="pending",
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        assert webhook.id is not None
        assert webhook.created_at is not None
        assert webhook.processing_status == "pending"

    @pytest.mark.asyncio
    async def test_webhook_status_transitions(self, db_session):
        """Test webhook status can be updated."""
        webhook = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id="rec_status_test",
            processing_status="pending",
        )
        db_session.add(webhook)
        await db_session.commit()

        # Update to processing
        webhook.processing_status = "processing"
        await db_session.commit()
        await db_session.refresh(webhook)
        assert webhook.processing_status == "processing"

        # Update to completed
        webhook.processing_status = "completed"
        webhook.processed_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(webhook)
        assert webhook.processing_status == "completed"
        assert webhook.processed_at is not None

    @pytest.mark.asyncio
    async def test_webhook_json_fields(self, db_session):
        """Test webhook JSON fields are properly stored and retrieved."""
        complex_summary = {
            "key_points": ["Point 1", "Point 2"],
            "sentiment": "positive",
            "topics": ["coaching", "goals"],
        }
        complex_action_items = [
            {"task": "Task 1", "assignee": "Client", "due": "2024-01-20"},
            {"task": "Task 2", "assignee": "Coach", "due": "2024-01-22"},
        ]

        webhook = FathomWebhook(
            id=str(uuid.uuid4()),
            recording_id="rec_json_test",
            summary=complex_summary,
            action_items=complex_action_items,
            processing_status="pending",
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        assert webhook.summary == complex_summary
        assert webhook.action_items == complex_action_items
        assert webhook.summary["sentiment"] == "positive"
        assert len(webhook.action_items) == 2
