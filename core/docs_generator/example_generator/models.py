"""
Models for example generator.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ExampleRequest:
    """Represents an HTTP request example."""
    method: str
    url: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    path_params: Dict[str, Any]
    body: Optional[Dict[str, Any]]


@dataclass
class ExampleResponse:
    """Represents an HTTP response example."""
    status_code: int
    headers: Dict[str, str]
    body: Dict[str, Any]


@dataclass
class CurlOptions:
    """Options for cURL command generation."""
    include_verbose: bool = True
    include_auth: bool = True
    format_multiline: bool = False
    custom_headers: Optional[Dict[str, str]] = None