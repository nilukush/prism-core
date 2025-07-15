# PRISM Enterprise Implementation Plan

## Executive Summary

This document outlines the enterprise-grade implementation plan for PRISM, focusing on security, scalability, compliance, and operational excellence. The plan follows 2024-2025 best practices and industry standards.

## Implementation Status

### ✅ Completed
1. **Email Service Enhancement** - Production-ready email service with multiple provider support
2. **Email Verification Flow** - Professional templates and secure token generation
3. **OpenTelemetry Integration** - Distributed tracing and metrics collection
4. **Health Check System** - Comprehensive health monitoring endpoints
5. **Security Middleware** - OWASP Top 10 protection implementation
6. **Enhanced Logging** - Structured logging with correlation IDs

### 🚧 In Progress
1. **OAuth2/OIDC Implementation** - Provider integration code ready, needs testing
2. **Multi-Factor Authentication** - Core implementation ready, UI integration pending
3. **Database Optimization** - Connection pooling configured, query optimization ongoing

### 📋 Pending
1. **CI/CD Pipeline** - GitHub Actions workflow design
2. **Kubernetes Deployment** - Helm charts and manifests
3. **API Rate Limiting Enhancement** - Advanced strategies implementation
4. **Comprehensive Test Suite** - Unit and integration tests

## Phase 1: Security & Authentication (Q1 2025)

### 1.1 OAuth2/OIDC Implementation

#### Current State
- Basic JWT authentication with local user management
- No SSO or external provider support
- Limited session management

#### Target State
- Full OAuth 2.0 + OpenID Connect support
- Multi-provider authentication (Google, Microsoft, GitHub, SAML)
- Enterprise SSO integration
- Passwordless authentication with FIDO2/WebAuthn

#### Implementation Steps

```python
# backend/src/core/oauth_config.py
from typing import Dict, Any
from pydantic import BaseModel

class OAuthProvider(BaseModel):
    """OAuth provider configuration."""
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str]
    
class OAuthConfig:
    """OAuth configuration manager."""
    
    PROVIDERS: Dict[str, OAuthProvider] = {
        "google": OAuthProvider(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"]
        ),
        "microsoft": OAuthProvider(
            client_id=settings.AZURE_CLIENT_ID,
            client_secret=settings.AZURE_CLIENT_SECRET,
            authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            userinfo_url="https://graph.microsoft.com/v1.0/me",
            scopes=["openid", "email", "profile", "User.Read"]
        ),
        "github": OAuthProvider(
            client_id=settings.GITHUB_CLIENT_ID,
            client_secret=settings.GITHUB_CLIENT_SECRET,
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scopes=["read:user", "user:email"]
        )
    }
```

```python
# backend/src/api/v1/oauth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import secrets
from jose import jwt

router = APIRouter(prefix="/oauth", tags=["oauth"])

@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login flow."""
    if provider not in OAuthConfig.PROVIDERS:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    config = OAuthConfig.PROVIDERS[provider]
    state = secrets.token_urlsafe(32)
    
    # Store state in Redis for CSRF protection
    await redis_client.setex(f"oauth_state:{state}", 600, provider)
    
    params = {
        "client_id": config.client_id,
        "redirect_uri": f"{settings.BACKEND_URL}/api/v1/oauth/{provider}/callback",
        "scope": " ".join(config.scopes),
        "state": state,
        "response_type": "code"
    }
    
    # Add provider-specific params
    if provider == "google":
        params["access_type"] = "offline"
        params["prompt"] = "consent"
    
    url = httpx.URL(config.authorize_url).copy_with(params=params)
    return RedirectResponse(url=str(url))

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback."""
    # Verify state
    stored_provider = await redis_client.get(f"oauth_state:{state}")
    if not stored_provider or stored_provider != provider:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for tokens
    config = OAuthConfig.PROVIDERS[provider]
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{settings.BACKEND_URL}/api/v1/oauth/{provider}/callback",
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        
        tokens = token_response.json()
        
        # Get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_response = await client.get(config.userinfo_url, headers=headers)
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_response.json()
    
    # Create or update user
    user = await UserService.get_or_create_oauth_user(
        db, provider, user_info, tokens.get("refresh_token")
    )
    
    # Create session tokens
    access_token, _ = AuthService.create_access_token(
        user_id=user.id,
        email=user.email,
        roles=[role.name for role in user.roles]
    )
    
    refresh_token, family_id, _ = AuthService.create_refresh_token(
        user_id=user.id
    )
    
    # Redirect to frontend with tokens
    frontend_url = httpx.URL(settings.FRONTEND_URL + "/auth/callback")
    frontend_url = frontend_url.copy_with(params={
        "access_token": access_token,
        "refresh_token": refresh_token
    })
    
    return RedirectResponse(url=str(frontend_url))
```

### 1.2 Multi-Factor Authentication (MFA)

