"""
Structured logging configuration using structlog.
Provides JSON logging for production and pretty printing for development.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.processors import CallsiteParameter

from backend.src.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Create logs directory if it doesn't exist
    if settings.LOG_FILE_PATH:
        log_path = Path(settings.LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog processors
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.contextvars.merge_contextvars,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    # Configure renderer based on environment
    if settings.is_development and settings.LOG_FORMAT != "json":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    )
    
    # Add file handler if configured
    handlers = [handler]
    if settings.LOG_FILE_PATH:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            str(settings.LOG_FILE_PATH),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=settings.LOG_FILE_RETENTION,
        )
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=shared_processors,
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
        )
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        handlers=handlers,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        force=True,
    )
    
    # Suppress noisy loggers
    for logger_name in ["uvicorn.access", "httpx", "httpcore"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


def log_error(
    logger: structlog.stdlib.BoundLogger,
    error: Exception,
    context: Dict[str, Any] | None = None,
) -> None:
    """
    Log an error with context.
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context to include
    """
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **(context or {}),
        exc_info=True,
    )


# Initialize default logger
setup_logging()
logger = get_logger(__name__)

# Example usage
if __name__ == "__main__":
    logger.info("logging_configured", environment=settings.APP_ENV)
    logger.debug("debug_message", data={"example": "value"})
    
    try:
        raise ValueError("Example error")
    except Exception as e:
        log_error(logger, e, {"operation": "example_operation"})