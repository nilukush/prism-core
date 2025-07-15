"""
Email API endpoints.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.api.deps import get_current_user, get_db
from backend.src.models.user import User
from backend.src.services.email import email_service, EmailType, EmailPriority
from backend.src.core.config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter()


class SendEmailRequest(BaseModel):
    """Request model for sending email."""
    recipients: List[EmailStr]
    subject: str
    body: str
    email_type: EmailType = EmailType.NOTIFICATION
    priority: EmailPriority = EmailPriority.NORMAL


class TestEmailRequest(BaseModel):
    """Request model for testing email configuration."""
    recipient: EmailStr


class EmailResponse(BaseModel):
    """Response model for email operations."""
    status: str
    message: str
    task_id: Optional[str] = None


@router.post("/send", response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EmailResponse:
    """
    Send email to specified recipients.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # Check if user has permission to send emails
        if not current_user.is_admin and len(request.recipients) > 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non-admin users can only send emails to up to 5 recipients"
            )
        
        # Log email send attempt
        logger.info(
            "email_send_requested",
            user_id=str(current_user.id),
            recipients_count=len(request.recipients),
            email_type=request.email_type
        )
        
        # Send email
        result = await email_service.send_email(
            email={
                "recipients": request.recipients,
                "subject": request.subject,
                "body": request.body,
                "email_type": request.email_type,
                "priority": request.priority,
                "metadata": {
                    "sender_id": str(current_user.id),
                    "sender_email": current_user.email
                }
            },
            background=True
        )
        
        return EmailResponse(
            status=result["status"],
            message=result["message"],
            task_id=result.get("task_id")
        )
        
    except Exception as e:
        logger.error(
            "email_send_failed",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )


@router.post("/test", response_model=EmailResponse)
async def test_email_configuration(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EmailResponse:
    """
    Test email configuration by sending a test email.
    
    Only available to admin users.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test email configuration"
        )
    
    try:
        # Send test email
        await email_service.send_notification_email(
            user=User(
                email=request.recipient,
                name="Test User"
            ),
            notification_title="Test Email from PRISM",
            notification_body=f"""
            <p>This is a test email sent from your PRISM instance.</p>
            <p>If you received this email, your email configuration is working correctly!</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>SMTP Server: {settings.MAIL_SERVER}</li>
                <li>SMTP Port: {settings.MAIL_PORT}</li>
                <li>From Email: {settings.MAIL_FROM}</li>
                <li>TLS Enabled: {settings.MAIL_USE_TLS}</li>
            </ul>
            """
        )
        
        return EmailResponse(
            status="success",
            message="Test email sent successfully"
        )
        
    except Exception as e:
        logger.error(
            "test_email_failed",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )


@router.post("/verify/resend", response_model=EmailResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EmailResponse:
    """
    Resend email verification to current user.
    """
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    try:
        # Generate new verification token
        from src.utils.security import generate_token
        verification_token = generate_token()
        
        # Update user with new token
        current_user.email_verification_token = verification_token
        db.add(current_user)
        await db.commit()
        
        # Send verification email
        result = await email_service.send_email_verification(
            user=current_user,
            verification_token=verification_token
        )
        
        return EmailResponse(
            status=result["status"],
            message="Verification email sent"
        )
        
    except Exception as e:
        logger.error(
            "resend_verification_failed",
            error=str(e),
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_email_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of a queued email task.
    """
    try:
        from src.workers.celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None,
            "info": task.info
        }
        
    except Exception as e:
        logger.error(
            "get_email_status_failed",
            error=str(e),
            task_id=task_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get email status"
        )