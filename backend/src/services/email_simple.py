"""
Simple email service placeholder to avoid import errors.
Replace with email_service.py once dependencies are installed.
"""

from typing import List, Dict, Any, Optional
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Placeholder email service."""
    
    def __init__(self):
        """Initialize email service."""
        self.enabled = False
        logger.warning("Using placeholder email service - emails will not be sent")
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Placeholder send email method."""
        logger.info(
            "email_send_placeholder",
            recipients=recipients,
            subject=subject,
            template=template_name
        )
        return True
    
    async def send_verification_email(
        self,
        email: str,
        username: str,
        verification_token: str
    ) -> bool:
        """Placeholder verification email."""
        logger.info(
            "verification_email_placeholder",
            email=email,
            username=username
        )
        return True
    
    async def send_welcome_email(
        self,
        email: str,
        username: str,
        full_name: Optional[str] = None
    ) -> bool:
        """Placeholder welcome email."""
        logger.info(
            "welcome_email_placeholder",
            email=email,
            username=username
        )
        return True
    
    async def send_password_reset_email(
        self,
        email: str,
        username: str,
        reset_token: str
    ) -> bool:
        """Placeholder password reset email."""
        logger.info(
            "password_reset_email_placeholder",
            email=email,
            username=username
        )
        return True


# Create singleton instance
email_service = EmailService()