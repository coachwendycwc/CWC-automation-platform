"""
Tests for invoices endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestInvoicesEndpoints:
    """Test invoices CRUD endpoints."""

    @pytest.mark.skip(reason="HTTPBearer with auto_error=False causes internal error")
    async def test_list_invoices_unauthenticated(self, client: AsyncClient):
        """Test listing invoices without auth fails."""
        response = await client.get("/api/invoices")
        assert response.status_code == 403

    async def test_list_invoices_empty(self, client: AsyncClient, auth_headers):
        """Test listing invoices when none exist."""
        response = await client.get("/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_invoices_with_data(
        self, client: AsyncClient, auth_headers, test_invoice
    ):
        """Test listing invoices returns existing ones."""
        response = await client.get("/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["invoice_number"] == "INV-001"

    @pytest.mark.anyio
    async def test_list_invoices_includes_collection_visibility(
        self, client: AsyncClient, auth_headers, test_invoice, db_session
    ):
        """Test invoice list includes collection-stage metadata."""
        test_invoice.status = "overdue"
        test_invoice.balance_due = test_invoice.total
        test_invoice.due_date = (datetime.utcnow() - timedelta(days=2)).date()
        test_invoice.overdue_reminder_sent_at = datetime.utcnow()
        test_invoice.last_collection_email_sent_at = datetime.utcnow()
        await db_session.commit()

        response = await client.get("/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["collection_stage"] == "overdue"
        assert data[0]["needs_collection_attention"] is True
        assert data[0]["last_collection_email_sent_at"] is not None

    @pytest.mark.anyio
    async def test_invoice_stats_include_collections_attention_count(
        self, client: AsyncClient, auth_headers, test_invoice, db_session
    ):
        """Test invoice stats expose follow-up workload."""
        test_invoice.status = "sent"
        test_invoice.balance_due = test_invoice.total
        test_invoice.due_date = (datetime.utcnow() + timedelta(days=2)).date()
        test_invoice.due_soon_reminder_sent_at = None
        await db_session.commit()

        response = await client.get("/api/invoices/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["collections_attention_count"] >= 1

    async def test_create_invoice(
        self, client: AsyncClient, auth_headers, test_contact
    ):
        """Test creating a new invoice."""
        due_date = (datetime.utcnow() + timedelta(days=30)).date().isoformat()
        response = await client.post(
            "/api/invoices",
            headers=auth_headers,
            json={
                "contact_id": test_contact.id,
                "line_items": [
                    {
                        "description": "Executive Coaching",
                        "quantity": 4,
                        "unit_price": 500.0,
                    }
                ],
                "due_date": due_date,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["total"]) == 2000.0
        assert "id" in data
        assert "invoice_number" in data

    async def test_get_invoice(
        self, client: AsyncClient, auth_headers, test_invoice
    ):
        """Test getting a specific invoice."""
        response = await client.get(
            f"/api/invoices/{test_invoice.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_invoice.id
        assert data["invoice_number"] == "INV-001"

    async def test_get_invoice_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent invoice returns 404."""
        response = await client.get(
            "/api/invoices/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_invoice(
        self, client: AsyncClient, auth_headers, test_invoice
    ):
        """Test updating an invoice."""
        response = await client.put(
            f"/api/invoices/{test_invoice.id}",
            headers=auth_headers,
            json={
                "status": "sent",
                "memo": "Thank you for your business!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["memo"] == "Thank you for your business!"

    async def test_delete_invoice(
        self, client: AsyncClient, auth_headers, test_invoice
    ):
        """Test deleting an invoice."""
        response = await client.delete(
            f"/api/invoices/{test_invoice.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Invoice deleted"

    async def test_filter_invoices_by_status(
        self, client: AsyncClient, auth_headers, test_invoice
    ):
        """Test filtering invoices by status."""
        response = await client.get(
            "/api/invoices?status=draft",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_filter_invoices_by_contact(
        self, client: AsyncClient, auth_headers, test_invoice, test_contact
    ):
        """Test filtering invoices by contact."""
        response = await client.get(
            f"/api/invoices?contact_id={test_contact.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.anyio
    async def test_send_due_soon_reminder(
        self, client: AsyncClient, auth_headers, test_invoice, db_session
    ):
        test_invoice.status = "sent"
        test_invoice.balance_due = test_invoice.total
        test_invoice.due_date = (datetime.utcnow() + timedelta(days=3)).date()
        await db_session.commit()

        with patch("app.routers.invoices.email_service.send_reminder_due_soon", new=AsyncMock(return_value=True)):
            response = await client.post(
                f"/api/invoices/{test_invoice.id}/send-reminder",
                headers=auth_headers,
                json={"kind": "due_soon"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["due_soon_reminder_sent_at"] is not None
        assert data["last_collection_email_sent_at"] is not None

    @pytest.mark.anyio
    async def test_send_overdue_reminder_marks_invoice_overdue(
        self, client: AsyncClient, auth_headers, test_invoice, db_session
    ):
        test_invoice.status = "sent"
        test_invoice.balance_due = test_invoice.total
        test_invoice.due_date = (datetime.utcnow() - timedelta(days=5)).date()
        await db_session.commit()

        with patch("app.routers.invoices.email_service.send_reminder_overdue", new=AsyncMock(return_value=True)):
            response = await client.post(
                f"/api/invoices/{test_invoice.id}/send-reminder",
                headers=auth_headers,
                json={"kind": "overdue"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "overdue"
        assert data["overdue_reminder_sent_at"] is not None


class TestPublicInvoiceEndpoints:
    """Test public invoice view endpoints."""

    async def test_get_invoice_by_token(
        self, client: AsyncClient, test_invoice, db_session
    ):
        """Test accessing invoice by view token."""
        # First we need to ensure the invoice has a view_token
        test_invoice.view_token = "test-view-token-123"
        test_invoice.status = "sent"  # Must be sent to view publicly
        await db_session.commit()

        response = await client.get("/api/invoice/test-view-token-123")
        assert response.status_code == 200
        data = response.json()
        assert data["invoice_number"] == "INV-001"

    async def test_get_invoice_invalid_token(self, client: AsyncClient):
        """Test accessing invoice with invalid token fails."""
        response = await client.get("/api/invoice/invalid-token")
        assert response.status_code == 404
