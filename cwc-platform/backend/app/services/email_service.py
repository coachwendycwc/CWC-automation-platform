"""
Email service with Gmail SMTP integration.
Sends real emails when Gmail credentials are configured, otherwise logs to console.
"""
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.models.invoice import Invoice
from app.models.contact import Contact
from app.config import get_settings

logger = logging.getLogger(__name__)


def _create_html_email(
    title: str,
    greeting: str,
    content: str,
    cta_text: Optional[str] = None,
    cta_url: Optional[str] = None,
    footer_text: str = "Best regards,<br>CWC Coaching",
) -> str:
    """
    Create a professional HTML email template.

    Args:
        title: Email title (shown in header)
        greeting: Greeting line (e.g., "Hi Sarah,")
        content: Main content (HTML allowed)
        cta_text: Call-to-action button text
        cta_url: Call-to-action button URL
        footer_text: Footer text
    """
    cta_button = ""
    if cta_text and cta_url:
        cta_button = f'''
        <div style="text-align: center; margin: 30px 0;">
            <a href="{cta_url}"
               style="background-color: #7c3aed; color: white; padding: 14px 28px;
                      text-decoration: none; border-radius: 6px; font-weight: 600;
                      display: inline-block;">
                {cta_text}
            </a>
        </div>
        '''

    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #7c3aed; padding: 24px 32px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: white; font-size: 20px; font-weight: 600;">
                                CWC Coaching
                            </h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <p style="margin: 0 0 16px; font-size: 16px; color: #374151;">
                                {greeting}
                            </p>
                            <div style="font-size: 15px; color: #4b5563; line-height: 1.6;">
                                {content}
                            </div>
                            {cta_button}
                            <p style="margin: 24px 0 0; font-size: 15px; color: #4b5563;">
                                {footer_text}
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 32px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; font-size: 12px; color: #9ca3af; text-align: center;">
                                © 2024 Coaching Women of Color. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''

class EmailService:
    """
    Email service for sending notifications.

    Uses Gmail SMTP when credentials are provided, otherwise logs to console.
    """

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    def __init__(self):
        settings = get_settings()
        self.gmail_email = settings.gmail_email
        self.gmail_password = settings.gmail_app_password
        self.from_name = "CWC Coaching"
        self.is_configured = bool(self.gmail_email and self.gmail_password)

        if self.is_configured:
            logger.info("Gmail SMTP email service initialized")
        else:
            logger.info("Email service running in stub mode (no Gmail credentials)")

    def _log_email(self, to: str, subject: str, body: str) -> None:
        """Log email details to console."""
        logger.info("=" * 60)
        logger.info("EMAIL STUB - Would send email:")
        logger.info(f"  To: {to}")
        logger.info(f"  Subject: {subject}")
        logger.info(f"  Body preview: {body[:200]}...")
        logger.info("=" * 60)

    async def _send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email via Gmail SMTP or log if not configured."""
        if not self.is_configured:
            self._log_email(to, subject, body)
            return True

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.gmail_email}>"
            message["To"] = to

            # Attach plain text and HTML versions
            part1 = MIMEText(body, "plain")
            message.attach(part1)

            if html_body:
                part2 = MIMEText(html_body, "html")
                message.attach(part2)

            # Send via Gmail SMTP
            context = ssl.create_default_context()
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(self.gmail_email, self.gmail_password)
                server.sendmail(self.gmail_email, to, message.as_string())

            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

    async def send_invoice(
        self,
        invoice: Invoice,
        contact: Contact,
        base_url: str,
        custom_message: Optional[str] = None,
    ) -> bool:
        """
        Send invoice notification to client.

        Args:
            invoice: The invoice to send
            contact: The contact to send to
            base_url: Base URL for the invoice view link
            custom_message: Optional custom message to include

        Returns:
            True if email would be sent successfully
        """
        if not contact.email:
            logger.warning(f"Cannot send invoice {invoice.invoice_number}: Contact has no email")
            return False

        view_url = f"{base_url}/pay/{invoice.view_token}"

        subject = f"Invoice #{invoice.invoice_number} from CWC Coaching"

        body = f"""
Hi {contact.first_name},

You have a new invoice from CWC Coaching.

Invoice: #{invoice.invoice_number}
Amount Due: ${invoice.balance_due:,.2f}
Due Date: {invoice.due_date.strftime('%B %d, %Y')}

{custom_message if custom_message else ''}

View and pay your invoice here:
{view_url}

Thank you for your business!

Best regards,
CWC Coaching
"""

        custom_text = f"<p>{custom_message}</p>" if custom_message else ""
        html_content = f'''
            <p>You have a new invoice from CWC Coaching.</p>
            {custom_text}
            <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                <tr>
                    <td style="padding: 12px; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb;">
                        <strong>Invoice Number</strong>
                    </td>
                    <td style="padding: 12px; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        #{invoice.invoice_number}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                        <strong>Amount Due</strong>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right; font-size: 18px; font-weight: bold; color: #7c3aed;">
                        ${invoice.balance_due:,.2f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px;">
                        <strong>Due Date</strong>
                    </td>
                    <td style="padding: 12px; text-align: right;">
                        {invoice.due_date.strftime('%B %d, %Y')}
                    </td>
                </tr>
            </table>
            <p>Thank you for your business!</p>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="View & Pay Invoice",
            cta_url=view_url,
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_payment_confirmation(
        self,
        invoice: Invoice,
        contact: Contact,
        amount_paid: float,
    ) -> bool:
        """
        Send payment confirmation to client.
        """
        if not contact.email:
            return False

        subject = f"Payment Received - Invoice #{invoice.invoice_number}"

        remaining = invoice.balance_due
        status_msg = "Your invoice has been paid in full." if remaining <= 0 else f"Remaining balance: ${remaining:,.2f}"

        body = f"""
