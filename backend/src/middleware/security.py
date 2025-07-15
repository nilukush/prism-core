"""
Security middleware for OWASP Top 10 protection.
Implements security headers and input validation.
"""

from typing import List, Optional, Dict, Any
import re
from urllib.parse import urlparse

# Handle optional bleach dependency
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import hashlib
import secrets
import os

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    Implements OWASP security best practices.
    """
    
    def __init__(
        self,
        app,
        content_security_policy: Optional[str] = None,
        strict_transport_security: Optional[str] = None,
        x_frame_options: str = "DENY",
        x_content_type_options: str = "nosniff",
        x_xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[str] = None,
        report_uri: Optional[str] = None,
        nonce_enabled: bool = True
    ):
        super().__init__(app)
        
        # Default CSP if not provided
        if content_security_policy is None:
            content_security_policy = self._get_default_csp()
        
        # Default HSTS
        if strict_transport_security is None:
            strict_transport_security = "max-age=31536000; includeSubDomains; preload"
        
        # Default Permissions Policy
        if permissions_policy is None:
            permissions_policy = (
                "geolocation=(), microphone=(), camera=(), payment=(), "
                "usb=(), magnetometer=(), accelerometer=(), gyroscope=()"
            )
        
        self.security_headers = {
            "X-Content-Type-Options": x_content_type_options,
            "X-Frame-Options": x_frame_options,
            "X-XSS-Protection": x_xss_protection,
            "Referrer-Policy": referrer_policy,
            "Permissions-Policy": permissions_policy
        }
        
        # Only add HSTS in production
        if settings.is_production:
            self.security_headers["Strict-Transport-Security"] = strict_transport_security
        
        self.csp_template = content_security_policy
        self.report_uri = report_uri
        self.nonce_enabled = nonce_enabled
    
    def _get_default_csp(self) -> str:
        """Get default Content Security Policy."""
        csp_directives = {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.googletagmanager.com",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com data:",
            "img-src": "'self' data: https: blob:",
            "connect-src": "'self' https://api.openai.com https://api.anthropic.com wss://localhost:* ws://localhost:*",
            "media-src": "'self'",
            "object-src": "'none'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "upgrade-insecure-requests": ""
        }
        
        # Add WebSocket support in development
        if settings.is_development:
            csp_directives["connect-src"] += " ws://localhost:* wss://localhost:*"
        
        # Build CSP string
        csp_parts = []
        for directive, value in csp_directives.items():
            if value:
                csp_parts.append(f"{directive} {value}")
            else:
                csp_parts.append(directive)
        
        return "; ".join(csp_parts)
    
    async def dispatch(self, request: Request, call_next):
        # Generate nonce for this request if enabled
        if self.nonce_enabled:
            nonce = secrets.token_urlsafe(16)
            request.state.csp_nonce = nonce
        else:
            nonce = None
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add CSP with nonce if applicable
        csp = self.csp_template
        if nonce:
            csp = csp.replace("'unsafe-inline'", f"'nonce-{nonce}' 'unsafe-inline'")
        
        # Add report URI if configured
        if self.report_uri:
            csp += f"; report-uri {self.report_uri}"
        
        response.headers["Content-Security-Policy"] = csp
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove sensitive headers
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        for header in sensitive_headers:
            if header in response.headers:
                del response.headers[header]
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitize user inputs to prevent XSS and injection attacks.
    """
    
    def __init__(
        self,
        app,
        allowed_tags: Optional[List[str]] = None,
        allowed_attributes: Optional[Dict[str, List[str]]] = None,
        strip_comments: bool = True
    ):
        super().__init__(app)
        
        # Default allowed HTML tags
        if allowed_tags is None:
            allowed_tags = [
                'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'blockquote',
                'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
            ]
        
        # Default allowed attributes
        if allowed_attributes is None:
            allowed_attributes = {
                'a': ['href', 'title', 'target', 'rel'],
                'span': ['class', 'style'],
                'div': ['class', 'style'],
                'img': ['src', 'alt', 'width', 'height'],
                'code': ['class']
            }
        
        self.allowed_tags = allowed_tags
        self.allowed_attributes = allowed_attributes
        self.strip_comments = strip_comments
        
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bor\b\s*\d+\s*=\s*\d+)",
            r"(\band\b\s*\d+\s*=\s*\d+)",
            r"(';|';--)",
            r"(\bwaitfor\s+delay\b)",
            r"(\bexec\s*\()",
            r"(\bxp_cmdshell\b)"
        ]
        
        self.sql_regex = re.compile("|".join(self.sql_patterns), re.IGNORECASE)
        
        # NoSQL injection patterns
        self.nosql_patterns = [
            r"(\$where|\$ne|\$gt|\$lt|\$gte|\$lte|\$in|\$nin|\$exists|\$regex)",
            r"(\{.*\$.*\})",
            r"(function\s*\(.*\))",
            r"(this\.|db\.|collection\.)"
        ]
        
        self.nosql_regex = re.compile("|".join(self.nosql_patterns), re.IGNORECASE)
        
        # Command injection patterns
        self.cmd_patterns = [
            r"(;|\||&|`|\$\(|\$\{|<\(|>\()",
            r"(\b(cat|ls|rm|mv|cp|chmod|chown|sudo|su|wget|curl|nc|telnet)\b)",
            r"(\.\.\/|\.\.\\)",
            r"(\/etc\/passwd|\/etc\/shadow|C:\\Windows)"
        ]
        
        self.cmd_regex = re.compile("|".join(self.cmd_patterns), re.IGNORECASE)
    
    def sanitize_html(self, content: str) -> str:
        """Sanitize HTML content."""
        if BLEACH_AVAILABLE:
            return bleach.clean(
                content,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                strip=True,
                strip_comments=self.strip_comments
            )
        else:
            # Fallback: basic HTML tag removal
            import html
            # Escape HTML entities
            content = html.escape(content)
            # Remove script tags (basic protection)
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
            return content
    
    def detect_sql_injection(self, value: str) -> bool:
        """Detect potential SQL injection attempts."""
        if not isinstance(value, str):
            return False
        
        # Check for SQL patterns
        if self.sql_regex.search(value):
            logger.warning(
                "potential_sql_injection_detected",
                value=value[:100],  # Log only first 100 chars
                pattern="sql"
            )
            return True
        
        return False
    
    def detect_nosql_injection(self, value: str) -> bool:
        """Detect potential NoSQL injection attempts."""
        if not isinstance(value, str):
            return False
        
        # Check for NoSQL patterns
        if self.nosql_regex.search(value):
            logger.warning(
                "potential_nosql_injection_detected",
                value=value[:100],
                pattern="nosql"
            )
            return True
        
        return False
    
    def detect_command_injection(self, value: str) -> bool:
        """Detect potential command injection attempts."""
        if not isinstance(value, str):
            return False
        
        # Check for command injection patterns
        if self.cmd_regex.search(value):
            logger.warning(
                "potential_command_injection_detected",
                value=value[:100],
                pattern="command"
            )
            return True
        
        return False
    
    def is_safe_url(self, url: str, allowed_hosts: Optional[List[str]] = None) -> bool:
        """Check if URL is safe for redirect."""
        if not url:
            return False
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        # Check for dangerous schemes
        dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
        if parsed.scheme in dangerous_schemes:
            return False
        
        # If no host specified, it's a relative URL (safe)
        if not parsed.netloc:
            return True
        
        # Check against allowed hosts
        if allowed_hosts:
            return parsed.netloc in allowed_hosts
        
        # Default: only allow same host
        return parsed.netloc == settings.FRONTEND_URL.replace("http://", "").replace("https://", "")
    
    async def dispatch(self, request: Request, call_next):
        # Skip for safe methods and paths
        safe_methods = ["GET", "HEAD", "OPTIONS"]
        safe_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        
        if request.method in safe_methods or request.url.path in safe_paths:
            return await call_next(request)
        
        # Check query parameters
        for key, value in request.query_params.items():
            if self.detect_sql_injection(value):
                logger.warning(
                    "sql_injection_blocked",
                    path=request.url.path,
                    param=key,
                    client_ip=request.client.host if request.client else "unknown"
                )
                return Response(
                    content="Invalid input detected",
                    status_code=400
                )
            
            if self.detect_command_injection(value):
                logger.warning(
                    "command_injection_blocked",
                    path=request.url.path,
                    param=key,
                    client_ip=request.client.host if request.client else "unknown"
                )
                return Response(
                    content="Invalid input detected",
                    status_code=400
                )
        
        # For POST/PUT/PATCH requests, we'll need to check the body
        # This is handled in the request validation layer
        
        response = await call_next(request)
        return response


class AntiCSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.
    Uses double-submit cookie pattern.
    """
    
    def __init__(
        self,
        app,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        safe_methods: List[str] = None,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.safe_methods = safe_methods or ["GET", "HEAD", "OPTIONS"]
        self.exclude_paths = exclude_paths or ["/api/v1/auth/login", "/api/v1/auth/register"]
    
    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)
    
    def get_csrf_token_from_cookie(self, request: Request) -> Optional[str]:
        """Get CSRF token from cookie."""
        return request.cookies.get(self.cookie_name)
    
    def get_csrf_token_from_header(self, request: Request) -> Optional[str]:
        """Get CSRF token from header."""
        return request.headers.get(self.header_name)
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            
            # Set CSRF cookie if not present
            if self.cookie_name not in request.cookies:
                token = self.generate_csrf_token()
                response.set_cookie(
                    key=self.cookie_name,
                    value=token,
                    httponly=True,
                    secure=settings.is_production,
                    samesite="strict",
                    max_age=3600  # 1 hour
                )
            
            return response
        
        # Skip for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Check CSRF token
        cookie_token = self.get_csrf_token_from_cookie(request)
        header_token = self.get_csrf_token_from_header(request)
        
        if not cookie_token or not header_token or cookie_token != header_token:
            logger.warning(
                "csrf_validation_failed",
                path=request.url.path,
                method=request.method,
                has_cookie=bool(cookie_token),
                has_header=bool(header_token)
            )
            
            return Response(
                content="CSRF validation failed",
                status_code=403
            )
        
        response = await call_next(request)
        return response


# Utility functions for input validation
def validate_email(email: str) -> bool:
    """Validate email format."""
    email_regex = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    return bool(email_regex.match(email))


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    if len(password) < getattr(settings, "PASSWORD_MIN_LENGTH", 8):
        issues.append(f"Password must be at least {getattr(settings, 'PASSWORD_MIN_LENGTH', 8)} characters")
    
    if getattr(settings, "PASSWORD_REQUIRE_UPPERCASE", True) and not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if getattr(settings, "PASSWORD_REQUIRE_LOWERCASE", True) and not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if getattr(settings, "PASSWORD_REQUIRE_NUMBERS", True) and not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    
    if getattr(settings, "PASSWORD_REQUIRE_SPECIAL", True):
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            issues.append("Password must contain at least one special character")
    
    # Check for common passwords
    common_passwords = [
        "password", "123456", "password123", "admin", "letmein",
        "welcome", "monkey", "dragon", "baseball", "iloveyou"
    ]
    
    if password.lower() in common_passwords:
        issues.append("Password is too common")
    
    return len(issues) == 0, issues


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal."""
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ["../", "..\\", "/", "\\", "\x00", "\n", "\r", "\t"]
    for char in dangerous_chars:
        filename = filename.replace(char, "")
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename


# Export middleware and utilities
__all__ = [
    "SecurityHeadersMiddleware",
    "InputSanitizationMiddleware",
    "AntiCSRFMiddleware",
    "validate_email",
    "validate_password_strength",
    "sanitize_filename"
]