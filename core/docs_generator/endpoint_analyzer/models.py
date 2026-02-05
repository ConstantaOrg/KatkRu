"""
Data models for endpoint analyzer.
"""

from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class RouteInfo:
    """Basic route information extracted from FastAPI."""
    path: str
    method: str
    function: Callable
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None