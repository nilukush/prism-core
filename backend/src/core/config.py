"""
Core configuration module for PRISM.
Handles all environment variables and application settings.
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import PostgresDsn, RedisDsn, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )
    
    # Application
    APP_NAME: str = "PRISM"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Aliases for compatibility
    PROJECT_NAME: str = Field(default="PRISM", alias="APP_NAME")
    VERSION: str = Field(default="0.1.0", alias="APP_VERSION")
    ENVIRONMENT: str = Field(default="development", alias="APP_ENV")
    DEBUG: bool = Field(default=False, alias="APP_DEBUG")
    
    # Security
    # For production, set SECRET_KEY via environment variable
    # This ensures JWT tokens survive restarts
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/prism_dev"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0"
    )
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_POOL_SIZE: int = 10
    
    # Vector Database (Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "prism_documents"
    QDRANT_USE_CLOUD: bool = False
    
    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    LLM_REQUEST_TIMEOUT: int = 120
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    
    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Local LLM (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: Union[str, List[str]] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: Union[str, List[str]] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator("CORS_ALLOW_METHODS", mode="before")
    @classmethod
    def assemble_cors_methods(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    
    @field_validator("CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def assemble_cors_headers(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]
    
    # Feature Flags
    FEATURE_ANALYTICS_ENABLED: bool = True
    FEATURE_MARKETPLACE_ENABLED: bool = False
    FEATURE_ENTERPRISE_SSO_ENABLED: bool = False
    FEATURE_MULTI_TENANCY_ENABLED: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    RATE_LIMIT_STRATEGY: str = "token_bucket"  # token_bucket or sliding_window
    
    # DDoS Protection
    DDOS_PROTECTION_ENABLED: bool = True
    DDOS_MAX_CONNECTIONS_PER_IP: int = 100
    DDOS_BLACKLIST_DURATION: int = 3600
    DDOS_CHALLENGE_ENABLED: bool = True
    BEHIND_PROXY: bool = False  # Set to True if behind reverse proxy
    
    # Caching
    CACHE_TTL_DEFAULT: int = 300
    CACHE_TTL_DOCUMENTS: int = 3600
    CACHE_TTL_ANALYTICS: int = 1800
    
    # Worker Configuration
    CELERY_BROKER_URL: RedisDsn = Field(
        default="redis://localhost:6379/1"
    )
    CELERY_RESULT_BACKEND: RedisDsn = Field(
        default="redis://localhost:6379/2"
    )
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_TASK_EAGER_PROPAGATES: bool = True
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # OpenTelemetry
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "prism-backend"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: Optional[str] = "./logs/prism.log"
    LOG_FILE_ROTATION: str = "daily"
    LOG_FILE_RETENTION: int = 30
    
    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: Path = Path("./uploads")
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_REGION: str = "us-east-1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3100", "http://localhost:8100"]
    )
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@prism-ai.dev"
    SMTP_FROM_NAME: str = "PRISM"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    
    # Email Service Configuration
    MAIL_USERNAME: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    MAIL_PASSWORD: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    MAIL_FROM: str = Field(default="noreply@prism-ai.dev", alias="SMTP_FROM_EMAIL")
    MAIL_PORT: int = Field(default=587, alias="SMTP_PORT")
    MAIL_SERVER: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    MAIL_FROM_NAME: str = Field(default="PRISM", alias="SMTP_FROM_NAME")
    MAIL_USE_TLS: bool = Field(default=True, alias="SMTP_TLS")
    MAIL_USE_SSL: bool = Field(default=False, alias="SMTP_SSL")
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True
    
    # Email Settings
    EMAIL_ENABLED: bool = True
    EMAIL_RATE_LIMIT_PER_HOUR: int = 10
    EMAIL_BATCH_SIZE: int = 50
    EMAIL_RETRY_ATTEMPTS: int = 3
    EMAIL_RETRY_DELAY: int = 60
    SUPPORT_EMAIL: str = "support@prism-ai.dev"
    
    # Email Feature Flags
    EMAIL_VERIFICATION_REQUIRED: bool = True
    EMAIL_WELCOME_ENABLED: bool = True
    EMAIL_DAILY_DIGEST_ENABLED: bool = False
    EMAIL_WEEKLY_REPORT_ENABLED: bool = True
    
    # Integrations
    # Jira
    JIRA_URL: Optional[str] = None
    JIRA_EMAIL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_DEFAULT_PROJECT: Optional[str] = None
    
    # Confluence
    CONFLUENCE_URL: Optional[str] = None
    CONFLUENCE_EMAIL: Optional[str] = None
    CONFLUENCE_API_TOKEN: Optional[str] = None
    CONFLUENCE_DEFAULT_SPACE: Optional[str] = None
    
    # Slack
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_APP_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    SLACK_DEFAULT_CHANNEL: Optional[str] = None
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_ORG: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.APP_ENV == "testing"
    
    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for a specific provider."""
        provider = provider or self.DEFAULT_LLM_PROVIDER
        
        if provider == "openai":
            return {
                "api_key": self.OPENAI_API_KEY,
                "organization": self.OPENAI_ORG_ID,
                "base_url": self.OPENAI_API_BASE,
                "model": self.DEFAULT_LLM_MODEL,
                "temperature": self.LLM_TEMPERATURE,
                "max_tokens": self.LLM_MAX_TOKENS,
                "timeout": self.LLM_REQUEST_TIMEOUT,
            }
        elif provider == "anthropic":
            return {
                "api_key": self.ANTHROPIC_API_KEY,
                "model": "claude-3-opus-20240229",
                "temperature": self.LLM_TEMPERATURE,
                "max_tokens": self.LLM_MAX_TOKENS,
                "timeout": self.LLM_REQUEST_TIMEOUT,
            }
        elif provider == "ollama":
            return {
                "base_url": self.OLLAMA_BASE_URL,
                "model": self.OLLAMA_MODEL,
                "temperature": self.LLM_TEMPERATURE,
                "max_tokens": self.LLM_MAX_TOKENS,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


# Create global settings instance
settings = Settings()