```python
# backend/src/models/user_mfa.py
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import pyotp

class MFAMethod(str, enum.Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    WEBAUTHN = "webauthn"
    BACKUP_CODES = "backup_codes"

class UserMFA(Base, TimestampMixin):
    """User MFA configuration."""
    __tablename__ = "user_mfa"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    method = Column(Enum(MFAMethod), nullable=False)
    secret = Column(String, nullable=True)  # Encrypted
    phone_number = Column(String, nullable=True)  # For SMS
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # WebAuthn specific
    credential_id = Column(String, nullable=True)
    public_key = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mfa_methods")

class MFAService:
    """MFA service implementation."""
    
    @staticmethod
    async def setup_totp(db: AsyncSession, user_id: UUID) -> Dict[str, str]:
        """Setup TOTP for user."""
        secret = pyotp.random_base32()
        
        # Create MFA entry
        mfa = UserMFA(
            user_id=user_id,
            method=MFAMethod.TOTP,
            secret=encrypt(secret),  # Encrypt before storing
            is_verified=False
        )
        db.add(mfa)
        await db.commit()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="PRISM"
        )
        
        return {
            "secret": secret,
            "qr_code": generate_qr_code(provisioning_uri),
            "manual_entry_key": secret
        }
    
    @staticmethod
    async def verify_totp(
        db: AsyncSession,
        user_id: UUID,
        token: str
    ) -> bool:
        """Verify TOTP token."""
        mfa = await db.execute(
            select(UserMFA).where(
                and_(
                    UserMFA.user_id == user_id,
                    UserMFA.method == MFAMethod.TOTP
                )
            )
        )
        mfa = mfa.scalar_one_or_none()
        
        if not mfa:
            return False
        
        secret = decrypt(mfa.secret)
        totp = pyotp.TOTP(secret)
        
        # Allow 1 window for clock skew
        if totp.verify(token, valid_window=1):
            mfa.is_verified = True
            mfa.last_used_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        
        return False
```

### 1.3 Passwordless Authentication (FIDO2/WebAuthn)

```python
# backend/src/services/webauthn.py
from webauthn import generate_registration_options, verify_registration_response
from webauthn import generate_authentication_options, verify_authentication_response

class WebAuthnService:
    """WebAuthn/FIDO2 service."""
    
    @staticmethod
    async def register_begin(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        """Start WebAuthn registration."""
        user = await UserService.get_by_id(db, user_id)
        
        # Get existing credentials
        existing_credentials = await db.execute(
            select(UserMFA).where(
                and_(
                    UserMFA.user_id == user_id,
                    UserMFA.method == MFAMethod.WEBAUTHN
                )
            )
        )
        exclude_credentials = [
            {"id": cred.credential_id, "type": "public-key"}
            for cred in existing_credentials
        ]
        
        options = generate_registration_options(
            rp_id=settings.WEBAUTHN_RP_ID,
            rp_name="PRISM",
            user_id=str(user_id).encode(),
            user_name=user.username,
            user_display_name=user.full_name,
            exclude_credentials=exclude_credentials,
            authenticator_selection={
                "authenticator_attachment": "platform",
                "user_verification": "preferred"
            }
        )
        
        # Store challenge in Redis
        await redis_client.setex(
            f"webauthn_challenge:{user_id}",
            300,
            options.challenge
        )
        
        return options
    
    @staticmethod
    async def register_complete(
        db: AsyncSession,
        user_id: UUID,
        credential: Dict[str, Any]
    ) -> bool:
        """Complete WebAuthn registration."""
        # Verify challenge
        expected_challenge = await redis_client.get(f"webauthn_challenge:{user_id}")
        if not expected_challenge:
            raise HTTPException(status_code=400, detail="Challenge expired")
        
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=settings.FRONTEND_URL,
            expected_rp_id=settings.WEBAUTHN_RP_ID
        )
        
        if verification.verified:
            # Store credential
            mfa = UserMFA(
                user_id=user_id,
                method=MFAMethod.WEBAUTHN,
                credential_id=verification.credential_id,
                public_key=verification.credential_public_key,
                is_verified=True
            )
            db.add(mfa)
            await db.commit()
            
            return True
        
        return False
```

## Phase 2: Email Verification & SMTP Configuration

### 2.1 Production-Ready Email Service

