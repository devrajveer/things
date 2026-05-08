import logging
import sys
from typing import Any

import structlog

def configure_logging(environment: str = "dev", log_level: str = "info") -> None:
    """Configure structlog based on environment."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.CallsiteParameterAdder(
            {structlog.processors.CallsiteParameter.FUNC_NAME}
        ),
    ]

    if environment == "prod":
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger() -> structlog.BoundLogger:
    """Get a bound logger instance."""
    return structlog.get_logger()
