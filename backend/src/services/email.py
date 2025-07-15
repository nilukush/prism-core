"""
Simple email service implementation without fastapi-mail.
"""

import logging
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import asyncio
from enum import Enum
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.src.core.config import settings

logger = logging.getLogger(__name__)


class EmailType(str, Enum):
    """Email type enum."""
    NOTIFICATION = "notification"
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    INVITATION = "invitation"
    REPORT = "report"
    ALERT = "alert"
    MARKETING = "marketing"


class EmailPriority(str, Enum):
    """Email priority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailService:
    """Simple email service for sending emails."""
    
    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from_email = settings.SMTP_FROM_EMAIL
        self.smtp_from_name = settings.SMTP_FROM_NAME or "PRISM"
        self.smtp_tls = settings.SMTP_TLS
        
        # Initialize Jinja2 for templates
        self.template_env = Environment(
            loader=FileSystemLoader("backend/src/templates/email"),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email to recipients."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            msg['To'] = ", ".join(recipients)
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email in a thread to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, recipients, msg
            )
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _send_smtp_email(self, recipients: List[str], msg: MIMEMultipart):
        """Send email via SMTP."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.smtp_tls:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg, to_addrs=recipients)
    
    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        subject = f"Welcome to {self.smtp_from_name}!"
        body = f"Hi {user_name},\n\nWelcome to {self.smtp_from_name}! We're excited to have you on board.\n\nBest regards,\nThe {self.smtp_from_name} Team"
        
        try:
            template = self.template_env.get_template("welcome.html")
            html_body = template.render(user_name=user_name, app_name=self.smtp_from_name)
        except Exception:
            html_body = None
        
        return await self.send_email([user_email], subject, body, html_body)
    
    async def send_password_reset_email(
        self, user_email: str, user_name: str, reset_link: str
    ) -> bool:
        """Send password reset email."""
        subject = f"Reset your {self.smtp_from_name} password"
        body = f"Hi {user_name},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 1 hour.\n\nBest regards,\nThe {self.smtp_from_name} Team"
        
        try:
            template = self.template_env.get_template("password_reset.html")
            html_body = template.render(
                user_name=user_name,
                reset_link=reset_link,
                app_name=self.smtp_from_name
            )
        except Exception:
            html_body = None
        
        return await self.send_email([user_email], subject, body, html_body)
    
    async def send_verification_email(
        self, user_email: str, user_name: str, verification_link: str
    ) -> bool:
        """Send email verification email."""
        subject = f"Verify your {self.smtp_from_name} email"
        body = f"Hi {user_name},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nBest regards,\nThe {self.smtp_from_name} Team"
        
        try:
            template = self.template_env.get_template("verify_email.html")
            html_body = template.render(
                user_name=user_name,
                verification_link=verification_link,
                app_name=self.smtp_from_name
            )
        except Exception:
            html_body = None
        
        return await self.send_email([user_email], subject, body, html_body)


# Create singleton instance
email_service = EmailService()