```python
# backend/src/services/email_enhanced.py
from email_validator import validate_email, EmailNotValidError
import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape
import boto3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailProvider(str, Enum):
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    MAILGUN = "mailgun"

class EnhancedEmailService:
    """Production-ready email service with multiple providers."""
    
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER
        self.template_env = Environment(
            loader=FileSystemLoader("backend/src/templates/email"),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Initialize provider clients
        if self.provider == EmailProvider.SENDGRID:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        elif self.provider == EmailProvider.AWS_SES:
            self.ses_client = boto3.client(
                'ses',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> bool:
        """Send email with template and retry logic."""
        # Validate recipients
        valid_recipients = []
        for recipient in recipients:
            try:
                validation = validate_email(recipient)
                valid_recipients.append(validation.email)
            except EmailNotValidError:
                logger.warning(f"Invalid email: {recipient}")
        
        if not valid_recipients:
            return False
        
        # Render template
        template = self.template_env.get_template(f"{template_name}.html")
        html_content = template.render(**context)
        
        # Extract text content from HTML
        text_content = html_to_text(html_content)
        
        # Send based on provider
        for attempt in range(3):  # Retry logic
            try:
                if self.provider == EmailProvider.SMTP:
                    return await self._send_smtp(
                        valid_recipients, subject, text_content, html_content
                    )
                elif self.provider == EmailProvider.SENDGRID:
                    return await self._send_sendgrid(
                        valid_recipients, subject, text_content, html_content
                    )
                elif self.provider == EmailProvider.AWS_SES:
                    return await self._send_ses(
                        valid_recipients, subject, text_content, html_content
                    )
                
            except Exception as e:
                logger.error(f"Email send attempt {attempt + 1} failed: {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Queue for retry via Celery
                    send_email_task.delay(
                        recipients=valid_recipients,
                        subject=subject,
                        template_name=template_name,
                        context=context
                    )
                    return False
        
        return False
    
    async def _send_smtp(
        self,
        recipients: List[str],
        subject: str,
        text_content: str,
        html_content: str
    ) -> bool:
        """Send via SMTP with connection pooling."""
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message['To'] = ", ".join(recipients)
        
        # Add tracking headers
        message['X-Entity-Ref-ID'] = str(uuid4())
        message['List-Unsubscribe'] = f"<{settings.FRONTEND_URL}/unsubscribe>"
        
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        message.attach(text_part)
        message.attach(html_part)
        
        # Use connection pool
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_TLS
        ) as smtp:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            await smtp.send_message(message)
        
        return True
```

### 2.2 Email Verification Flow

```python
# backend/src/api/v1/auth_enhanced.py
@router.post("/register")
async def register_enhanced(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks
):
    """Enhanced registration with email verification."""
    # Check rate limiting by IP
    client_ip = request.client.host
    rate_limit_key = f"register:{client_ip}"
    
    attempts = await redis_client.incr(rate_limit_key)
    if attempts == 1:
        await redis_client.expire(rate_limit_key, 3600)  # 1 hour window
    
    if attempts > 5:
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again later."
        )
    
    # Validate email domain for enterprise
    email_domain = user_data.email.split('@')[1]
    if settings.RESTRICT_EMAIL_DOMAINS:
        allowed_domains = settings.ALLOWED_EMAIL_DOMAINS
        if email_domain not in allowed_domains:
            raise HTTPException(
                status_code=400,
                detail=f"Email domain {email_domain} is not allowed"
            )
    
    # Check for disposable email
    if await is_disposable_email(user_data.email):
        raise HTTPException(
            status_code=400,
            detail="Disposable email addresses are not allowed"
        )
    
    # Create user
    user = await UserService.create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        status=UserStatus.PENDING
    )
    
    # Generate verification token
    verification_token = AuthService.create_email_verification_token(
        user_id=user.id,
        email=user.email
    )
    
    # Send verification email
    verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"
    
    background_tasks.add_task(
        email_service.send_email,
        recipients=[user.email],
        subject="Verify your PRISM account",
        template_name="email_verification",
        context={
            "user_name": user.full_name or user.username,
            "verification_url": verification_url,
            "expires_in": "24 hours"
        }
    )
    
    # Log registration event
    await audit_log.log_event(
        event_type="user.registered",
        user_id=user.id,
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
        metadata={
            "email": user.email,
            "username": user.username
        }
    )
    
    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user_id": str(user.id)
    }

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify email with token."""
    user = await AuthService.verify_email_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    
    # Send welcome email
    await email_service.send_email(
        recipients=[user.email],
        subject="Welcome to PRISM!",
        template_name="welcome",
        context={
            "user_name": user.full_name or user.username,
            "dashboard_url": f"{settings.FRONTEND_URL}/dashboard"
        }
    )
    
    # Create initial workspace
    await WorkspaceService.create_default_workspace(db, user.id)
    
    return {"message": "Email verified successfully"}
```

## Phase 3: Monitoring & Observability

### 3.1 OpenTelemetry Implementation

```python
# backend/src/core/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_telemetry(app: FastAPI):
    """Setup OpenTelemetry instrumentation."""
    if not settings.OTEL_ENABLED:
        return
    
    # Setup tracing
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({
                "service.name": settings.OTEL_SERVICE_NAME,
                "service.version": settings.APP_VERSION,
                "deployment.environment": settings.APP_ENV
            })
        )
    )
    
    tracer_provider = trace.get_tracer_provider()
    
    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=True  # Use False in production with TLS
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Setup metrics
    metric_reader = PeriodicExportingMetricReader(
        exporter=OTLPMetricExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT
        ),
        export_interval_millis=60000  # Export every minute
    )
    
    metrics.set_meter_provider(
        MeterProvider(
            resource=Resource.create({
                "service.name": settings.OTEL_SERVICE_NAME
            }),
            metric_readers=[metric_reader]
        )
    )
    
    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        service_name=f"{settings.OTEL_SERVICE_NAME}-db"
    )
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    
    # Custom instrumentation
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    # Create custom metrics
    request_counter = meter.create_counter(
        name="prism_requests_total",
        description="Total number of requests",
        unit="1"
    )
    
    request_duration = meter.create_histogram(
        name="prism_request_duration_seconds",
        description="Request duration in seconds",
        unit="s"
    )
    
    active_users = meter.create_up_down_counter(
        name="prism_active_users",
        description="Number of active users",
        unit="1"
    )
    
    return tracer, meter
```

