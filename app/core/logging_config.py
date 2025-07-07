import logging
import json
import os
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
endpoint_var: ContextVar[Optional[str]] = ContextVar('endpoint', default=None)
method_var: ContextVar[Optional[str]] = ContextVar('method', default=None)


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "artifact": os.getenv("SERVICE_NAME", "api-transbank"),
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "correlation_id": correlation_id_var.get(),
            "endpoint": endpoint_var.get(),
            "method": method_var.get(),
            "message": record.getMessage(),
        }
        
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
            
        if hasattr(record, 'error'):
            log_entry["error"] = record.error
            
        if record.exc_info:
            log_entry["traceback"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)


def setup_logging():
    """Configure structured logging"""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
        handlers=[handler],
        format='%(message)s'
    )
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)