"""
PDF service for generating contract PDFs.
Uses weasyprint for HTML to PDF conversion.

Note: weasyprint requires system dependencies:
- macOS: brew install pango
- Ubuntu: apt-get install libpango-1.0-0 libpangocairo-1.0-0
"""
import logging
from datetime import datetime
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import weasyprint, but don't fail if not available
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("weasyprint not installed. PDF generation will be disabled.")


class PDFService:
    """Service for generating PDF documents."""

    def __init__(self):
        self.company_name = "CWC Coaching"
        self.company_address = "123 Coaching Street, Suite 100"
        self.company_email = "hello@cwc-coaching.com"

    def _get_base_styles(self) -> str:
        """Get base CSS styles for PDF documents."""
        return """
            @page {
                size: letter;
                margin: 1in;
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10px;
                    color: #666;
                }
            }
            body {
                font-family: 'Helvetica', 'Arial', sans-serif;
                font-size: 12px;
                line-height: 1.5;
                color: #333;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #333;
                padding-bottom: 20px;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
                color: #1a1a1a;
            }
            .header .company-info {
                margin-top: 10px;
                font-size: 11px;
                color: #666;
            }
            .contract-meta {
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
                padding: 15px;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            .contract-meta .meta-item {
                text-align: left;
            }
            .contract-meta .meta-label {
                font-size: 10px;
                color: #666;
                text-transform: uppercase;
            }
            .contract-meta .meta-value {
                font-weight: bold;
                font-size: 14px;
            }
            .contract-content {
                margin-bottom: 40px;
            }
            .contract-content h2 {
                font-size: 16px;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            .contract-content p {
                margin-bottom: 10px;
            }
            .signature-section {
                margin-top: 40px;
                page-break-inside: avoid;
            }
            .signature-block {
                display: flex;
                justify-content: space-between;
                margin-top: 20px;
            }
            .signature-party {
                width: 45%;
            }
            .signature-line {
                border-bottom: 1px solid #333;
                height: 60px;
                margin-bottom: 5px;
            }
            .signature-image {
                height: 60px;
                margin-bottom: 5px;
            }
            .signature-image img {
                max-height: 50px;
                max-width: 200px;
            }
            .signature-name {
                font-weight: bold;
                margin-bottom: 5px;
            }
            .signature-date {
                font-size: 11px;
                color: #666;
            }
            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 10px;
                color: #666;
                text-align: center;
            }
            .e-signature-notice {
                font-size: 9px;
                color: #888;
                margin-top: 10px;
            }
        """

    def _build_contract_html(
        self,
        title: str,
        contract_number: str,
        content: str,
        contact_name: str,
        organization_name: Optional[str],
        created_at: datetime,
        signer_name: Optional[str] = None,
        signer_email: Optional[str] = None,
        signed_at: Optional[datetime] = None,
        signature_data: Optional[str] = None,
        signer_ip: Optional[str] = None,
    ) -> str:
        """Build HTML content for contract PDF."""
        # Signature block
        signature_html = ""
        if signed_at and signer_name:
            sig_image = ""
            if signature_data:
                sig_image = f'<div class="signature-image"><img src="{signature_data}" alt="Signature" /></div>'
            else:
                sig_image = '<div class="signature-line"></div>'

            signature_html = f"""
            <div class="signature-section">
                <h2>Signatures</h2>
                <div class="signature-block">
                    <div class="signature-party">
                        <p class="signature-name">{self.company_name}</p>
                        <div class="signature-line"></div>
                        <p class="signature-date">Date: _________________</p>
                    </div>
                    <div class="signature-party">
                        <p class="signature-name">{signer_name}</p>
                        {sig_image}
                        <p class="signature-date">Date: {signed_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                </div>
                <div class="e-signature-notice">
                    This document was signed electronically via CWC Platform.
                    Signer IP: {signer_ip or 'N/A'} | Email: {signer_email or 'N/A'}
                </div>
            </div>
            """
        else:
            signature_html = """
            <div class="signature-section">
                <h2>Signatures</h2>
                <div class="signature-block">
                    <div class="signature-party">
                        <p class="signature-name">""" + self.company_name + """</p>
                        <div class="signature-line"></div>
                        <p class="signature-date">Date: _________________</p>
                    </div>
                    <div class="signature-party">
                        <p class="signature-name">Client</p>
                        <div class="signature-line"></div>
                        <p class="signature-date">Date: _________________</p>
                    </div>
                </div>
            </div>
            """

        # Build full HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            <div class="header">
                <h1>{self.company_name}</h1>
                <div class="company-info">
                    {self.company_address}<br>
                    {self.company_email}
                </div>
            </div>

            <div class="contract-meta">
                <div class="meta-item">
                    <div class="meta-label">Contract Number</div>
                    <div class="meta-value">{contract_number}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Client</div>
                    <div class="meta-value">{contact_name}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Date</div>
                    <div class="meta-value">{created_at.strftime('%B %d, %Y')}</div>
                </div>
            </div>

            <div class="contract-title">
                <h1 style="font-size: 18px;">{title}</h1>
            </div>

            <div class="contract-content">
                {content}
            </div>

            {signature_html}

            <div class="footer">
                Contract Number: {contract_number} | Generated by CWC Platform
            </div>
        </body>
        </html>
        """

        return html

    async def generate_contract_pdf(
        self,
        title: str,
        contract_number: str,
        content: str,
        contact_name: str,
        organization_name: Optional[str] = None,
        created_at: Optional[datetime] = None,
        signer_name: Optional[str] = None,
        signer_email: Optional[str] = None,
        signed_at: Optional[datetime] = None,
        signature_data: Optional[str] = None,
        signer_ip: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Generate a PDF from contract data.

        Returns PDF bytes or None if weasyprint is not available.
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("Cannot generate PDF: weasyprint is not installed")
            return None

        if created_at is None:
            created_at = datetime.now()

        html_content = self._build_contract_html(
            title=title,
            contract_number=contract_number,
            content=content,
            contact_name=contact_name,
            organization_name=organization_name,
            created_at=created_at,
            signer_name=signer_name,
            signer_email=signer_email,
            signed_at=signed_at,
            signature_data=signature_data,
            signer_ip=signer_ip,
        )

        css = CSS(string=self._get_base_styles())
        html = HTML(string=html_content)

        pdf_bytes = html.write_pdf(stylesheets=[css])
        return pdf_bytes

    def is_available(self) -> bool:
        """Check if PDF generation is available."""
        return WEASYPRINT_AVAILABLE


# Singleton instance
pdf_service = PDFService()
