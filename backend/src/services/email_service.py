"""
Enterprise-grade email service with multiple providers and templates.
Supports SMTP, SendGrid, AWS SES, and Mailgun.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import formataddr
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from enum import Enum
from datetime import datetime, timezone
import hashlib
import base64

# Handle optional dependencies gracefully
try:
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    
try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers."""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    MAILGUN = "mailgun"


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailTemplate(str, Enum):
    """Available email templates."""
    WELCOME = "welcome"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    INVITATION = "invitation"
    NOTIFICATION = "notification"
    REPORT = "report"
    ALERT = "alert"
    DIGEST = "digest"


class EmailService:
    """Enterprise email service with retry logic and monitoring."""
    
    def __init__(self):
        """Initialize email service with configured provider."""
        self.provider = EmailProvider(getattr(settings, "EMAIL_PROVIDER", "smtp"))
        self.enabled = settings.EMAIL_ENABLED
        
        # Setup template environment
        if JINJA2_AVAILABLE:
            template_path = Path(__file__).parent.parent / "templates" / "email"
            self.template_env = Environment(
                loader=FileSystemLoader(str(template_path)),
                autoescape=select_autoescape(['html', 'xml']),
                enable_async=True
            )
        else:
            logger.warning("Jinja2 not available - email templates disabled")
            self.template_env = None
        
        # Initialize provider-specific clients
        self._init_providers()
        
        # Email tracking
        self.sent_count = 0
        self.failed_count = 0
        self.last_error = None
    
    def _init_providers(self):
        """Initialize email provider clients."""
        if self.provider == EmailProvider.SENDGRID:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            except ImportError:
                logger.warning("SendGrid library not installed")
                self.sendgrid_client = None
        
        elif self.provider == EmailProvider.AWS_SES:
            try:
                import boto3
                self.ses_client = boto3.client(
                    'ses',
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
            except ImportError:
                logger.warning("Boto3 library not installed")
                self.ses_client = None
        
        elif self.provider == EmailProvider.MAILGUN:
            try:
                import requests
                self.mailgun_api_key = settings.MAILGUN_API_KEY
                self.mailgun_domain = settings.MAILGUN_DOMAIN
            except ImportError:
                logger.warning("Requests library not installed")
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send email using configured provider with retry logic.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            template_name: Name of the template to use
            context: Template context variables
            attachments: Optional list of attachments
            priority: Email priority
            headers: Optional custom headers
            
        Returns:
            bool: True if email was sent successfully
        """
        if not self.enabled:
            logger.info("email_service_disabled", recipients=recipients, subject=subject)
            return True
        
        # Validate recipients
        valid_recipients = []
        for recipient in recipients:
            try:
                validation = validate_email(recipient, check_deliverability=False)
                valid_recipients.append(validation.email)
            except EmailNotValidError as e:
                logger.warning("invalid_email_address", email=recipient, error=str(e))
        
        if not valid_recipients:
            logger.error("no_valid_recipients", original_recipients=recipients)
            return False
        
        # Add default context
        context.update({
            "app_name": settings.APP_NAME,
            "app_url": settings.FRONTEND_URL,
            "current_year": datetime.now().year,
            "support_email": settings.SUPPORT_EMAIL
        })
        
        # Render templates
        try:
            html_template = self.template_env.get_template(f"{template_name}.html")
            html_content = await html_template.render_async(**context)
            
            # Try to render text template, fall back to HTML strip
            try:
                text_template = self.template_env.get_template(f"{template_name}.txt")
                text_content = await text_template.render_async(**context)
            except:
                text_content = self._html_to_text(html_content)
        
        except Exception as e:
            logger.error("template_render_error", template=template_name, error=str(e))
            return False
        
        # Add tracking pixel for analytics
        if getattr(settings, "EMAIL_TRACKING_ENABLED", False):
            tracking_id = self._generate_tracking_id(valid_recipients[0], subject)
            tracking_url = f"{settings.BACKEND_URL}/api/v1/email/track/{tracking_id}"
            html_content = html_content.replace(
                "</body>",
                f'<img src="{tracking_url}" width="1" height="1" style="display:none;" /></body>'
            )
        
        # Send with retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if self.provider == EmailProvider.SMTP:
                    success = await self._send_smtp(
                        valid_recipients, subject, text_content, html_content,
                        attachments, priority, headers
                    )
                elif self.provider == EmailProvider.SENDGRID:
                    success = await self._send_sendgrid(
                        valid_recipients, subject, text_content, html_content,
                        attachments, priority, headers
                    )
                elif self.provider == EmailProvider.AWS_SES:
                    success = await self._send_ses(
                        valid_recipients, subject, text_content, html_content,
                        attachments, priority, headers
                    )
                elif self.provider == EmailProvider.MAILGUN:
                    success = await self._send_mailgun(
                        valid_recipients, subject, text_content, html_content,
                        attachments, priority, headers
                    )
                else:
                    logger.error("unsupported_email_provider", provider=self.provider)
                    return False
                
                if success:
                    self.sent_count += 1
                    logger.info(
                        "email_sent_successfully",
                        recipients=valid_recipients,
                        subject=subject,
                        template=template_name,
                        attempt=attempt + 1
                    )
                    return True
                
            except Exception as e:
                self.last_error = str(e)
                logger.error(
                    "email_send_error",
                    provider=self.provider,
                    recipients=valid_recipients,
                    subject=subject,
                    error=str(e),
                    attempt=attempt + 1
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.failed_count += 1
                    
                    # Queue for background retry if available
                    if hasattr(self, 'celery_app'):
                        from backend.src.workers.tasks.email_tasks import send_email_task
                        send_email_task.delay(
                            recipients=valid_recipients,
                            subject=subject,
                            template_name=template_name,
                            context=context
                        )
        
        return False
    
    async def _send_smtp(
        self,
        recipients: List[str],
        subject: str,
        text_content: str,
        html_content: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send email via SMTP."""
        message = MIMEMultipart('alternative')
        
        # Set headers
        message['Subject'] = subject
        message['From'] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_FROM_EMAIL))
        message['To'] = ", ".join(recipients)
        message['Date'] = formataddr((None, datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")))
        
        # Priority headers
        if priority == EmailPriority.HIGH:
            message['X-Priority'] = '1'
            message['Importance'] = 'high'
        elif priority == EmailPriority.URGENT:
            message['X-Priority'] = '1'
            message['Importance'] = 'high'
            message['X-MSMail-Priority'] = 'High'
        
        # Custom headers
        if headers:
            for key, value in headers.items():
                message[key] = value
        
        # Add tracking headers
        message['X-Entity-Ref-ID'] = self._generate_message_id()
        message['List-Unsubscribe'] = f"<{settings.FRONTEND_URL}/unsubscribe>"
        message['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
        
        # Add content parts
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                self._add_attachment(message, attachment)
        
        # Send email
        try:
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=settings.SMTP_TLS,
                use_tls=settings.SMTP_SSL
            ) as smtp:
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                await smtp.send_message(message)
                return True
                
        except Exception as e:
            logger.error("smtp_send_error", error=str(e), host=settings.SMTP_HOST)
            raise
    
    async def _send_sendgrid(
        self,
        recipients: List[str],
        subject: str,
        text_content: str,
        html_content: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send email via SendGrid."""
        if not self.sendgrid_client:
            raise ValueError("SendGrid client not initialized")
        
        from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
        
        message = Mail(
            from_email=Email(settings.SMTP_FROM_EMAIL, settings.SMTP_FROM_NAME),
            to_emails=[To(email) for email in recipients],
            subject=subject
        )
        
        message.content = [
            Content("text/plain", text_content),
            Content("text/html", html_content)
        ]
        
        # Add custom headers
        if headers:
            message.headers = headers
        
        # Add attachments
        if attachments:
            for att in attachments:
                attachment = Attachment()
                attachment.file_content = base64.b64encode(att['content']).decode()
                attachment.file_type = att.get('mime_type', 'application/octet-stream')
                attachment.file_name = att['filename']
                attachment.disposition = 'attachment'
                message.add_attachment(attachment)
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.sendgrid_client.send, message
            )
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error("sendgrid_send_error", error=str(e))
            raise
    
    async def send_verification_email(
        self,
        email: str,
        username: str,
        verification_token: str
    ) -> bool:
        """Send email verification email."""
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"
        
        context = {
            "username": username,
            "verification_url": verification_url,
            "expires_in_hours": 24
        }
        
        return await self.send_email(
            recipients=[email],
            subject=f"Verify your {settings.APP_NAME} account",
            template_name=EmailTemplate.EMAIL_VERIFICATION,
            context=context,
            priority=EmailPriority.HIGH
        )
    
    async def send_welcome_email(
        self,
        email: str,
        username: str,
        full_name: Optional[str] = None
    ) -> bool:
        """Send welcome email to new user."""
        context = {
            "username": username,
            "full_name": full_name or username,
            "dashboard_url": f"{settings.FRONTEND_URL}/dashboard",
            "docs_url": f"{settings.FRONTEND_URL}/docs",
            "support_url": f"{settings.FRONTEND_URL}/support"
        }
        
        return await self.send_email(
            recipients=[email],
            subject=f"Welcome to {settings.APP_NAME}!",
            template_name=EmailTemplate.WELCOME,
            context=context
        )
    
    async def send_password_reset_email(
        self,
        email: str,
        username: str,
        reset_token: str
    ) -> bool:
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
        
        context = {
            "username": username,
            "reset_url": reset_url,
            "expires_in_hours": 1,
            "ip_address": "Unknown",  # Should be passed from request
            "browser": "Unknown"  # Should be parsed from user agent
        }
        
        return await self.send_email(
            recipients=[email],
            subject=f"Reset your {settings.APP_NAME} password",
            template_name=EmailTemplate.PASSWORD_RESET,
            context=context,
            priority=EmailPriority.HIGH
        )
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text."""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace &nbsp; with space
        text = text.replace('&nbsp;', ' ')
        # Decode HTML entities
        import html
        text = html.unescape(text)
        return text.strip()
    
    def _generate_tracking_id(self, recipient: str, subject: str) -> str:
        """Generate unique tracking ID for email."""
        data = f"{recipient}:{subject}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        import uuid
        return f"<{uuid.uuid4()}@{settings.APP_NAME.lower()}.com>"
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message."""
        from email.mime.base import MIMEBase
        from email import encoders
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment['content'])
        encoders.encode_base64(part)
        
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment["filename"]}"'
        )
        
        if 'mime_type' in attachment:
            part.set_type(attachment['mime_type'])
        
        message.attach(part)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get email service statistics."""
        return {
            "provider": self.provider,
            "enabled": self.enabled,
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "last_error": self.last_error,
            "success_rate": (
                self.sent_count / (self.sent_count + self.failed_count)
                if (self.sent_count + self.failed_count) > 0
                else 0
            )
        }


# Create singleton instance
email_service = EmailService()