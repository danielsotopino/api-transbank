from contextvars import ContextVar
from typing import Optional

"""
Context variables for request tracing and logging.

These variables are set per-request and automatically propagate through
async call stacks, making them available to all logging calls within
the same request context.

Usage:
    # In middleware:
    correlation_id_var.set(str(uuid.uuid4()))
    endpoint_var.set(str(request.url.path))

    # In any function within the request:
    correlation_id = correlation_id_var.get()
    logger.info("Processing request", correlation_id=correlation_id)
"""

# Unique identifier for tracing requests across services
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    'correlation_id',
    default=None
)

# Current endpoint path
endpoint_var: ContextVar[Optional[str]] = ContextVar(
    'endpoint',
    default=None
)

# HTTP method (GET, POST, etc.)
method_var: ContextVar[Optional[str]] = ContextVar(
    'method',
    default=None
)

# User identifier for the current request
user_id_var: ContextVar[Optional[str]] = ContextVar(
    'user_id',
    default=None
)

# Username for the current request
username_var: ContextVar[Optional[str]] = ContextVar(
    'username',
    default=None
)
