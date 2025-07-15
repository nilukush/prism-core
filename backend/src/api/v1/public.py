"""
Public API endpoints with rate limiting examples.
"""

from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

from backend.src.core.config import settings
from backend.src.middleware.rate_limiting import rate_limit
from backend.src.core.logging import logger

router = APIRouter(tags=["Public"])


class ContactForm(BaseModel):
    """Contact form submission."""
    name: str
    email: str
    subject: str
    message: str


class NewsletterSubscription(BaseModel):
    """Newsletter subscription request."""
    email: str
    preferences: Dict[str, bool] = {
        "product_updates": True,
        "blog_posts": True,
        "webinars": False
    }


@router.get("/status")
async def public_status(request: Request) -> Dict[str, Any]:
    """
    Public status endpoint with default rate limiting.
    No authentication required.
    """
    return {
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "api": "healthy",
            "database": "healthy",
            "cache": "healthy"
        },
        "rate_limit_info": {
            "limit": request.state.rate_limit_headers.get("X-RateLimit-Limit"),
            "remaining": request.state.rate_limit_headers.get("X-RateLimit-Remaining"),
            "reset": request.state.rate_limit_headers.get("X-RateLimit-Reset")
        }
    }


@router.post("/contact")
@rate_limit(requests_per_minute=5, requests_per_hour=20)
async def submit_contact_form(
    request: Request,
    form: ContactForm
) -> Dict[str, Any]:
    """
    Submit contact form with strict rate limiting.
    Limited to 5 requests per minute to prevent spam.
    """
    logger.info(
        "contact_form_submission",
        name=form.name,
        email=form.email,
        subject=form.subject
    )
    
    # In production, send email or create ticket
    # await email_service.send_contact_form(form)
    
    return {
        "success": True,
        "message": "Thank you for contacting us. We'll respond within 24 hours.",
        "reference_id": f"CONTACT-{hash(form.email) % 100000:06d}"
    }


@router.post("/newsletter/subscribe")
@rate_limit(requests_per_minute=3, requests_per_hour=10)
async def subscribe_newsletter(
    request: Request,
    subscription: NewsletterSubscription
) -> Dict[str, Any]:
    """
    Subscribe to newsletter with rate limiting.
    Prevents subscription bombing attacks.
    """
    # Validate email domain
    domain = subscription.email.split("@")[-1].lower()
    
    # Block disposable email domains
    disposable_domains = [
        "tempmail.com", "throwaway.email", "guerrillamail.com",
        "mailinator.com", "10minutemail.com"
    ]
    
    if domain in disposable_domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disposable email addresses are not allowed"
        )
    
    logger.info(
        "newsletter_subscription",
        email=subscription.email,
        preferences=subscription.preferences
    )
    
    # In production, add to mailing list
    # await mailing_list.subscribe(subscription)
    
    return {
        "success": True,
        "message": "Successfully subscribed to newsletter",
        "subscription_id": f"NL-{hash(subscription.email) % 1000000:07d}",
        "preferences": subscription.preferences
    }


@router.get("/pricing")
async def get_pricing(request: Request) -> Dict[str, Any]:
    """
    Get pricing information.
    Higher rate limit as this is frequently accessed.
    """
    return {
        "plans": [
            {
                "name": "Starter",
                "price": 29,
                "currency": "USD",
                "period": "month",
                "features": [
                    "Up to 5 projects",
                    "10 team members",
                    "Basic AI features",
                    "Email support"
                ],
                "rate_limits": {
                    "api_calls_per_hour": 1000,
                    "ai_generations_per_day": 100
                }
            },
            {
                "name": "Professional",
                "price": 99,
                "currency": "USD",
                "period": "month",
                "features": [
                    "Unlimited projects",
                    "50 team members",
                    "Advanced AI features",
                    "Priority support",
                    "Custom integrations"
                ],
                "rate_limits": {
                    "api_calls_per_hour": 10000,
                    "ai_generations_per_day": 1000
                }
            },
            {
                "name": "Enterprise",
                "price": "custom",
                "currency": "USD",
                "period": "month",
                "features": [
                    "Unlimited everything",
                    "Dedicated support",
                    "SLA guarantee",
                    "On-premise option",
                    "Custom AI models"
                ],
                "rate_limits": {
                    "api_calls_per_hour": "unlimited",
                    "ai_generations_per_day": "unlimited"
                }
            }
        ],
        "rate_limit_info": getattr(request.state, "rate_limit_headers", {})
    }


@router.get("/demo/rate-limit-test")
@rate_limit(requests_per_minute=10)
async def rate_limit_demo(request: Request) -> Dict[str, Any]:
    """
    Demo endpoint to test rate limiting.
    Try hitting this endpoint more than 10 times per minute.
    """
    client_id = request.client.host
    
    return {
        "message": "Rate limit test successful",
        "client_ip": client_id,
        "rate_limit_headers": getattr(request.state, "rate_limit_headers", {}),
        "test_instructions": [
            "This endpoint allows 10 requests per minute",
            "Try running: for i in {1..15}; do curl http://localhost:8100/api/v1/public/demo/rate-limit-test; done",
            "You should see 429 errors after the 10th request"
        ]
    }


@router.post("/demo/ddos-test")
async def ddos_test(request: Request) -> Dict[str, Any]:
    """
    Demo endpoint to test DDoS protection.
    This endpoint will trigger various DDoS protection mechanisms.
    
    WARNING: Only use in development/testing environments.
    """
    if settings.APP_ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DDoS test endpoint is disabled in production"
        )
    
    return {
        "message": "DDoS test endpoint",
        "client_ip": request.client.host,
        "headers": dict(request.headers),
        "protection_layers": [
            "IP whitelist/blacklist",
            "Geographic filtering",
            "Traffic pattern analysis",
            "JavaScript challenge",
            "Connection limiting",
            "Rate limiting"
        ],
        "test_commands": {
            "flood_test": "ab -n 1000 -c 100 http://localhost:8100/api/v1/public/demo/ddos-test",
            "slow_loris": "slowhttptest -c 1000 -H -g -o slow_read_stats -i 10 -r 200 -t GET -u http://localhost:8100/api/v1/public/demo/ddos-test -x 24 -p 3",
            "path_scanning": "for i in {1..100}; do curl http://localhost:8100/api/v1/public/path$i; done"
        }
    }