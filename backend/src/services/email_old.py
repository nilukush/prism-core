"""
Email service module for PRISM platform.
Handles all email operations including sending, templating, and queue management.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
from datetime import datetime
from enum import Enum

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import BaseModel, EmailStr, Field
from jinja2 import Environment, FileSystemLoader, select_autoescape
import structlog

from backend.src.core.config import settings
from backend.src.core.cache import cache
from backend.src.models.user import User
from backend.src.core.database import AsyncSession
from backend.src.utils.security import generate_token

logger = structlog.get_logger()


class EmailType(str, Enum):
    """Email types for tracking and analytics."""
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    INVITATION = "invitation"
    NOTIFICATION = "notification"
    REPORT = "report"
    ALERT = "alert"


class EmailPriority(str, Enum):
    """Email priority levels."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EmailSchema(BaseModel):
    """Email data schema."""
    recipients: List[EmailStr]
    subject: str
    body: str
    email_type: EmailType
    priority: EmailPriority = EmailPriority.NORMAL
    attachments: Optional[List[Dict[str, Any]]] = None
    headers: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EmailTemplate(BaseModel):
    """Email template configuration."""
    name: str
    subject: str
    template_file: str
    email_type: EmailType
    requires_auth: bool = True


class EmailService:
    """
    Comprehensive email service for PRISM platform.
    Handles email sending, templating, and queue management.
    """

    def __init__(self):
        """Initialize email service with configuration."""
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_USE_TLS,
            MAIL_SSL_TLS=settings.MAIL_USE_SSL,
            USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
            VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
            TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email",
        )
        
        self.fastmail = FastMail(self.config)
        
        # Initialize Jinja2 environment for email templates
        self.template_env = Environment(
            loader=FileSystemLoader(self.config.TEMPLATE_FOLDER),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Email templates configuration
        self.templates = {
            EmailType.WELCOME: EmailTemplate(
                name="welcome",
                subject=f"Welcome to {settings.APP_NAME}!",
                template_file="welcome.html",
                email_type=EmailType.WELCOME
            ),
            EmailType.PASSWORD_RESET: EmailTemplate(
                name="password_reset",
                subject=f"Reset your {settings.APP_NAME} password",
                template_file="password_reset.html",
                email_type=EmailType.PASSWORD_RESET
            ),
            EmailType.EMAIL_VERIFICATION: EmailTemplate(
                name="email_verification",
                subject=f"Verify your {settings.APP_NAME} email",
                template_file="email_verification.html",
                email_type=EmailType.EMAIL_VERIFICATION
            ),
            EmailType.INVITATION: EmailTemplate(
                name="invitation",
                subject=f"You're invited to join {settings.APP_NAME}",
                template_file="invitation.html",
                email_type=EmailType.INVITATION
            ),
            EmailType.NOTIFICATION: EmailTemplate(
                name="notification",
                subject="New notification from {settings.APP_NAME}",
                template_file="notification.html",
                email_type=EmailType.NOTIFICATION
            ),
            EmailType.REPORT: EmailTemplate(
                name="report",
                subject="{report_type} Report - {settings.APP_NAME}",
                template_file="report.html",
                email_type=EmailType.REPORT
            ),
        }

    async def send_email(
        self,
        email: EmailSchema,
        background: bool = True
    ) -> Dict[str, Any]:
        """
        Send email with optional background processing.
        
        Args:
            email: Email schema with recipients and content
            background: Whether to send in background
            
        Returns:
            Dict with send status and message ID
        """
        try:
            # Log email attempt
            logger.info(
                "sending_email",
                email_type=email.email_type,
                recipients_count=len(email.recipients),
                priority=email.priority
            )
            
            # Check rate limiting
            if not await self._check_rate_limit(email.recipients[0]):
                raise Exception("Rate limit exceeded for email sending")
            
            # Create message
            message = MessageSchema(
                subject=email.subject,
                recipients=email.recipients,
                body=email.body,
                subtype=MessageType.html,
                headers=email.headers or {},
                attachments=email.attachments or []
            )
            
            # Send email
            if background:
                # Queue for background sending
                task_id = await self._queue_email(email)
                return {
                    "status": "queued",
                    "task_id": task_id,
                    "message": "Email queued for sending"
                }
            else:
                # Send immediately
                await self.fastmail.send_message(message)
                
                # Track email sent
                await self._track_email_sent(email)
                
                return {
                    "status": "sent",
                    "message": "Email sent successfully"
                }
                
        except Exception as e:
            logger.error(
                "email_send_failed",
                error=str(e),
                email_type=email.email_type
            )
            raise

    async def send_welcome_email(
        self,
        user: User,
        verification_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send welcome email to new user."""
        template = self.templates[EmailType.WELCOME]
        
        # Generate email content
        context = {
            "user_name": user.name,
            "user_email": user.email,
            "app_name": settings.APP_NAME,
            "app_url": settings.FRONTEND_URL,
            "verification_token": verification_token,
            "verification_url": f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}" if verification_token else None,
            "support_email": settings.SUPPORT_EMAIL,
            "current_year": datetime.now().year
        }
        
        html_content = self._render_template(template.template_file, context)
        
        email = EmailSchema(
            recipients=[user.email],
            subject=template.subject,
            body=html_content,
            email_type=EmailType.WELCOME,
            priority=EmailPriority.HIGH,
            metadata={"user_id": str(user.id)}
        )
        
        return await self.send_email(email)

    async def send_password_reset_email(
        self,
        user: User,
        reset_token: str
    ) -> Dict[str, Any]:
        """Send password reset email."""
        template = self.templates[EmailType.PASSWORD_RESET]
        
        context = {
            "user_name": user.name,
            "reset_url": f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}",
            "app_name": settings.APP_NAME,
            "expiry_hours": 24,
            "support_email": settings.SUPPORT_EMAIL,
            "current_year": datetime.now().year
        }
        
        html_content = self._render_template(template.template_file, context)
        
        email = EmailSchema(
            recipients=[user.email],
            subject=template.subject,
            body=html_content,
            email_type=EmailType.PASSWORD_RESET,
            priority=EmailPriority.HIGH,
            metadata={"user_id": str(user.id)}
        )
        
        return await self.send_email(email)

    async def send_email_verification(
        self,
        user: User,
        verification_token: str
    ) -> Dict[str, Any]:
        """Send email verification."""
        template = self.templates[EmailType.EMAIL_VERIFICATION]
        
        context = {
            "user_name": user.name,
            "verification_url": f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}",
            "app_name": settings.APP_NAME,
            "expiry_hours": 48,
            "support_email": settings.SUPPORT_EMAIL,
            "current_year": datetime.now().year
        }
        
        html_content = self._render_template(template.template_file, context)
        
        email = EmailSchema(
            recipients=[user.email],
            subject=template.subject,
            body=html_content,
            email_type=EmailType.EMAIL_VERIFICATION,
            priority=EmailPriority.HIGH,
            metadata={"user_id": str(user.id)}
        )
        
        return await self.send_email(email)

    async def send_invitation_email(
        self,
        inviter: User,
        invitee_email: str,
        organization_name: str,
        invitation_token: str,
        role: str = "member"
    ) -> Dict[str, Any]:
        """Send invitation email to join organization."""
        template = self.templates[EmailType.INVITATION]
        
        context = {
            "inviter_name": inviter.name,
            "organization_name": organization_name,
            "role": role,
            "invitation_url": f"{settings.FRONTEND_URL}/auth/accept-invitation?token={invitation_token}",
            "app_name": settings.APP_NAME,
            "expiry_days": 7,
            "support_email": settings.SUPPORT_EMAIL,
            "current_year": datetime.now().year
        }
        
        html_content = self._render_template(template.template_file, context)
        
        email = EmailSchema(
            recipients=[invitee_email],
            subject=template.subject.format(inviter_name=inviter.name),
            body=html_content,
            email_type=EmailType.INVITATION,
            priority=EmailPriority.NORMAL,
            metadata={
                "inviter_id": str(inviter.id),
                "organization_name": organization_name
            }
        )
        
        return await self.send_email(email)

    async def send_notification_email(
        self,
        user: User,
        notification_title: str,
        notification_body: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send notification email."""
        template = self.templates[EmailType.NOTIFICATION]
        
        context = {
            "user_name": user.name,
            "notification_title": notification_title,
            "notification_body": notification_body,
            "action_url": action_url,
            "action_text": action_text or "View Details",
            "app_name": settings.APP_NAME,
            "app_url": settings.FRONTEND_URL,
            "support_email": settings.SUPPORT_EMAIL,
            "current_year": datetime.now().year
        }
        
        html_content = self._render_template(template.template_file, context)
        
        email = EmailSchema(
            recipients=[user.email],
            subject=f"{notification_title} - {settings.APP_NAME}",
            body=html_content,
            email_type=EmailType.NOTIFICATION,
            priority=EmailPriority.NORMAL,
            metadata={"user_id": str(user.id)}
        )
        
        return await self.send_email(email)

    async def send_bulk_email(
        self,
        recipients: List[EmailStr],
        subject: str,
        template_file: str,
        context: Dict[str, Any],
        email_type: EmailType = EmailType.NOTIFICATION,
        priority: EmailPriority = EmailPriority.LOW
    ) -> Dict[str, Any]:
        """
        Send bulk email to multiple recipients.
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            template_file: Template file name
            context: Template context
            email_type: Type of email
            priority: Email priority
            
        Returns:
            Dict with send status
        """
        # Chunk recipients to avoid overloading
        chunk_size = 50
        chunks = [recipients[i:i + chunk_size] for i in range(0, len(recipients), chunk_size)]
        
        results = []
        for chunk in chunks:
            html_content = self._render_template(template_file, context)
            
            email = EmailSchema(
                recipients=chunk,
                subject=subject,
                body=html_content,
                email_type=email_type,
                priority=priority,
                metadata={"bulk": True, "total_recipients": len(recipients)}
            )
            
            result = await self.send_email(email, background=True)
            results.append(result)
            
            # Small delay between chunks
            await asyncio.sleep(0.5)
        
        return {
            "status": "queued",
            "chunks": len(chunks),
            "total_recipients": len(recipients),
            "results": results
        }

    def _render_template(self, template_file: str, context: Dict[str, Any]) -> str:
        """Render email template with context."""
        template = self.template_env.get_template(template_file)
        return template.render(**context)

    async def _check_rate_limit(self, email: str) -> bool:
        """Check if email sending is within rate limits."""
        key = f"email_rate_limit:{email}"
        current = await cache.get(key)
        
        if current is None:
            # First email, set counter
            await cache.set(key, 1, expire=3600)  # 1 hour window
            return True
        
        if int(current) >= settings.EMAIL_RATE_LIMIT_PER_HOUR:
            return False
        
        # Increment counter
        await cache.increment(key)
        return True

    async def _queue_email(self, email: EmailSchema) -> str:
        """Queue email for background sending."""
        from src.workers.tasks.email_tasks import send_email_task
        
        task = send_email_task.delay(email.dict())
        return task.id

    async def _track_email_sent(self, email: EmailSchema) -> None:
        """Track email sent for analytics."""
        # Increment counters
        await cache.increment(f"emails_sent:{email.email_type}")
        await cache.increment(f"emails_sent:daily:{datetime.now().strftime('%Y%m%d')}")
        
        # Log to analytics if enabled
        if settings.ENABLE_ANALYTICS:
            logger.info(
                "email_sent",
                email_type=email.email_type,
                recipients_count=len(email.recipients),
                priority=email.priority,
                metadata=email.metadata
            )


# Global email service instance
email_service = EmailService()