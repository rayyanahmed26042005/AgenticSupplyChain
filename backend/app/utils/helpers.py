"""
General helper utilities.
"""

from datetime import datetime
from typing import Any, Dict
import uuid


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID."""
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}-{uid}" if prefix else uid


def timestamp_now() -> str:
    """Get current ISO timestamp."""
    return datetime.now().isoformat()


def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """Safely get nested dict value with dot notation."""
    keys = key.split(".")
    result = data
    for k in keys:
        if isinstance(result, dict):
            result = result.get(k, default)
        else:
            return default
    return result