Hi {contact.first_name},

Thank you for your payment!

Invoice: #{invoice.invoice_number}
Amount Received: ${amount_paid:,.2f}
{status_msg}

Best regards,
CWC Coaching
"""

        status_html = '<span style="color: #059669; font-weight: bold;">✓ Paid in Full</span>' if remaining <= 0 else f'Remaining balance: <strong>${remaining:,.2f}</strong>'
        html_content = f'''
            <p>Thank you for your payment!</p>
            <div style="background-color: #ecfdf5; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="margin: 0 0 8px; color: #065f46; font-size: 14px;">Payment Received</p>
                <p style="margin: 0; font-size: 28px; font-weight: bold; color: #059669;">${amount_paid:,.2f}</p>
            </div>
            <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                        Invoice Number
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        #{invoice.invoice_number}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px;">
                        Status
                    </td>
                    <td style="padding: 12px; text-align: right;">
                        {status_html}
                    </td>
                </tr>
            </table>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {contact.first_name},",
            content=html_content,
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_reminder_due_soon(
        self,
        invoice: Invoice,
        contact: Contact,
        base_url: str,
        days_until_due: int,
    ) -> bool:
        """
        Send reminder for invoice due soon (e.g., 3 days before).
        """
        if not contact.email:
            return False

        view_url = f"{base_url}/pay/{invoice.view_token}"

        subject = f"Reminder: Invoice #{invoice.invoice_number} due in {days_until_due} days"

        body = f"""
Hi {contact.first_name},

This is a friendly reminder that your invoice is due soon.

Invoice: #{invoice.invoice_number}
Amount Due: ${invoice.balance_due:,.2f}
Due Date: {invoice.due_date.strftime('%B %d, %Y')} ({days_until_due} days from now)

Pay your invoice here:
{view_url}

Best regards,
CWC Coaching
"""

        return await self._send_email(contact.email, subject, body)

    async def send_reminder_overdue(
        self,
        invoice: Invoice,
        contact: Contact,
        base_url: str,
        days_overdue: int,
    ) -> bool:
        """
        Send reminder for overdue invoice.
        """
        if not contact.email:
            return False

        view_url = f"{base_url}/pay/{invoice.view_token}"

        subject = f"Payment Overdue: Invoice #{invoice.invoice_number}"

        body = f"""
Hi {contact.first_name},

Your invoice is now {days_overdue} day{'s' if days_overdue != 1 else ''} overdue.

Invoice: #{invoice.invoice_number}
Amount Due: ${invoice.balance_due:,.2f}
Original Due Date: {invoice.due_date.strftime('%B %d, %Y')}

Please make your payment as soon as possible:
{view_url}

If you have any questions or concerns about this invoice, please don't hesitate to reach out.

Best regards,
CWC Coaching
"""

        return await self._send_email(contact.email, subject, body)

    # Contract email methods

    async def send_contract_notification(
        self,
        to_email: str,
        contact_name: str,
        contract_title: str,
        signing_link: str,
        expires_at: Optional["datetime"] = None,
        custom_message: Optional[str] = None,
    ) -> bool:
        """
        Send contract signing notification to client.
        """
        subject = f"Contract Ready for Signature: {contract_title}"

        expiry_text = ""
        if expires_at:
            expiry_text = f"\nPlease sign by: {expires_at.strftime('%B %d, %Y at %I:%M %p')}\n"

        custom_text = f"\n{custom_message}\n" if custom_message else ""

        body = f"""
Hi {contact_name.split()[0] if contact_name else 'there'},

A contract is ready for your review and signature.

Contract: {contract_title}
{expiry_text}
{custom_text}
Please review and sign your contract here:
{signing_link}

If you have any questions before signing, please don't hesitate to reach out.

Best regards,
CWC Coaching
"""

        return await self._send_email(to_email, subject, body)

    async def send_contract_signed_confirmation(
        self,
        to_email: str,
        contact_name: str,
        contract_title: str,
        contract_number: str,
        signed_at: "datetime",
    ) -> bool:
        """
        Send signature confirmation to client.
        """
        subject = f"Contract Signed: {contract_title}"

        body = f"""
Hi {contact_name.split()[0] if contact_name else 'there'},

Thank you for signing your contract!

Contract: {contract_title}
Contract Number: {contract_number}
Signed: {signed_at.strftime('%B %d, %Y at %I:%M %p')}

A copy of the signed contract is attached for your records.

We look forward to working with you!

Best regards,
CWC Coaching
"""

        return await self._send_email(to_email, subject, body)

    async def send_contract_signed_admin_notification(
        self,
        contract_title: str,
        contract_number: str,
        signer_name: str,
        signer_email: str,
        signed_at: "datetime",
    ) -> bool:
        """
        Send notification to admin when contract is signed.
        """
        admin_email = "admin@cwc-coaching.com"  # TODO: Make configurable
        subject = f"Contract Signed: {contract_number}"

        body = f"""
A contract has been signed!

Contract: {contract_title}
Contract Number: {contract_number}
Signed by: {signer_name} ({signer_email})
Signed at: {signed_at.strftime('%B %d, %Y at %I:%M %p')}

View the signed contract in your dashboard.
"""

        return await self._send_email(admin_email, subject, body)

    async def send_contract_reminder(
        self,
        to_email: str,
        contact_name: str,
        contract_title: str,
        signing_link: str,
        expires_at: Optional["datetime"] = None,
    ) -> bool:
        """
        Send reminder for unsigned contract.
        """
        subject = f"Reminder: Contract Awaiting Signature - {contract_title}"

        expiry_text = ""
        if expires_at:
            expiry_text = f"\nThis contract expires on: {expires_at.strftime('%B %d, %Y at %I:%M %p')}\n"

        body = f"""