### 3.2 Structured Logging

```python
# backend/src/core/logging_enhanced.py
import structlog
from pythonjsonlogger import jsonlogger
import logging.config

def setup_structured_logging():
    """Setup structured logging with correlation IDs."""
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure Python logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": settings.LOG_FILE_PATH,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"]
        }
    }
    
    logging.config.dictConfig(logging_config)

# Middleware for request correlation
class CorrelationIdMiddleware:
    """Add correlation ID to all requests."""
    
    async def __call__(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        
        with structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            user_id=getattr(request.state, "user_id", None),
            path=request.url.path,
            method=request.method
        ):
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
```

### 3.3 Health Checks & Readiness

```python
# backend/src/api/v1/health_enhanced.py
from typing import Dict, Any
import psutil
import aioredis

class HealthCheckService:
    """Comprehensive health check service."""
    
    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database connectivity and performance."""
        start_time = time.time()
        try:
            async with get_db() as db:
                result = await db.execute(text("SELECT 1"))
                row = result.scalar()
                
                # Check connection pool
                pool_status = db.get_bind().pool.status()
                
                return {
                    "status": "healthy",
                    "latency_ms": (time.time() - start_time) * 1000,
                    "pool_size": pool_status.size,
                    "pool_checked_out": pool_status.checked_out,
                    "pool_overflow": pool_status.overflow
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        start_time = time.time()
        try:
            await redis_client.ping()
            info = await redis_client.info()
            
            return {
                "status": "healthy",
                "latency_ms": (time.time() - start_time) * 1000,
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    @staticmethod
    async def check_external_services() -> Dict[str, Any]:
        """Check external service connectivity."""
        services = {}
        
        # Check OpenAI
        if settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        timeout=5.0
                    )
                services["openai"] = {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "status_code": response.status_code
                }
            except Exception as e:
                services["openai"] = {"status": "unhealthy", "error": str(e)}
        
        return services

@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user)
):
    """Detailed health check for monitoring."""
    if "admin" not in [role.name for role in current_user.roles]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    checks = await asyncio.gather(
        HealthCheckService.check_database(),
        HealthCheckService.check_redis(),
        HealthCheckService.check_external_services(),
        return_exceptions=True
    )
    
    # System metrics
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "load_average": os.getloadavg()
    }
    
    return {
        "status": "healthy" if all(
            check.get("status") == "healthy"
            for check in checks if isinstance(check, dict)
        ) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "checks": {
            "database": checks[0] if not isinstance(checks[0], Exception) else {"status": "error", "error": str(checks[0])},
            "redis": checks[1] if not isinstance(checks[1], Exception) else {"status": "error", "error": str(checks[1])},
            "external_services": checks[2] if not isinstance(checks[2], Exception) else {"status": "error", "error": str(checks[2])}
        },
        "system": system_metrics
    }
```

## Phase 4: Security Hardening

### 4.1 OWASP Top 10 Protection

```python
# backend/src/middleware/security.py
from starlette.middleware.base import BaseHTTPMiddleware
import bleach
from sqlalchemy import event

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com https://api.anthropic.com"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        
        return response

class SQLInjectionProtection:
    """SQL injection protection."""
    
    @staticmethod
    def setup_protection(engine):
        """Setup SQL injection protection."""
        
        @event.listens_for(engine, "before_execute")
        def receive_before_execute(conn, clauseelement, multiparams, params):
            # Log all SQL queries in development
            if settings.APP_ENV == "development":
                logger.debug(
                    "sql_query",
                    query=str(clauseelement),
                    params=params
                )
            
            # Validate query patterns
            query_str = str(clauseelement).lower()
            dangerous_patterns = [
                "exec(",
                "execute(",
                "eval(",
                "__import__",
                "subprocess",
                "os.system"
            ]
            
            for pattern in dangerous_patterns:
                if pattern in query_str:
                    logger.error(
                        "dangerous_sql_pattern_detected",
                        pattern=pattern,
                        query=query_str
                    )
                    raise ValueError(f"Dangerous SQL pattern detected: {pattern}")

class InputSanitization:
    """Input sanitization utilities."""
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitize HTML content."""
        allowed_tags = [
            'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre'
        ]
        allowed_attributes = {
            'a': ['href', 'title', 'target'],
            'span': ['class'],
            'div': ['class']
        }
        
        return bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    @staticmethod
    def validate_file_upload(file: UploadFile) -> bool:
        """Validate file uploads."""
        # Check file size
        if file.size > settings.MAX_UPLOAD_SIZE:
            raise ValueError(f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes")
        
        # Check file extension
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.md', '.csv', '.xlsx'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise ValueError(f"File type {file_ext} not allowed")
        
        # Check MIME type
        mime_type = magic.from_buffer(file.file.read(1024), mime=True)
        file.file.seek(0)  # Reset file pointer
        
        allowed_mimes = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/markdown',
            'text/csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        if mime_type not in allowed_mimes:
            raise ValueError(f"MIME type {mime_type} not allowed")
        
        return True
```

