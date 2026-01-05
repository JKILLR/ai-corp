"""
Logging utilities for AI Corp
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger for AI Corp.

    Args:
        name: Logger name (usually __name__)
        level: Optional logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(f"ai-corp.{name}")

    if level is not None:
        logger.setLevel(level)
    elif not logger.level:
        logger.setLevel(logging.INFO)

    # Add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)

    return logger


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure global logging for AI Corp.

    Args:
        level: Logging level
    """
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set AI Corp logger
    logger = logging.getLogger('ai-corp')
    logger.setLevel(level)