Hi {contact_name.split()[0] if contact_name else 'there'},

This is a friendly reminder that your contract is still awaiting signature.

Contract: {contract_title}
{expiry_text}
Please review and sign your contract here:
{signing_link}

If you have any questions, please don't hesitate to reach out.

Best regards,
CWC Coaching
"""

        return await self._send_email(to_email, subject, body)

    # Booking email methods

    async def send_booking_confirmation(
        self,
        to_email: str,
        contact_name: str,
        booking_type: str,
        booking_date: "datetime",
        booking_duration: int,
        meeting_link: Optional[str] = None,
    ) -> bool:
        """Send booking confirmation to client."""
        subject = f"Booking Confirmed: {booking_type}"

        meeting_text = f"\n\nJoin here: {meeting_link}" if meeting_link else ""

        body = f"""
Hi {contact_name.split()[0] if contact_name else 'there'},

Your booking has been confirmed!

What: {booking_type}
When: {booking_date.strftime('%A, %B %d, %Y at %I:%M %p')}
Duration: {booking_duration} minutes{meeting_text}

Please add this to your calendar. If you need to reschedule or cancel, please let us know at least 24 hours in advance.

Looking forward to speaking with you!

Best regards,
CWC Coaching
"""

        first_name = contact_name.split()[0] if contact_name else 'there'
        meeting_row = f'''
                <tr>
                    <td style="padding: 12px;">
                        <strong>Meeting Link</strong>
                    </td>
                    <td style="padding: 12px; text-align: right;">
                        <a href="{meeting_link}" style="color: #7c3aed;">Join Meeting</a>
                    </td>
                </tr>
        ''' if meeting_link else ""

        html_content = f'''
            <p>Your booking has been confirmed!</p>
            <div style="background-color: #f0fdf4; border-radius: 8px; padding: 16px; margin: 20px 0; border-left: 4px solid #22c55e;">
                <p style="margin: 0; color: #166534; font-weight: 600;">✓ Confirmed</p>
            </div>
            <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                <tr>
                    <td style="padding: 12px; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb;">
                        <strong>Session</strong>
                    </td>
                    <td style="padding: 12px; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        {booking_type}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                        <strong>Date & Time</strong>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        {booking_date.strftime('%A, %B %d, %Y')}<br>
                        <span style="color: #7c3aed; font-weight: 600;">{booking_date.strftime('%I:%M %p')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                        <strong>Duration</strong>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                        {booking_duration} minutes
                    </td>
                </tr>
                {meeting_row}
            </table>
            <p style="font-size: 13px; color: #6b7280;">
                Please add this to your calendar. If you need to reschedule or cancel,
                please let us know at least 24 hours in advance.
            </p>
            <p>Looking forward to speaking with you!</p>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {first_name},",
            content=html_content,
            cta_text="Join Meeting" if meeting_link else None,
            cta_url=meeting_link,
        )

        return await self._send_email(to_email, subject, body, html_body)

    async def send_booking_reminder(
        self,
        to_email: str,
        contact_name: str,
        booking_type: str,
        booking_date: "datetime",
        meeting_link: Optional[str] = None,
        hours_until: int = 24,
    ) -> bool:
        """Send booking reminder to client."""
        subject = f"Reminder: {booking_type} in {hours_until} hours"

        meeting_text = f"\n\nJoin here: {meeting_link}" if meeting_link else ""

        body = f"""
Hi {contact_name.split()[0] if contact_name else 'there'},

This is a friendly reminder about your upcoming session.

What: {booking_type}
When: {booking_date.strftime('%A, %B %d, %Y at %I:%M %p')}{meeting_text}

See you soon!

Best regards,
CWC Coaching
"""

        return await self._send_email(to_email, subject, body)

    async def send_booking_cancelled(
        self,
        to_email: str,
        contact_name: str,
        booking_type: str,
        booking_date: "datetime",
    ) -> bool:
        """Send booking cancellation notice to client."""
        subject = f"Booking Cancelled: {booking_type}"

        body = f"""
Hi {contact_name.split()[0] if contact_name else 'there'},

Your booking has been cancelled.

What: {booking_type}
Was scheduled for: {booking_date.strftime('%A, %B %d, %Y at %I:%M %p')}

If you'd like to reschedule, please book a new time at your convenience.

Best regards,
CWC Coaching
"""

        return await self._send_email(to_email, subject, body)

    # Password reset email

    async def send_password_reset(
        self,
        to_email: str,
        reset_link: str,
    ) -> bool:
        """Send password reset email."""
        subject = "Reset Your Password - CWC Platform"

        body = f"""
Hi,

You requested to reset your password for CWC Platform.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

Best regards,
CWC Platform Team
"""

        return await self._send_email(to_email, subject, body)

    # Offboarding email methods

    async def send_offboarding_completion(
        self,
        to_email: str,
        contact_name: str,
        workflow_type: str,
        project_title: Optional[str] = None,
        custom_message: Optional[str] = None,
    ) -> bool:
        """Send completion/thank you email when offboarding a client."""
        first_name = contact_name.split()[0] if contact_name else "there"

        type_text = {
            "client": "coaching engagement",
            "project": f"project{f' ({project_title})' if project_title else ''}",
            "contract": "contract",
        }.get(workflow_type, "engagement")

        subject = f"Thank You for Working with Coaching Women of Color"

        custom_text = f"\n{custom_message}\n" if custom_message else ""

        body = f"""
Hi {first_name},

