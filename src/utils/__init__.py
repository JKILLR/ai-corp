"""
AI Corp Utilities Module

Common utilities for AI Corp:
- Logging
- Configuration
- Helpers
"""

from .config import load_config, get_corp_path
from .logging import get_logger

__all__ = ['load_config', 'get_corp_path', 'get_logger']