### 4.2 Rate Limiting & DDoS Protection

```python
# backend/src/middleware/rate_limit_enhanced.py
from typing import Dict, Optional
import hashlib

class EnhancedRateLimiter:
    """Enhanced rate limiting with multiple strategies."""
    
    def __init__(self):
        self.strategies = {
            "fixed_window": self._fixed_window_check,
            "sliding_window": self._sliding_window_check,
            "token_bucket": self._token_bucket_check,
            "adaptive": self._adaptive_check
        }
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        strategy: str = "sliding_window"
    ) -> tuple[bool, Optional[int]]:
        """Check if request is within rate limit."""
        if strategy not in self.strategies:
            strategy = "sliding_window"
        
        return await self.strategies[strategy](key, limit, window)
    
    async def _sliding_window_check(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Optional[int]]:
        """Sliding window rate limiting."""
        now = time.time()
        window_start = now - window
        
        # Remove old entries
        await redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count requests in window
        request_count = await redis_client.zcard(key)
        
        if request_count >= limit:
            # Get oldest request time
            oldest = await redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window - now) + 1
                return False, retry_after
            return False, window
        
        # Add current request
        await redis_client.zadd(key, {str(uuid4()): now})
        await redis_client.expire(key, window + 1)
        
        return True, None
    
    async def _token_bucket_check(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Optional[int]]:
        """Token bucket rate limiting."""
        bucket_key = f"bucket:{key}"
        last_refill_key = f"refill:{key}"
        
        # Get current tokens and last refill time
        tokens = await redis_client.get(bucket_key)
        last_refill = await redis_client.get(last_refill_key)
        
        now = time.time()
        
        if tokens is None:
            # Initialize bucket
            await redis_client.set(bucket_key, limit - 1)
            await redis_client.set(last_refill_key, now)
            await redis_client.expire(bucket_key, window)
            await redis_client.expire(last_refill_key, window)
            return True, None
        
        tokens = int(tokens)
        last_refill = float(last_refill)
        
        # Calculate tokens to add
        time_passed = now - last_refill
        tokens_to_add = int(time_passed * (limit / window))
        
        # Update tokens
        new_tokens = min(tokens + tokens_to_add, limit)
        
        if new_tokens > 0:
            await redis_client.set(bucket_key, new_tokens - 1)
            await redis_client.set(last_refill_key, now)
            return True, None
        else:
            # Calculate when next token will be available
            retry_after = int((1 / (limit / window)) - (now - last_refill)) + 1
            return False, retry_after

class RateLimitMiddleware:
    """Enhanced rate limiting middleware."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.limiter = EnhancedRateLimiter()
        
        # Define rate limit rules
        self.rules = {
            "/api/v1/auth/login": {"limit": 5, "window": 300, "strategy": "sliding_window"},
            "/api/v1/auth/register": {"limit": 3, "window": 3600, "strategy": "fixed_window"},
            "/api/v1/ai/generate": {"limit": 10, "window": 60, "strategy": "token_bucket"},
            "default": {"limit": 100, "window": 60, "strategy": "sliding_window"}
        }
    
    async def __call__(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get rate limit key
        client_ip = request.client.host
        user_id = getattr(request.state, "user_id", None)
        
        # Use user ID if authenticated, otherwise IP
        if user_id:
            rate_limit_key = f"rate_limit:user:{user_id}"
        else:
            # Hash IP for privacy
            ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
            rate_limit_key = f"rate_limit:ip:{ip_hash}"
        
        # Get rule for endpoint
        path = request.url.path
        rule = self.rules.get(path, self.rules["default"])
        
        # Check rate limit
        allowed, retry_after = await self.limiter.check_rate_limit(
            rate_limit_key,
            rule["limit"],
            rule["window"],
            rule["strategy"]
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule["limit"]),
                    "X-RateLimit-Window": str(rule["window"]),
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rule["limit"])
        response.headers["X-RateLimit-Window"] = str(rule["window"])
        
        return response
```