Thank you for the opportunity to work together during our {type_text}!
{custom_text}
It has been a pleasure supporting you on your journey. We hope our work together has been valuable and impactful.

If you ever need support in the future, please don't hesitate to reach out. We're always here to help.

Wishing you continued success!

Warm regards,
Coaching Women of Color
"""

        html_content = f'''
            <p>Thank you for the opportunity to work together during our {type_text}!</p>
            {f'<p>{custom_message}</p>' if custom_message else ''}
            <p>It has been a pleasure supporting you on your journey. We hope our work together has been valuable and impactful.</p>
            <div style="background-color: #fdf4ff; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; border: 1px solid #e879f9;">
                <p style="margin: 0; color: #86198f; font-size: 16px;">
                    If you ever need support in the future, please don't hesitate to reach out.
                    We're always here to help.
                </p>
            </div>
            <p>Wishing you continued success!</p>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {first_name},",
            content=html_content,
            footer_text="Warm regards,<br>Coaching Women of Color",
        )

        return await self._send_email(to_email, subject, body, html_body)

    async def send_survey_request(
        self,
        to_email: str,
        contact_name: str,
        survey_url: str,
        workflow_type: str = "client",
    ) -> bool:
        """Send feedback survey request email."""
        first_name = contact_name.split()[0] if contact_name else "there"

        subject = "Your Feedback Matters - End-of-Engagement Survey"

        body = f"""
Hi {first_name},

Congratulations on completing your coaching journey with us! Your growth and progress have been a joy to witness.

We'd love to hear about your experience. Your honest feedback helps us:
- Celebrate your wins and growth together
- Understand what worked best for you
- Continuously improve for future clients

The survey covers:
- Your overall experience and satisfaction
- Growth and outcomes you've achieved
- What was most helpful in our coaching process
- Your experience feeling supported as a woman of color

There's also an optional section if you'd like to share a testimonial.

Take the survey here (about 5-7 minutes):
{survey_url}

Your responses are deeply valued and help us serve women of color more effectively.

With gratitude,
Coaching Women of Color
"""

        html_content = f'''
            <p>Congratulations on completing your coaching journey with us! Your growth and progress have been a joy to witness.</p>
            <p>We'd love to hear about your experience. Your honest feedback helps us:</p>
            <ul style="color: #4b5563; line-height: 1.8;">
                <li>Celebrate your wins and growth together</li>
                <li>Understand what worked best for you</li>
                <li>Continuously improve for future clients</li>
            </ul>
            <div style="background-color: #f5f3ff; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <p style="margin: 0 0 12px; color: #5b21b6; font-weight: 600;">The survey covers:</p>
                <ul style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                    <li>Your overall experience and satisfaction</li>
                    <li>Growth and outcomes you've achieved</li>
                    <li>What was most helpful in our coaching process</li>
                    <li>Your experience feeling supported as a woman of color</li>
                </ul>
                <p style="margin: 12px 0 0; color: #6b7280; font-size: 13px; font-style: italic;">
                    There's also an optional section if you'd like to share a testimonial.
                </p>
            </div>
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 12px 16px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    ⏱️ This survey takes about 5-7 minutes to complete
                </p>
            </div>
            <p>Your responses are deeply valued and help us serve women of color more effectively.</p>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {first_name},",
            content=html_content,
            cta_text="Share Your Feedback",
            cta_url=survey_url,
            footer_text="With gratitude,<br>Coaching Women of Color",
        )

        return await self._send_email(to_email, subject, body, html_body)

    async def send_testimonial_request(
        self,
        to_email: str,
        contact_name: str,
        testimonial_url: str,
        workflow_type: str = "client",
    ) -> bool:
        """Send testimonial request email."""
        first_name = contact_name.split()[0] if contact_name else "there"

        subject = "Would You Share Your Experience?"

        body = f"""
Hi {first_name},

We're so glad we could support you on your journey!

If our work together has been valuable to you, would you consider sharing your experience? Your words could help other women of color who are considering taking the next step in their careers.

You can share a written testimonial, or if you'd prefer, record a short video (just 1-2 minutes) sharing your story. Video testimonials are especially powerful for helping others see the real impact of coaching.

Share your story here:
{testimonial_url}

What to include:
- What brought you to coaching
- A specific win or breakthrough you experienced
- How you've grown through our work together
- Who you'd recommend this to

No pressure at all - only if you feel comfortable. We truly appreciate you either way!

Warm regards,
Coaching Women of Color
"""

        html_content = f'''
            <p>We're so glad we could support you on your journey!</p>
            <p>If our work together has been valuable to you, would you consider sharing your experience? Your words could help other women of color who are considering taking the next step in their careers.</p>
            <div style="background-color: #f0fdf4; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #86efac;">
                <p style="margin: 0 0 12px; color: #166534; font-weight: 600; text-align: center;">
                    ✨ Your story could inspire someone else's journey
                </p>
                <p style="margin: 0; color: #4b5563; font-size: 14px; text-align: center;">
                    Share a written testimonial or record a short video (1-2 minutes).<br>
                    Video testimonials are especially powerful!
                </p>
            </div>
            <div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <p style="margin: 0 0 8px; color: #374151; font-weight: 600; font-size: 14px;">What to include:</p>
                <ul style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6; padding-left: 20px;">
                    <li>What brought you to coaching</li>
                    <li>A specific win or breakthrough you experienced</li>
                    <li>How you've grown through our work together</li>
                    <li>Who you'd recommend this to</li>
                </ul>
            </div>
            <p style="font-size: 13px; color: #6b7280;">
                No pressure at all - only if you feel comfortable. We truly appreciate you either way!
            </p>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {first_name},",
            content=html_content,
            cta_text="Share Your Story",
            cta_url=testimonial_url,
            footer_text="Warm regards,<br>Coaching Women of Color",
        )

        return await self._send_email(to_email, subject, body, html_body)

    # Note notification email methods

    async def send_note_to_coach_notification(
        self,
        coach_email: str,
        client_name: str,
        note_content: str,
        notes_url: str,
    ) -> bool:
        """Send notification to coach when client sends a note."""
        subject = f"New message from {client_name}"

        # Truncate content for preview
        preview = note_content[:200] + "..." if len(note_content) > 200 else note_content

        body = f"""
Hi,

You have a new message from {client_name}:

"{preview}"

View and reply to this message:
{notes_url}

Best regards,
CWC Platform
"""

        html_content = f'''
            <p>You have a new message from <strong>{client_name}</strong>:</p>
            <div style="background-color: #f3f4f6; border-radius: 8px; padding: 16px; margin: 20px 0; border-left: 4px solid #3b82f6;">
                <p style="margin: 0; color: #374151; font-style: italic;">"{preview}"</p>
            </div>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting="Hi,",
            content=html_content,
            cta_text="View Messages",
            cta_url=notes_url,
            footer_text="Best regards,<br>CWC Platform",
        )

        return await self._send_email(coach_email, subject, body, html_body)

    async def send_note_to_client_notification(
        self,
        client_email: str,
        client_name: str,
        note_content: str,
        portal_url: str,
    ) -> bool:
        """Send notification to client when coach sends a note."""
        first_name = client_name.split()[0] if client_name else "there"
        subject = "New message from your coach"

        # Truncate content for preview
        preview = note_content[:200] + "..." if len(note_content) > 200 else note_content

        body = f"""
Hi {first_name},

You have a new message from your coach:

"{preview}"

View your messages:
{portal_url}

Best regards,
CWC Coaching
"""

        html_content = f'''
            <p>You have a new message from your coach:</p>
            <div style="background-color: #f0fdf4; border-radius: 8px; padding: 16px; margin: 20px 0; border-left: 4px solid #22c55e;">
                <p style="margin: 0; color: #374151; font-style: italic;">"{preview}"</p>
            </div>
        '''

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {first_name},",
            content=html_content,
            cta_text="View Messages",
            cta_url=portal_url,
            footer_text="Best regards,<br>CWC Coaching",
        )

        return await self._send_email(client_email, subject, body, html_body)

    async def send_assessment_notification(
        self,
        assessment,  # OrganizationalAssessment
        admin_email: str,
    ) -> bool:
        """Send notification to admin when new assessment is submitted."""
        settings = get_settings()

        subject = f"New Organizational Assessment: {assessment.organization_name}"

        # Format areas of interest
        areas_map = {
            "executive_coaching": "Executive Coaching (1:1)",
            "group_coaching": "Group Coaching / Cohorts",
            "keynote_speaking": "Keynote Speaking",
            "webinars_workshops": "Webinars & Workshops",
            "virtual_series": "Multi-Session Virtual Series",
            "other": "Other",
        }
        areas = [areas_map.get(a, a) for a in (assessment.areas_of_interest or [])]

        # Format budget
        budget_map = {
            "under_5k": "Under $5,000",
            "5k_10k": "$5,000–$9,999",
            "10k_20k": "$10,000–$19,999",
            "20k_40k": "$20,000–$39,999",
            "40k_plus": "$40,000+",
            "not_sure": "Not sure yet",
        }
        budget = budget_map.get(assessment.budget_range, assessment.budget_range or "Not specified")

        # Format timeline
        timeline_map = {
            "asap": "ASAP (2-4 weeks)",
            "1_2_months": "1–2 months",
            "3_4_months": "3–4 months",
            "5_plus_months": "5+ months",
            "not_sure": "Not sure yet",
        }
        timeline = timeline_map.get(assessment.ideal_timeline, assessment.ideal_timeline or "Not specified")

        body = f"""
New Organizational Needs Assessment Submitted

Contact Information:
- Name: {assessment.full_name}
- Title: {assessment.title_role}
- Organization: {assessment.organization_name}
- Email: {assessment.work_email}
- Phone: {assessment.phone_number or "Not provided"}

Areas of Interest: {", ".join(areas) if areas else "None selected"}

Budget Range: {budget}
Timeline: {timeline}

Current Challenge:
{assessment.current_challenge or "Not provided"}

Success Definition:
{assessment.success_definition or "Not provided"}

View in admin: {settings.frontend_url}/assessments/{assessment.id}
"""

        html_content = f'''
            <h3 style="color: #374151; margin-bottom: 16px;">Contact Information</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Name:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{assessment.full_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Title:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{assessment.title_role}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Organization:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{assessment.organization_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><a href="mailto:{assessment.work_email}">{assessment.work_email}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Phone:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{assessment.phone_number or "Not provided"}</td>
                </tr>
            </table>

            <h3 style="color: #374151; margin-bottom: 16px;">Interests & Budget</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Areas of Interest:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{", ".join(areas) if areas else "None selected"}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Budget:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{budget}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Timeline:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{timeline}</td>
                </tr>
            </table>

            {f'<h3 style="color: #374151; margin-bottom: 16px;">Current Challenge</h3><p style="background-color: #fef3c7; padding: 16px; border-radius: 8px; margin-bottom: 24px;">{assessment.current_challenge}</p>' if assessment.current_challenge else ''}

            {f'<h3 style="color: #374151; margin-bottom: 16px;">Success Definition</h3><p style="background-color: #dbeafe; padding: 16px; border-radius: 8px; margin-bottom: 24px;">{assessment.success_definition}</p>' if assessment.success_definition else ''}
        '''

        html_body = _create_html_email(
            title=subject,
            greeting="New assessment submitted!",
            content=html_content,
            cta_text="View Full Assessment",
            cta_url=f"{settings.frontend_url}/assessments/{assessment.id}",
            footer_text="",
        )

        return await self._send_email(admin_email, subject, body, html_body)

    async def send_onboarding_assessment(
        self,
        contact,
        assessment_url: str,
    ) -> bool:
        """
        Send onboarding assessment email to new coachee after payment.
        """
        subject = "Welcome! Please Complete Your Onboarding Assessment"

        body = f"""
