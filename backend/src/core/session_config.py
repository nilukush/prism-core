"""
Session configuration module for enterprise deployment.
Centralizes all session-related configuration values.
"""

import os
from typing import Optional


class SessionConfig:
    """Enterprise session configuration with secure defaults."""
    
    # Session TTL configuration (in seconds)
    SESSION_TTL: int = int(os.getenv('SESSION_TTL', str(86400 * 7)))  # 7 days default
    TOKEN_FAMILY_TTL: int = int(os.getenv('TOKEN_FAMILY_TTL', str(86400 * 30)))  # 30 days
    BLACKLIST_TTL: int = int(os.getenv('BLACKLIST_TTL', str(86400 * 7)))  # 7 days
    ACCESS_TOKEN_TTL: int = int(os.getenv('ACCESS_TOKEN_TTL', '1800'))  # 30 minutes
    REFRESH_TOKEN_TTL: int = int(os.getenv('REFRESH_TOKEN_TTL', str(86400 * 7)))  # 7 days
    
    # Redis configuration
    REDIS_LOCK_TTL: int = int(os.getenv('REDIS_LOCK_TTL', '30'))  # 30 seconds
    REDIS_RETRY_MAX: int = int(os.getenv('REDIS_RETRY_MAX', '5'))
    REDIS_RETRY_DELAY: int = int(os.getenv('REDIS_RETRY_DELAY', '1'))
    REDIS_RETRY_BACKOFF: float = float(os.getenv('REDIS_RETRY_BACKOFF', '2.0'))
    
    # Security configuration
    SESSION_ID_BYTES: int = int(os.getenv('SESSION_ID_BYTES', '32'))  # 256 bits
    SESSION_BINDING_ENABLED: bool = os.getenv('SESSION_BINDING_ENABLED', 'true').lower() == 'true'
    SESSION_BINDING_SECRET_BYTES: int = int(os.getenv('SESSION_BINDING_SECRET_BYTES', '32'))
    
    # Token configuration
    TOKEN_ROTATION_ENABLED: bool = os.getenv('TOKEN_ROTATION_ENABLED', 'true').lower() == 'true'
    TOKEN_REUSE_WINDOW: int = int(os.getenv('TOKEN_REUSE_WINDOW', '10'))  # seconds
    TOKEN_FAMILY_MAX_HISTORY: int = int(os.getenv('TOKEN_FAMILY_MAX_HISTORY', '20'))
    
    # Cleanup configuration
    SESSION_CLEANUP_INTERVAL: int = int(os.getenv('SESSION_CLEANUP_INTERVAL', '3600'))  # 1 hour
    SESSION_CLEANUP_BATCH_SIZE: int = int(os.getenv('SESSION_CLEANUP_BATCH_SIZE', '1000'))
    
    # Audit configuration
    AUDIT_RETENTION_DAYS: int = int(os.getenv('AUDIT_RETENTION_DAYS', '90'))
    AUDIT_ENABLED: bool = os.getenv('AUDIT_ENABLED', 'true').lower() == 'true'
    
    # Redis key prefixes (allow customization for multi-tenant deployments)
    REDIS_PREFIX_SESSION: str = os.getenv('REDIS_PREFIX_SESSION', 'session:')
    REDIS_PREFIX_TOKEN_FAMILY: str = os.getenv('REDIS_PREFIX_TOKEN_FAMILY', 'token:family:')
    REDIS_PREFIX_BLACKLIST: str = os.getenv('REDIS_PREFIX_BLACKLIST', 'token:blacklist:')
    REDIS_PREFIX_AUDIT: str = os.getenv('REDIS_PREFIX_AUDIT', 'audit:session:')
    REDIS_PREFIX_LOCK: str = os.getenv('REDIS_PREFIX_LOCK', 'lock:session:')
    
    @classmethod
    def validate(cls) -> None:
        """Validate session configuration values."""
        # Ensure TTLs make sense
        if cls.ACCESS_TOKEN_TTL >= cls.REFRESH_TOKEN_TTL:
            raise ValueError("Access token TTL must be less than refresh token TTL")
        
        if cls.TOKEN_FAMILY_TTL < cls.REFRESH_TOKEN_TTL:
            raise ValueError("Token family TTL must be greater than refresh token TTL")
        
        if cls.SESSION_TTL < cls.ACCESS_TOKEN_TTL:
            raise ValueError("Session TTL must be greater than access token TTL")
        
        # Validate security settings
        if cls.SESSION_ID_BYTES < 16:  # 128 bits minimum
            raise ValueError("Session ID must be at least 128 bits (16 bytes)")
        
        if cls.SESSION_BINDING_SECRET_BYTES < 16:
            raise ValueError("Session binding secret must be at least 128 bits (16 bytes)")
        
        # Validate Redis settings
        if cls.REDIS_RETRY_MAX < 1:
            raise ValueError("Redis retry max must be at least 1")
        
        if cls.REDIS_RETRY_DELAY < 0:
            raise ValueError("Redis retry delay must be non-negative")
        
        if cls.REDIS_RETRY_BACKOFF < 1:
            raise ValueError("Redis retry backoff must be at least 1")
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """Get configuration as dictionary for session manager initialization."""
        return {
            'session_ttl': cls.SESSION_TTL,
            'token_family_ttl': cls.TOKEN_FAMILY_TTL,
            'blacklist_ttl': cls.BLACKLIST_TTL,
            'lock_ttl': cls.REDIS_LOCK_TTL,
            'session_id_bytes': cls.SESSION_ID_BYTES,
            'redis_retry_max': cls.REDIS_RETRY_MAX,
            'redis_retry_delay': cls.REDIS_RETRY_DELAY,
            'redis_retry_backoff': cls.REDIS_RETRY_BACKOFF,
            'session_binding_enabled': cls.SESSION_BINDING_ENABLED,
            'session_binding_secret_bytes': cls.SESSION_BINDING_SECRET_BYTES,
            'token_rotation_enabled': cls.TOKEN_ROTATION_ENABLED,
            'token_reuse_window': cls.TOKEN_REUSE_WINDOW,
            'token_family_max_history': cls.TOKEN_FAMILY_MAX_HISTORY,
            'cleanup_interval': cls.SESSION_CLEANUP_INTERVAL,
            'cleanup_batch_size': cls.SESSION_CLEANUP_BATCH_SIZE,
            'audit_retention_days': cls.AUDIT_RETENTION_DAYS,
            'audit_enabled': cls.AUDIT_ENABLED,
            'prefix_session': cls.REDIS_PREFIX_SESSION,
            'prefix_token_family': cls.REDIS_PREFIX_TOKEN_FAMILY,
            'prefix_blacklist': cls.REDIS_PREFIX_BLACKLIST,
            'prefix_audit': cls.REDIS_PREFIX_AUDIT,
            'prefix_lock': cls.REDIS_PREFIX_LOCK,
        }


# Validate configuration on import in production
if os.getenv('ENVIRONMENT') in ['production', 'staging']:
    SessionConfig.validate()