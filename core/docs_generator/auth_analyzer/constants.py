"""
Constants for auth analyzer.
"""

from dataclasses import dataclass
from typing import List, Set
from core.utils.anything import Roles


@dataclass
class AuthDependencies:
    """Known authentication dependencies."""
    KNOWN_AUTH_DEPS: Set[str] = None
    
    def __post_init__(self):
        if self.KNOWN_AUTH_DEPS is None:
            self.KNOWN_AUTH_DEPS = {
                'JWTCookieDep',
                'jwt_cookie_dep',
                'role_require'
            }


@dataclass
class KnownRoles:
    """Known application roles."""
    ROLES: Set[str] = None
    
    def __post_init__(self):
        if self.ROLES is None:
            self.ROLES = {
                Roles.methodist,
                Roles.read_all
            }


@dataclass
class PathIndicators:
    """Path indicators for authentication requirements."""
    PRIVATE_INDICATORS: List[str] = None
    PUBLIC_INDICATORS: List[str] = None
    
    def __post_init__(self):
        if self.PRIVATE_INDICATORS is None:
            self.PRIVATE_INDICATORS = ['/private/', '/server/']
        
        if self.PUBLIC_INDICATORS is None:
            self.PUBLIC_INDICATORS = ['/public/', '/api/v1/public']


@dataclass
class AuthKeywords:
    """Keywords for authentication detection."""
    AUTH_KEYWORDS: List[str] = None
    JWT_KEYWORDS: List[str] = None
    
    def __post_init__(self):
        if self.AUTH_KEYWORDS is None:
            self.AUTH_KEYWORDS = ['jwt', 'auth', 'cookie']
        
        if self.JWT_KEYWORDS is None:
            self.JWT_KEYWORDS = ['jwt', 'cookie', 'header']


@dataclass
class JWTDefaults:
    """Default JWT configuration values."""
    ALGORITHM: str = 'RS256'
    COOKIE_TOKEN_NAME: str = 'access_token'
    HEADER_TOKEN_NAME: str = 'Authorization'
    
    EXPIRATION_INFO: dict = None
    
    def __post_init__(self):
        if self.EXPIRATION_INFO is None:
            self.EXPIRATION_INFO = {
                'access_token_ttl': 'Configurable via env.JWTs.ttl_aT',
                'refresh_token_ttl': 'Configurable via env.JWTs.ttl_rT',
                'websocket_token_ttl': 'Configurable via env.JWTs.ttl_wT'
            }


@dataclass
class MiddlewareDefaults:
    """Default middleware configuration."""
    MIDDLEWARE_TYPES: List[str] = None
    
    def __post_init__(self):
        if self.MIDDLEWARE_TYPES is None:
            self.MIDDLEWARE_TYPES = ['AuthUXASGIMiddleware', 'LoggingTimeMiddleware']


# Создаем экземпляры для использования
AUTH_DEPENDENCIES = AuthDependencies()
KNOWN_ROLES = KnownRoles()
PATH_INDICATORS = PathIndicators()
AUTH_KEYWORDS = AuthKeywords()
JWT_DEFAULTS = JWTDefaults()
MIDDLEWARE_DEFAULTS = MiddlewareDefaults()