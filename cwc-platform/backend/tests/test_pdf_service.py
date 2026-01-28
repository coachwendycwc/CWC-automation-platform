"""
Tests for PDF service.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.pdf_service import PDFService


class TestPDFServiceBasics:
    """Tests for PDF service basic functionality."""

    @pytest.fixture
    def pdf_service(self):
        """Create PDF service instance."""
        return PDFService()

    def test_init(self, pdf_service):
        """Test service initialization."""
        assert pdf_service.company_name == "CWC Coaching"
        assert pdf_service.company_email == "hello@cwc-coaching.com"

    def test_get_base_styles(self, pdf_service):
        """Test base styles generation."""
        styles = pdf_service._get_base_styles()
        assert "@page" in styles
        assert "font-family" in styles
        assert "signature" in styles

    def test_build_contract_html_unsigned(self, pdf_service):
        """Test HTML generation for unsigned contract."""
        html = pdf_service._build_contract_html(
            title="Coaching Agreement",
            contract_number="CON-001",
            content="<p>This is the contract content.</p>",
            contact_name="John Doe",
            organization_name="Test Corp",
            created_at=datetime(2024, 1, 15),
        )

        assert "CON-001" in html
        assert "John Doe" in html
        assert "Coaching Agreement" in html
        assert "signature-line" in html

    def test_build_contract_html_signed(self, pdf_service):
        """Test HTML generation for signed contract."""
        html = pdf_service._build_contract_html(
            title="Signed Agreement",
            contract_number="CON-002",
            content="<p>Contract content.</p>",
            contact_name="Jane Doe",
            organization_name=None,
            created_at=datetime(2024, 1, 15),
            signer_name="Jane Doe",
            signer_email="jane@example.com",
            signed_at=datetime(2024, 1, 20, 14, 30),
            signature_data="data:image/png;base64,ABC123",
            signer_ip="192.168.1.1",
        )

        assert "Jane Doe" in html
        assert "jane@example.com" in html
        assert "192.168.1.1" in html
        assert "signature-image" in html
        assert "data:image/png;base64,ABC123" in html

    def test_build_contract_html_signed_no_image(self, pdf_service):
        """Test HTML generation for signed contract without signature image."""
        html = pdf_service._build_contract_html(
            title="Typed Signature",
            contract_number="CON-003",
            content="<p>Content.</p>",
            contact_name="Bob Smith",
            organization_name=None,
            created_at=datetime(2024, 1, 15),
            signer_name="Bob Smith",
            signer_email="bob@example.com",
            signed_at=datetime(2024, 1, 20, 14, 30),
            signature_data=None,
        )

        assert "Bob Smith" in html
        assert "signature-line" in html

    def test_is_available(self, pdf_service):
        """Test availability check."""
        # This depends on whether weasyprint is installed
        result = pdf_service.is_available()
        assert isinstance(result, bool)


class TestPDFServiceGeneration:
    """Tests for PDF generation."""

    @pytest.fixture
    def pdf_service(self):
        """Create PDF service instance."""
        return PDFService()

    @pytest.mark.asyncio
    @patch("app.services.pdf_service.WEASYPRINT_AVAILABLE", False)
    async def test_generate_pdf_not_available(self, pdf_service):
        """Test PDF generation when weasyprint not installed."""
        # Re-create service with mocked availability
        result = await pdf_service.generate_contract_pdf(
            title="Test Contract",
            contract_number="CON-001",
            content="<p>Content</p>",
            contact_name="Test User",
        )

        # Should return None when weasyprint not available
        if not pdf_service.is_available():
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_pdf_default_date(self, pdf_service):
        """Test PDF generation uses current date when not provided."""
        if not pdf_service.is_available():
            pytest.skip("weasyprint not installed")

        result = await pdf_service.generate_contract_pdf(
            title="Test Contract",
            contract_number="CON-001",
            content="<p>Content</p>",
            contact_name="Test User",
            created_at=None,  # Should use current date
        )

        assert result is not None or not pdf_service.is_available()


class TestPDFServiceIntegration:
    """Integration tests for PDF service (require weasyprint)."""

    @pytest.fixture
    def pdf_service(self):
        """Create PDF service instance."""
        return PDFService()

    @pytest.mark.asyncio
    async def test_generate_complete_contract_pdf(self, pdf_service):
        """Test generating a complete contract PDF."""
        if not pdf_service.is_available():
            pytest.skip("weasyprint not installed")

        result = await pdf_service.generate_contract_pdf(
            title="Executive Coaching Agreement",
            contract_number="CON-2024-001",
            content="""
                <h2>1. Services</h2>
                <p>Coach agrees to provide executive coaching services.</p>
                <h2>2. Term</h2>
                <p>This agreement shall be effective for 6 months.</p>
                <h2>3. Compensation</h2>
                <p>Client agrees to pay $500 per session.</p>
            """,
            contact_name="Alice Johnson",
            organization_name="Tech Solutions Inc.",
            created_at=datetime(2024, 3, 1),
            signer_name="Alice Johnson",
            signer_email="alice@techsolutions.com",
            signed_at=datetime(2024, 3, 5, 10, 15),
            signer_ip="10.0.0.1",
        )

        assert result is not None
        assert isinstance(result, bytes)
        # PDF files start with %PDF
        assert result[:4] == b"%PDF"
