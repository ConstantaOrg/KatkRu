"""
Data models for auth analyzer.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class AuthInfo:
    """Authentication information for a dependency."""
    requires_auth: bool = False
    roles: List[str] = None
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = []


@dataclass
class JWTInfo:
    """JWT token information."""
    uses_jwt: bool = False
    token_location: str = None  # 'cookie', 'header', 'query'
    token_name: str = None
    algorithm: str = None
    expiration_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.expiration_info is None:
            self.expiration_info = {}


@dataclass
class MiddlewareInfo:
    """Middleware authentication information."""
    has_auth_middleware: bool = False
    middleware_types: List[str] = None
    ip_whitelist_check: bool = False
    session_management: bool = False
    token_refresh: bool = False
    
    def __post_init__(self):
        if self.middleware_types is None:
            self.middleware_types = []


@dataclass
class AuthDocumentation:
    """Complete authentication documentation for a route."""
    authentication_required: bool
    roles_required: List[str]
    jwt_info: JWTInfo
    middleware_info: MiddlewareInfo
    public_endpoint: bool
    private_endpoint: bool
    auth_description: str