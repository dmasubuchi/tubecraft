"""
TUBECRAFT Logging Configuration
Structured logging setup using structlog
"""

import structlog
import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json
import os

from .config import settings


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to log events"""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service information to log events"""
    event_dict["service"] = "tubecraft-generator"
    event_dict["version"] = settings.app_version
    return event_dict


def setup_logging():
    """Configure structured logging"""
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Determine processors based on format
    if settings.log_format.lower() == "json":
        processors = [
            add_timestamp,
            add_service_info,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            add_timestamp,
            add_service_info,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a configured logger instance"""
    return structlog.get_logger(name)


class StructlogHandler(logging.Handler):
    """
    Custom logging handler that outputs to structlog
    Useful for capturing logs from third-party libraries
    """
    
    def __init__(self):
        super().__init__()
        self.logger = structlog.get_logger("external")
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record via structlog"""
        try:
            # Extract relevant fields
            log_entry = {
                "message": record.getMessage(),
                "level": record.levelname.lower(),
                "logger_name": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.format(record)
            
            # Log through structlog
            getattr(self.logger, record.levelname.lower(), self.logger.info)(
                log_entry["message"],
                **{k: v for k, v in log_entry.items() if k != "message"}
            )
            
        except Exception:
            self.handleError(record)


def configure_external_loggers():
    """Configure external library loggers to use structlog"""
    
    # List of external loggers to configure
    external_loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error", 
        "fastapi",
        "httpx",
        "sqlalchemy.engine",
        "asyncpg",
    ]
    
    structlog_handler = StructlogHandler()
    
    for logger_name in external_loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(structlog_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


def log_request_response(func):
    """Decorator to log HTTP request/response"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger("api")
        
        # Log request
        logger.info(
            "API request started",
            endpoint=func.__name__,
            args=str(args)[:200],  # Truncate for security
            kwargs={k: str(v)[:200] for k, v in kwargs.items() if k != "password"}
        )
        
        start_time = datetime.utcnow()
        
        try:
            result = await func(*args, **kwargs)
            
            # Log successful response
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "API request completed",
                endpoint=func.__name__,
                duration_seconds=duration,
                status="success"
            )
            
            return result
            
        except Exception as e:
            # Log error
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "API request failed",
                endpoint=func.__name__,
                duration_seconds=duration,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    return wrapper


# Performance logging utilities
class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, logger: structlog.BoundLogger = None):
        self.operation_name = operation_name
        self.logger = logger or get_logger("performance")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(
            "Operation started",
            operation=self.operation_name
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            
            if exc_type is None:
                self.logger.info(
                    "Operation completed",
                    operation=self.operation_name,
                    duration_seconds=duration
                )
            else:
                self.logger.error(
                    "Operation failed",
                    operation=self.operation_name,
                    duration_seconds=duration,
                    error=str(exc_val),
                    error_type=exc_type.__name__ if exc_type else None
                )


def performance_timer(operation_name: str):
    """Decorator for timing function execution"""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with PerformanceTimer(f"{func.__name__}_{operation_name}"):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with PerformanceTimer(f"{func.__name__}_{operation_name}"):
                return func(*args, **kwargs)
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator