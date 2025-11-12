"""
Logging configuration for SANGKURIANG API
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
import json
from typing import Dict, Any

# Log formatters
STANDARD_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DETAILED_FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

JSON_FORMATTER = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def create_log_directory():
    """Create log directory if it doesn't exist."""
    log_dir = os.getenv("LOG_DIRECTORY", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def setup_file_handler(logger_name: str, log_level: str = "INFO") -> logging.handlers.RotatingFileHandler:
    """Setup file handler for logging."""
    log_dir = create_log_directory()
    
    # Create filename with date
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{logger_name}_{current_date}.log")
    
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(DETAILED_FORMATTER)
    
    return file_handler

def setup_console_handler(log_level: str = "INFO") -> logging.StreamHandler:
    """Setup console handler for logging."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(STANDARD_FORMATTER)
    
    return console_handler

def setup_error_handler() -> logging.handlers.RotatingFileHandler:
    """Setup error handler for logging errors."""
    log_dir = create_log_directory()
    
    # Create error log file
    current_date = datetime.now().strftime("%Y-%m-%d")
    error_file = os.path.join(log_dir, f"errors_{current_date}.log")
    
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(DETAILED_FORMATTER)
    
    return error_handler

def setup_logging():
    """Setup logging configuration."""
    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(setup_console_handler(log_level))
    root_logger.addHandler(setup_error_handler())
    
    # Setup specific loggers
    # API logger
    api_logger = logging.getLogger("sangkuriang.api")
    api_logger.setLevel(getattr(logging, log_level))
    api_logger.addHandler(setup_file_handler("api", log_level))
    
    # Database logger
    db_logger = logging.getLogger("sangkuriang.database")
    db_logger.setLevel(getattr(logging, log_level))
    db_logger.addHandler(setup_file_handler("database", log_level))
    
    # Security logger
    security_logger = logging.getLogger("sangkuriang.security")
    security_logger.setLevel(getattr(logging, log_level))
    security_logger.addHandler(setup_file_handler("security", log_level))
    
    # Audit logger
    audit_logger = logging.getLogger("sangkuriang.audit")
    audit_logger.setLevel(getattr(logging, log_level))
    audit_logger.addHandler(setup_file_handler("audit", log_level))
    
    # Payment logger
    payment_logger = logging.getLogger("sangkuriang.payment")
    payment_logger.setLevel(getattr(logging, log_level))
    payment_logger.addHandler(setup_file_handler("payment", log_level))
    
    # Disable noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    # Log startup
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log directory: {create_log_directory()}")

def log_request(request_info: Dict[str, Any]) -> None:
    """Log request information."""
    logger = logging.getLogger("sangkuriang.api.request")
    
    log_data = {
        "type": "request",
        "timestamp": datetime.utcnow().isoformat(),
        "method": request_info.get("method"),
        "url": request_info.get("url"),
        "ip": request_info.get("ip"),
        "user_agent": request_info.get("user_agent"),
        "user_id": request_info.get("user_id"),
        "request_id": request_info.get("request_id")
    }
    
    logger.info(json.dumps(log_data))

def log_response(response_info: Dict[str, Any]) -> None:
    """Log response information."""
    logger = logging.getLogger("sangkuriang.api.response")
    
    log_data = {
        "type": "response",
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": response_info.get("status_code"),
        "response_time": response_info.get("response_time"),
        "request_id": response_info.get("request_id"),
        "error": response_info.get("error")
    }
    
    logger.info(json.dumps(log_data))

def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log security events."""
    logger = logging.getLogger("sangkuriang.security.event")
    
    log_data = {
        "type": "security_event",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    
    logger.warning(json.dumps(log_data))

def log_audit_event(project_id: str, audit_type: str, result: Dict[str, Any]) -> None:
    """Log audit events."""
    logger = logging.getLogger("sangkuriang.audit.event")
    
    log_data = {
        "type": "audit_event",
        "project_id": project_id,
        "audit_type": audit_type,
        "timestamp": datetime.utcnow().isoformat(),
        "result": result
    }
    
    logger.info(json.dumps(log_data))

def log_payment_event(event_type: str, payment_id: str, details: Dict[str, Any]) -> None:
    """Log payment events."""
    logger = logging.getLogger("sangkuriang.payment.event")
    
    log_data = {
        "type": "payment_event",
        "event_type": event_type,
        "payment_id": payment_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    
    logger.info(json.dumps(log_data))