Hi {contact.first_name},

Welcome to Coaching Women of Color!

Thank you for your payment. Before your first coaching session, please complete your onboarding assessment.
This helps me understand your goals, challenges, and what you hope to achieve through our work together.

Complete your assessment here:
{assessment_url}

This is required before your first session.

Looking forward to working with you!

Best,
Dr. Adaora Onyinyechukwuka Ogbue, DNP, MBA, PMP
Coaching Women of Color
        """

        html_content = f"""
        <p style="margin-bottom: 16px;">Welcome to Coaching Women of Color!</p>

        <p style="margin-bottom: 16px;">Thank you for your payment. Before your first coaching session, please complete your <strong>onboarding assessment</strong>.</p>

        <p style="margin-bottom: 16px;">This helps me understand:</p>
        <ul style="margin-bottom: 24px; padding-left: 20px;">
            <li>Your current role and responsibilities</li>
            <li>Your goals and what success looks like for you</li>
            <li>Your challenges and areas you'd like to focus on</li>
            <li>Your preferences for our work together</li>
        </ul>

        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
            <strong>Important:</strong> Completing this assessment is required before your first coaching session.
        </div>
        """

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="Complete Assessment",
            cta_url=assessment_url,
            footer_text="Looking forward to working with you!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    # =========================================================================
    # WORKFLOW AUTOMATION EMAILS
    # =========================================================================

    async def send_assessment_reminder(
        self,
        contact,
        assessment_url: str,
        day: int,
    ) -> bool:
        """Send reminder for incomplete onboarding assessment."""
        if day == 1:
            subject = "Reminder: Complete Your Onboarding Assessment"
            urgency = "When you have a moment"
        elif day == 3:
            subject = "Don't Forget: Your Onboarding Assessment"
            urgency = "We'd love to hear from you"
        else:  # day 7
            subject = "Final Reminder: Complete Your Assessment Before Your First Session"
            urgency = "Please complete this soon"

        body = f"""
Hi {contact.first_name},

{urgency}, please complete your onboarding assessment. This helps us prepare for your coaching journey and tailor our sessions to your unique needs and goals.

Complete your assessment here:
{assessment_url}

This is required before your first coaching session.

If you have any questions, just reply to this email.

Best,
Dr. Adaora Onyinyechukwuka Ogbue, DNP, MBA, PMP
Coaching Women of Color
        """

        html_content = f"""
        <p style="margin-bottom: 16px;">{urgency}, please complete your <strong>onboarding assessment</strong>.</p>

        <p style="margin-bottom: 16px;">This helps us prepare for your coaching journey and tailor our sessions to your unique needs and goals.</p>

        {"<div style='background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin-bottom: 24px; border-radius: 4px;'><strong>Reminder:</strong> This is required before your first coaching session.</div>" if day >= 3 else ""}
        """

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="Complete Assessment",
            cta_url=assessment_url,
            footer_text="Looking forward to working with you!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_welcome_series(
        self,
        contact,
        day: int,
        assessment=None,
    ) -> bool:
        """Send welcome series emails after assessment completion."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/dashboard"

        if day == 0:
            subject = "Welcome to Your Coaching Journey!"
            body = f"""
Hi {contact.first_name},

Thank you for completing your onboarding assessment! I've reviewed your responses and I'm excited to begin our work together.

Here are a few things you can do now:
- Access your client portal: {portal_url}
- Review your upcoming sessions
- Check out resources I've prepared for you

Looking forward to our first session!

Warmly,
Dr. Adaora Onyinyechukwuka Ogbue, DNP, MBA, PMP
Coaching Women of Color
            """
            html_content = """
            <p style="margin-bottom: 16px;">Thank you for completing your onboarding assessment! I've reviewed your responses and I'm excited to begin our work together.</p>

            <p style="margin-bottom: 16px;"><strong>Here are a few things you can do now:</strong></p>
            <ul style="margin-bottom: 24px; padding-left: 20px;">
                <li>Access your client portal</li>
                <li>Review your upcoming sessions</li>
                <li>Check out resources I've prepared for you</li>
            </ul>
            """
        elif day == 3:
            subject = "Getting Started with Your Goals"
            body = f"""
Hi {contact.first_name},

I hope you're settling into your coaching journey!

As you prepare for our sessions, I encourage you to:
- Reflect on the goals you shared in your assessment
- Notice any patterns or thoughts that come up during your day
- Jot down any questions or topics you'd like to explore

Your client portal is always available at: {portal_url}

See you soon!

Warmly,
Dr. Adaora
            """
            html_content = """
            <p style="margin-bottom: 16px;">I hope you're settling into your coaching journey!</p>

            <p style="margin-bottom: 16px;"><strong>As you prepare for our sessions, I encourage you to:</strong></p>
            <ul style="margin-bottom: 24px; padding-left: 20px;">
                <li>Reflect on the goals you shared in your assessment</li>
                <li>Notice any patterns or thoughts that come up during your day</li>
                <li>Jot down any questions or topics you'd like to explore</li>
            </ul>
            """
        else:  # day 7
            subject = "Your First Week Complete!"
            body = f"""
Hi {contact.first_name},

Congratulations on completing your first week as a coaching client!

Remember: transformation happens one step at a time. Be patient with yourself and celebrate small wins along the way.

If you haven't already, be sure to:
- Schedule your first session if you haven't yet
- Review any action items in your portal
- Reach out if you have questions

Your portal: {portal_url}

Here's to your growth!

Warmly,
Dr. Adaora
            """
            html_content = """
            <p style="margin-bottom: 16px;">Congratulations on completing your first week as a coaching client!</p>

            <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
                <strong>Remember:</strong> Transformation happens one step at a time. Be patient with yourself and celebrate small wins along the way.
            </div>

            <p style="margin-bottom: 16px;"><strong>If you haven't already, be sure to:</strong></p>
            <ul style="margin-bottom: 24px; padding-left: 20px;">
                <li>Schedule your first session if you haven't yet</li>
                <li>Review any action items in your portal</li>
                <li>Reach out if you have questions</li>
            </ul>
            """

        html_body = _create_html_email(
            title=subject,
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="Visit Your Portal",
            cta_url=portal_url,
            footer_text="Here's to your growth!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_action_item_reminder(
        self,
        contact,
        action_item,
        days_until: int,
    ) -> bool:
        """Send reminder for upcoming action item due date."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/action-items"

        if days_until == 0:
            due_text = "today"
        elif days_until == 1:
            due_text = "tomorrow"
        else:
            due_text = f"in {days_until} days"

        subject = f"Reminder: '{action_item.title}' is due {due_text}"

        body = f"""
Hi {contact.first_name},

Just a friendly reminder that your action item is due {due_text}:

"{action_item.title}"
{f"Description: {action_item.description}" if action_item.description else ""}

View and update your action items here:
{portal_url}

You've got this!

Best,
Dr. Adaora
        """

        html_content = f"""
        <p style="margin-bottom: 16px;">Just a friendly reminder that your action item is due <strong>{due_text}</strong>:</p>

        <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
            <p style="font-weight: bold; margin: 0 0 8px 0;">{action_item.title}</p>
            {f"<p style='margin: 0; color: #6b7280;'>{action_item.description}</p>" if action_item.description else ""}
        </div>

        <p style="margin-bottom: 16px;">View and update your action items in your portal.</p>
        """

        html_body = _create_html_email(
            title="Action Item Reminder",
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="View Action Items",
            cta_url=portal_url,
            footer_text="You've got this!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_action_item_overdue(
        self,
        contact,
        action_item,
        days_overdue: int,
    ) -> bool:
        """Send reminder for overdue action item."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/action-items"

        subject = f"Overdue: '{action_item.title}'"

        body = f"""
Hi {contact.first_name},

Your action item is now {days_overdue} day(s) overdue:

"{action_item.title}"

Life gets busy - that's okay! If this item is no longer relevant, you can skip it. Otherwise, try to complete it this week.

Update your action items here:
{portal_url}

Best,
Dr. Adaora
        """

        html_content = f"""
        <p style="margin-bottom: 16px;">Your action item is now <strong>{days_overdue} day(s) overdue</strong>:</p>

        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
            <p style="font-weight: bold; margin: 0;">{action_item.title}</p>
        </div>

        <p style="margin-bottom: 16px;">Life gets busy - that's okay! If this item is no longer relevant, you can skip it. Otherwise, try to complete it this week.</p>
        """

        html_body = _create_html_email(
            title="Action Item Overdue",
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="Update Action Items",
            cta_url=portal_url,
            footer_text="Every step counts!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_goal_reminder(
        self,
        contact,
        goal,
        days_until: int,
    ) -> bool:
        """Send reminder for goal approaching target date."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/goals"

        if days_until == 0:
            due_text = "today"
        elif days_until == 1:
            due_text = "tomorrow"
        else:
            due_text = f"in {days_until} days"

        subject = f"Goal Deadline Approaching: '{goal.title}'"

        progress = goal.progress_percent if hasattr(goal, 'progress_percent') else 0

        body = f"""
Hi {contact.first_name},

Your goal target date is {due_text}:

"{goal.title}"
Progress: {progress}%

Take a moment to:
- Review your progress so far
- Celebrate what you've accomplished
- Identify any final steps needed

View your goals: {portal_url}

Keep pushing forward!

