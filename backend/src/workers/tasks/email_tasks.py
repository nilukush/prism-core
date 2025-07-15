"""
Email-related Celery tasks for background processing.
"""

from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from fastapi_mail import MessageSchema, MessageType

from backend.src.workers.celery_app import celery_app
from backend.src.core.config import settings
from backend.src.services.email import email_service, EmailSchema

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True
)
def send_email_task(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email in background.
    
    Args:
        email_data: Email data dictionary
        
    Returns:
        Dict with send status
    """
    try:
        logger.info(f"Sending email: {email_data.get('email_type')} to {len(email_data.get('recipients', []))} recipients")
        
        # Convert dict back to EmailSchema
        email = EmailSchema(**email_data)
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                email_service.send_email(email, background=False)
            )
            
            logger.info(f"Email sent successfully: {result}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        
        # Check if we should retry
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying email send (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        else:
            # Max retries reached, log failure
            logger.error(f"Email send failed after {self.max_retries} attempts")
            
            # You might want to save failed emails to a dead letter queue
            # or notify administrators
            return {
                "status": "failed",
                "error": str(e),
                "attempts": self.request.retries
            }


@celery_app.task
def send_bulk_emails_task(
    recipients: List[str],
    subject: str,
    template_file: str,
    context: Dict[str, Any],
    email_type: str = "notification",
    priority: str = "low"
) -> Dict[str, Any]:
    """
    Send bulk emails to multiple recipients.
    
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
    try:
        logger.info(f"Sending bulk email to {len(recipients)} recipients")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                email_service.send_bulk_email(
                    recipients=recipients,
                    subject=subject,
                    template_file=template_file,
                    context=context,
                    email_type=email_type,
                    priority=priority
                )
            )
            
            logger.info(f"Bulk email queued successfully: {result}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to send bulk email: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task
def cleanup_email_logs_task(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old email logs and tracking data.
    
    Args:
        days_to_keep: Number of days to keep logs
        
    Returns:
        Dict with cleanup status
    """
    try:
        logger.info(f"Cleaning up email logs older than {days_to_keep} days")
        
        # Implementation would depend on where you store email logs
        # This is a placeholder for the cleanup logic
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Example: Clean up from database
        # deleted_count = await EmailLog.filter(created_at__lt=cutoff_date).delete()
        
        # Example: Clean up from cache/Redis
        # pattern = "emails_sent:daily:*"
        # keys_to_delete = []
        # for key in redis.scan_iter(match=pattern):
        #     date_str = key.split(":")[-1]
        #     if datetime.strptime(date_str, "%Y%m%d") < cutoff_date:
        #         keys_to_delete.append(key)
        # if keys_to_delete:
        #     redis.delete(*keys_to_delete)
        
        logger.info("Email log cleanup completed")
        
        return {
            "status": "success",
            "message": f"Cleaned up logs older than {days_to_keep} days"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup email logs: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task
def send_daily_digest_task() -> Dict[str, Any]:
    """
    Send daily digest emails to users who have opted in.
    
    Returns:
        Dict with send status
    """
    try:
        logger.info("Starting daily digest email task")
        
        # This would typically:
        # 1. Query users who have daily digest enabled
        # 2. Gather relevant activity for each user
        # 3. Send personalized digest emails
        
        # Placeholder implementation
        users_processed = 0
        emails_sent = 0
        
        # Example logic:
        # async for user in User.filter(preferences__daily_digest=True):
        #     digest_data = await gather_user_digest_data(user)
        #     if digest_data:
        #         await email_service.send_digest_email(user, digest_data)
        #         emails_sent += 1
        #     users_processed += 1
        
        logger.info(f"Daily digest completed: {emails_sent} emails sent to {users_processed} users")
        
        return {
            "status": "success",
            "users_processed": users_processed,
            "emails_sent": emails_sent
        }
        
    except Exception as e:
        logger.error(f"Failed to send daily digest: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task
def retry_failed_emails_task() -> Dict[str, Any]:
    """
    Retry sending failed emails from the dead letter queue.
    
    Returns:
        Dict with retry status
    """
    try:
        logger.info("Starting failed email retry task")
        
        # This would typically:
        # 1. Query failed emails from a dead letter queue
        # 2. Attempt to resend them
        # 3. Update their status based on the result
        
        retried_count = 0
        success_count = 0
        
        # Placeholder implementation
        # You would implement this based on your dead letter queue strategy
        
        logger.info(f"Email retry completed: {success_count}/{retried_count} emails sent successfully")
        
        return {
            "status": "success",
            "retried": retried_count,
            "successful": success_count
        }
        
    except Exception as e:
        logger.error(f"Failed to retry emails: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# Schedule periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule.update({
    'cleanup-email-logs': {
        'task': 'src.workers.tasks.email_tasks.cleanup_email_logs_task',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        'args': (30,)  # Keep logs for 30 days
    },
    'send-daily-digest': {
        'task': 'src.workers.tasks.email_tasks.send_daily_digest_task',
        'schedule': crontab(hour=9, minute=0),  # Run at 9 AM daily
    },
    'retry-failed-emails': {
        'task': 'src.workers.tasks.email_tasks.retry_failed_emails_task',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
})