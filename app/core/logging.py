"""
Logging configuration for the FastAPI application
"""

import logging

import structlog
from rich.console import Console
from rich.logging import RichHandler

from app.core.config import settings

# Rich console for pretty output
console = Console()


def setup_logging():
    """Setup structured logging and rich console output"""

    # Configure structured logging
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
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure rich logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    # Set log level
    logging.getLogger().setLevel(getattr(logging, settings.log_level.upper()))

    return structlog.get_logger()


# Global logger instance
logger = setup_logging()