## Phase 5: CI/CD Pipeline

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Security scanning
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/python
            p/typescript
            p/react
            p/nextjs
      
      - name: OWASP Dependency Check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: 'PRISM'
          path: '.'
          format: 'ALL'
  
  # Backend tests
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: prism_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-xdist
      
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost:5432/prism_test
          REDIS_URL: redis://localhost:6379/0
          APP_ENV: testing
        run: |
          cd backend
          pytest -v --cov=src --cov-report=xml --cov-report=html -n auto
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml
          flags: backend
  
  # Frontend tests
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Type check
        run: |
          cd frontend
          npm run type-check
      
      - name: Lint
        run: |
          cd frontend
          npm run lint
      
      - name: Run tests
        run: |
          cd frontend
          npm run test:ci
      
      - name: Build
        run: |
          cd frontend
          npm run build
  
  # Build and push Docker images
  build-and-push:
    needs: [security-scan, backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
    
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
      
      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-backend
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-frontend
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
  
  # Deploy to staging
  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v4
        with:
          namespace: prism-staging
          manifests: |
            k8s/overlays/staging/
          images: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:develop-backend
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:develop-frontend
```

### 5.2 Kubernetes Deployment

```yaml
# k8s/base/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prism-backend
  labels:
    app: prism
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prism
      component: backend
  template:
    metadata:
      labels:
        app: prism
        component: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: prism-backend
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: backend
        image: ghcr.io/yourusername/prism:latest-backend
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: prism-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: prism-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: prism-secrets
              key: secret-key
        - name: OTEL_ENABLED
          value: "true"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://opentelemetry-collector:4317"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/.cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: prism-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prism-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

## Phase 6: Database Optimization

### 6.1 Connection Pooling & Query Optimization

```python
# backend/src/core/database_enhanced.py
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from sqlalchemy import event
import time

class DatabaseManager:
    """Enhanced database manager with connection pooling."""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Setup database engine with optimal pooling."""
        # Determine pool class based on environment
        if settings.APP_ENV == "testing":
            pool_class = StaticPool
            pool_kwargs = {"connect_args": {"check_same_thread": False}}
        else:
            pool_class = QueuePool
            pool_kwargs = {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
                "pool_recycle": 3600,  # Recycle connections after 1 hour
                "pool_pre_ping": True,  # Verify connections before use
            }
        
        # Create async engine
        self.async_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_class=pool_class,
            **pool_kwargs
        )
        
        # Setup event listeners
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Setup performance monitoring listeners."""
        
        @event.listens_for(self.async_engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            if settings.APP_ENV == "development":
                logger.debug("executing_query", query=statement[:100])
        
        @event.listens_for(self.async_engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            
            # Log slow queries
            if total > 1.0:  # Queries taking more than 1 second
                logger.warning(
                    "slow_query_detected",
                    duration_seconds=total,
                    query=statement[:200],
                    parameters=str(parameters)[:100]
                )
            
            # Collect metrics
            if hasattr(metrics, 'query_duration'):
                metrics.query_duration.record(
                    total,
                    attributes={
                        "query_type": statement.split()[0].upper(),
                        "table": self._extract_table_name(statement)
                    }
                )
    
    @staticmethod
    def _extract_table_name(query: str) -> str:
        """Extract table name from query."""
        query_lower = query.lower()
        for keyword in ['from', 'into', 'update']:
            if keyword in query_lower:
                parts = query_lower.split(keyword)
                if len(parts) > 1:
                    table_part = parts[1].strip().split()[0]
                    return table_part.strip('"').strip("'")
        return "unknown"

# Query optimization utilities
class QueryOptimizer:
    """Query optimization utilities."""
    
    @staticmethod
    async def explain_query(db: AsyncSession, query):
        """Get query execution plan."""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        result = await db.execute(text(explain_query))
        return result.scalar()
    
    @staticmethod
    async def analyze_tables(db: AsyncSession, tables: List[str]):
        """Run ANALYZE on tables for query planner."""
        for table in tables:
            await db.execute(text(f"ANALYZE {table}"))
        await db.commit()
    
    @staticmethod
    async def create_indexes(db: AsyncSession):
        """Create optimal indexes based on usage patterns."""
        indexes = [
            # User queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email) WHERE is_deleted = false",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users(status) WHERE is_deleted = false",
            
            # Story queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stories_project_status ON stories(project_id, status) WHERE is_deleted = false",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stories_assigned_to ON stories(assigned_to_id) WHERE assigned_to_id IS NOT NULL AND is_deleted = false",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stories_created_at ON stories(created_at DESC) WHERE is_deleted = false",
            
            # Full-text search
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stories_search ON stories USING gin(to_tsvector('english', title || ' ' || description))",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_search ON documents USING gin(to_tsvector('english', title || ' ' || content))",
            
            # Analytics queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_user_timestamp ON analytics_events(user_id, timestamp DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_type_timestamp ON analytics_events(event_type, timestamp DESC)"
        ]
        
        for index_sql in indexes:
            try:
                await db.execute(text(index_sql))
                logger.info("created_index", index=index_sql.split("INDEX")[1].split("ON")[0].strip())
            except Exception as e:
                logger.error("failed_to_create_index", error=str(e), index=index_sql)
        
        await db.commit()
```

### 6.2 Caching Strategy

```python
# backend/src/core/cache_enhanced.py
import pickle
import hashlib
from typing import Any, Optional, Callable, Union
from functools import wraps

class CacheManager:
    """Enhanced cache manager with multiple strategies."""
    
    def __init__(self):
        self.redis = redis_client
        self.local_cache = {}  # In-memory cache for hot data
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
    
    async def get(
        self,
        key: str,
        default: Any = None,
        deserializer: Callable = None
    ) -> Any:
        """Get value from cache with fallback."""
        # Check local cache first
        if key in self.local_cache:
            self.cache_stats["hits"] += 1
            return self.local_cache[key]
        
        try:
            # Check Redis
            value = await self.redis.get(key)
            if value is not None:
                self.cache_stats["hits"] += 1
                
                # Deserialize
                if deserializer:
                    value = deserializer(value)
                else:
                    value = pickle.loads(value)
                
                # Store in local cache if frequently accessed
                if await self._is_hot_key(key):
                    self.local_cache[key] = value
                
                return value
            else:
                self.cache_stats["misses"] += 1
                return default
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error("cache_get_error", key=key, error=str(e))
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serializer: Callable = None
    ) -> bool:
        """Set value in cache."""
        try:
            # Serialize value
            if serializer:
                serialized = serializer(value)
            else:
                serialized = pickle.dumps(value)
            
            # Set in Redis
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            
            # Update local cache for hot keys
            if await self._is_hot_key(key):
                self.local_cache[key] = value
            
            return True
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error("cache_set_error", key=key, error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        deleted = 0
        
        # Clear from local cache
        for key in list(self.local_cache.keys()):
            if self._match_pattern(key, pattern):
                del self.local_cache[key]
                deleted += 1
        
        # Clear from Redis
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            if keys:
                deleted += await self.redis.delete(*keys)
            
            if cursor == 0:
                break
        
        return deleted
    
    async def _is_hot_key(self, key: str) -> bool:
        """Check if key is frequently accessed."""
        access_count = await self.redis.incr(f"access_count:{key}")
        
        # Reset counter daily
        if access_count == 1:
            await self.redis.expire(f"access_count:{key}", 86400)
        
        return access_count > 10  # Hot if accessed more than 10 times
    
    def cache_result(
        self,
        ttl: int = 300,
        key_prefix: str = "",
        key_func: Optional[Callable] = None
    ):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    key_parts = [key_prefix or func.__name__]
                    
                    # Add args to key
                    for arg in args:
                        if hasattr(arg, 'id'):
                            key_parts.append(str(arg.id))
                        elif isinstance(arg, (str, int, float, bool)):
                            key_parts.append(str(arg))
                    
                    # Add kwargs to key
                    for k, v in sorted(kwargs.items()):
                        if isinstance(v, (str, int, float, bool)):
                            key_parts.append(f"{k}:{v}")
                    
                    cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, ttl=ttl)
                
                return result
            
            return wrapper
        return decorator

# Global cache instance
cache_manager = CacheManager()

# Usage example
@cache_manager.cache_result(ttl=3600, key_prefix="user")
async def get_user_with_roles(db: AsyncSession, user_id: UUID):
    """Get user with roles (cached)."""
    query = select(User).options(
        selectinload(User.roles),
        selectinload(User.organizations)
    ).where(User.id == user_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

## Phase 7: Testing Strategy

### 7.1 Comprehensive Test Suite

```python
# backend/tests/test_auth_comprehensive.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import time

class TestAuthenticationFlow:
    """Comprehensive authentication tests."""
    
    @pytest.mark.asyncio
    async def test_complete_registration_flow(
        self,
        client: AsyncClient,
        db_session,
        redis_client
    ):
        """Test complete registration flow including email verification."""
        # Register user
        registration_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        with patch("backend.src.services.email.EmailService.send_email") as mock_email:
            mock_email.return_value = True
            
            response = await client.post(
                "/api/v1/auth/register",
                json=registration_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            
            # Verify email was called
            assert mock_email.called
            call_args = mock_email.call_args[1]
            assert call_args["recipients"] == ["test@example.com"]
            assert "verification" in call_args["template_name"]
        
        # Extract verification token from email context
        context = mock_email.call_args[1]["context"]
        verification_url = context["verification_url"]
        token = verification_url.split("token=")[1]
        
        # Verify email
        response = await client.post(
            f"/api/v1/auth/verify-email?token={token}"
        )
        assert response.status_code == 200
        
        # Try to login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_oauth_flow(self, client: AsyncClient):
        """Test OAuth login flow."""
        # Initiate OAuth
        response = await client.get("/api/v1/oauth/google/login")
        assert response.status_code == 307  # Redirect
        
        location = response.headers["location"]
        assert "accounts.google.com" in location
        assert "state=" in location
        
        # Extract state
        state = location.split("state=")[1].split("&")[0]
        
        # Mock OAuth callback
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "access_token": "google_access_token",
                    "refresh_token": "google_refresh_token"
                }
            )
            
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_get.return_value = MagicMock(
                    status_code=200,
                    json=lambda: {
                        "id": "google123",
                        "email": "user@gmail.com",
                        "name": "Google User"
                    }
                )
                
                response = await client.get(
                    f"/api/v1/oauth/google/callback?code=test_code&state={state}"
                )
                
                assert response.status_code == 307
                assert "access_token=" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_mfa_setup_and_login(
        self,
        client: AsyncClient,
        authenticated_user
    ):
        """Test MFA setup and login flow."""
        headers = {"Authorization": f"Bearer {authenticated_user.token}"}
        
        # Setup TOTP
        response = await client.post(
            "/api/v1/auth/mfa/totp/setup",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data
        
        secret = data["secret"]
        
        # Verify TOTP with valid code
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        response = await client.post(
            "/api/v1/auth/mfa/totp/verify",
            json={"code": code},
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Logout
        await client.post("/api/v1/auth/logout", headers=headers)
        
        # Login with MFA
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": authenticated_user.email,
                "password": authenticated_user.password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "mfa_required" in data
        assert "session_token" in data
        
        # Complete MFA
        code = totp.now()
        response = await client.post(
            "/api/v1/auth/mfa/complete",
            json={
                "session_token": data["session_token"],
                "code": code
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """Test rate limiting on sensitive endpoints."""
        # Try multiple login attempts
        for i in range(6):
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "wrong_password"
                }
            )
            
            if i < 5:
                assert response.status_code == 401
            else:
                # Should be rate limited
                assert response.status_code == 429
                assert "Retry-After" in response.headers
    
    @pytest.mark.asyncio
    async def test_token_rotation(
        self,
        client: AsyncClient,
        authenticated_user
    ):
        """Test refresh token rotation."""
        # Get initial tokens
        refresh_token = authenticated_user.refresh_token
        
        # Wait a bit
        time.sleep(1)
        
        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        new_access_token = data["access_token"]
        new_refresh_token = data["refresh_token"]
        
        # Verify new tokens are different
        assert new_refresh_token != refresh_token
        
        # Try to use old refresh token (should fail)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 401
        
        # Verify entire token family is revoked
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh_token}
        )
        
        assert response.status_code == 401
```

### 7.2 Performance Testing

```python
# backend/tests/performance/test_load.py
from locust import HttpUser, task, between
import random
import string

class PRISMUser(HttpUser):
    """Load test user for PRISM API."""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and setup."""
        # Register user
        username = ''.join(random.choices(string.ascii_lowercase, k=10))
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "username": username,
                "email": f"{username}@loadtest.com",
                "password": "LoadTest123!",
                "full_name": "Load Test User"
            }
        )
        
        if response.status_code == 200:
            # Login
            response = self.client.post(
                "/api/v1/auth/login",
                data={
                    "username": f"{username}@loadtest.com",
                    "password": "LoadTest123!"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_projects(self):
        """List user projects."""
        self.client.get(
            "/api/v1/projects",
            headers=self.headers
        )
    
    @task(2)
    def create_story(self):
        """Create a new story."""
        self.client.post(
            "/api/v1/stories",
            json={
                "title": f"Story {random.randint(1, 1000)}",
                "description": "Load test story",
                "project_id": "test-project-id"
            },
            headers=self.headers
        )
    
    @task(1)
    def generate_ai_content(self):
        """Generate AI content."""
        self.client.post(
            "/api/v1/ai/generate",
            json={
                "prompt": "Generate a user story for a login feature",
                "type": "story"
            },
            headers=self.headers
        )
    
    @task(4)
    def search_stories(self):
        """Search stories."""
        query = random.choice(["login", "user", "feature", "bug", "api"])
        self.client.get(
            f"/api/v1/stories/search?q={query}",
            headers=self.headers
        )
```

## Implementation Timeline

### Month 1 (January 2025)
- Week 1-2: OAuth2/OIDC implementation
- Week 3: MFA implementation (TOTP, SMS)
- Week 4: Passwordless authentication (WebAuthn)

### Month 2 (February 2025)
- Week 1: Email service enhancement
- Week 2: Monitoring setup (OpenTelemetry, Prometheus)
- Week 3: Security hardening (OWASP protections)
- Week 4: Enhanced rate limiting

### Month 3 (March 2025)
- Week 1-2: CI/CD pipeline setup
- Week 3: Kubernetes deployment
- Week 4: Database optimization

### Month 4 (April 2025)
- Week 1-2: Comprehensive testing
- Week 3: Performance optimization
- Week 4: Documentation and training

## Success Metrics

1. **Security**
   - 0 critical vulnerabilities in security scans
   - 100% of users with MFA enabled
   - <0.1% authentication failures due to bugs

2. **Performance**
   - <100ms average API response time
   - >99.9% uptime
   - Support for 10,000 concurrent users

3. **Compliance**
   - SOC2 Type II certification
   - GDPR compliance verified
   - PCI DSS 4.0 compliance for payment processing

4. **Developer Experience**
   - <5 minute build and deploy time
   - >80% code coverage
   - <1 hour mean time to recovery (MTTR)

## Conclusion

This enterprise implementation plan provides a comprehensive roadmap for transforming PRISM into a production-ready, enterprise-grade platform. The focus on security, scalability, and compliance ensures the platform meets the highest standards for enterprise deployment.