Best,
Dr. Adaora
        """

        html_content = f"""
        <p style="margin-bottom: 16px;">Your goal target date is <strong>{due_text}</strong>:</p>

        <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <p style="font-weight: bold; margin: 0 0 8px 0;">{goal.title}</p>
            <div style="background-color: #e5e7eb; border-radius: 9999px; height: 8px; overflow: hidden;">
                <div style="background-color: #8b5cf6; height: 100%; width: {progress}%;"></div>
            </div>
            <p style="margin: 8px 0 0 0; font-size: 14px; color: #6b7280;">{progress}% complete</p>
        </div>

        <p style="margin-bottom: 16px;"><strong>Take a moment to:</strong></p>
        <ul style="margin-bottom: 24px; padding-left: 20px;">
            <li>Review your progress so far</li>
            <li>Celebrate what you've accomplished</li>
            <li>Identify any final steps needed</li>
        </ul>
        """

        html_body = _create_html_email(
            title="Goal Deadline Approaching",
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="View Your Goals",
            cta_url=portal_url,
            footer_text="Keep pushing forward!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_post_session_followup(
        self,
        contact,
        booking,
    ) -> bool:
        """Send follow-up email after coaching session."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/dashboard"
        action_items_url = f"{settings.frontend_url}/client/action-items"

        session_type = booking.booking_type.name if booking.booking_type else "Coaching Session"

        subject = f"Following Up on Your {session_type}"

        body = f"""
Hi {contact.first_name},

Thank you for our session! I hope you found it valuable.

A few things to keep in mind:
- Review any action items we discussed
- Jot down insights or reflections while they're fresh
- Reach out if you have questions before our next session

Check your action items: {action_items_url}

See you next time!

Warmly,
Dr. Adaora
        """

        html_content = """
        <p style="margin-bottom: 16px;">Thank you for our session! I hope you found it valuable.</p>

        <p style="margin-bottom: 16px;"><strong>A few things to keep in mind:</strong></p>
        <ul style="margin-bottom: 24px; padding-left: 20px;">
            <li>Review any action items we discussed</li>
            <li>Jot down insights or reflections while they're fresh</li>
            <li>Reach out if you have questions before our next session</li>
        </ul>
        """

        html_body = _create_html_email(
            title=f"Following Up on Your {session_type}",
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="View Action Items",
            cta_url=action_items_url,
            footer_text="See you next time!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_weekly_summary(
        self,
        contact,
        summary: dict,
    ) -> bool:
        """Send weekly progress summary."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/dashboard"

        subject = "Your Weekly Progress Summary"

        # Build summary text
        stats_lines = []
        if summary.get("completed_this_week", 0) > 0:
            stats_lines.append(f"- {summary['completed_this_week']} action item(s) completed")
        if summary.get("pending_action_items", 0) > 0:
            stats_lines.append(f"- {summary['pending_action_items']} action item(s) pending")
        if summary.get("overdue_items", 0) > 0:
            stats_lines.append(f"- {summary['overdue_items']} item(s) overdue")
        if summary.get("active_goals", 0) > 0:
            stats_lines.append(f"- {summary['active_goals']} active goal(s)")

        stats_text = "\n".join(stats_lines) if stats_lines else "No activity to report"

        next_session_text = ""
        if summary.get("next_session"):
            next_session_text = f"\nNext Session: {summary['next_session'].start_time.strftime('%A, %B %d at %I:%M %p')}"

        body = f"""
Hi {contact.first_name},

Here's your weekly progress summary:

{stats_text}
{next_session_text}

Keep up the great work!

Best,
Dr. Adaora

View your full dashboard: {portal_url}
        """

        # Build HTML stats
        html_stats = ""
        for line in stats_lines:
            html_stats += f"<li>{line[2:]}</li>"

        html_content = f"""
        <p style="margin-bottom: 16px;">Here's your weekly progress summary:</p>

        <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <ul style="margin: 0; padding-left: 20px;">
                {html_stats if html_stats else "<li>No activity to report</li>"}
            </ul>
        </div>

        {f"<p style='margin-bottom: 16px;'><strong>Next Session:</strong> {summary['next_session'].start_time.strftime('%A, %B %d at %I:%M %p')}</p>" if summary.get('next_session') else ""}
        """

        html_body = _create_html_email(
            title="Weekly Progress Summary",
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="View Dashboard",
            cta_url=portal_url,
            footer_text="Keep up the great work!",
        )

        return await self._send_email(contact.email, subject, body, html_body)

    async def send_monthly_summary(
        self,
        contact,
        summary: dict,
    ) -> bool:
        """Send monthly progress report."""
        settings = get_settings()
        portal_url = f"{settings.frontend_url}/client/dashboard"

        subject = "Your Monthly Coaching Report"

        body = f"""
Hi {contact.first_name},

Here's your monthly coaching report:

Sessions This Month: {summary.get('sessions_this_month', 0)}
Action Items Completed: {summary.get('action_items_completed', 0)}
Goals Completed: {summary.get('goals_completed', 0)}
Active Goals: {summary.get('active_goals', 0)}

Reflect on how far you've come and set your intentions for the month ahead!

Best,
Dr. Adaora

View your full dashboard: {portal_url}
        """

        html_content = f"""
        <p style="margin-bottom: 16px;">Here's your monthly coaching report:</p>

        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px;">
            <div style="background-color: #f0fdf4; padding: 16px; border-radius: 8px; text-align: center;">
                <p style="font-size: 24px; font-weight: bold; margin: 0; color: #22c55e;">{summary.get('sessions_this_month', 0)}</p>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">Sessions</p>
            </div>
            <div style="background-color: #eff6ff; padding: 16px; border-radius: 8px; text-align: center;">
                <p style="font-size: 24px; font-weight: bold; margin: 0; color: #3b82f6;">{summary.get('action_items_completed', 0)}</p>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">Items Completed</p>
            </div>
            <div style="background-color: #faf5ff; padding: 16px; border-radius: 8px; text-align: center;">
                <p style="font-size: 24px; font-weight: bold; margin: 0; color: #8b5cf6;">{summary.get('goals_completed', 0)}</p>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">Goals Completed</p>
            </div>
            <div style="background-color: #fefce8; padding: 16px; border-radius: 8px; text-align: center;">
                <p style="font-size: 24px; font-weight: bold; margin: 0; color: #eab308;">{summary.get('active_goals', 0)}</p>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">Active Goals</p>
            </div>
        </div>

        <p style="margin-bottom: 16px;">Reflect on how far you've come and set your intentions for the month ahead!</p>
        """

        html_body = _create_html_email(
            title="Monthly Coaching Report",
            greeting=f"Hi {contact.first_name},",
            content=html_content,
            cta_text="View Dashboard",
            cta_url=portal_url,
            footer_text="Here's to another month of growth!",
        )

        return await self._send_email(contact.email, subject, body, html_body)


# Import datetime for type hints
from datetime import datetime

# Singleton instance for easy access
email_service = EmailService()
