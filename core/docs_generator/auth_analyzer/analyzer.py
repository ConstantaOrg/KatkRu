"""
Main authentication analyzer class.
"""

from typing import List, Tuple
from fastapi.routing import APIRoute

from .models import AuthDocumentation
from .handlers import (
    analyze_auth_requirements, analyze_jwt_token_info, analyze_middleware_auth,
    get_auth_documentation
)


class AuthAnalyzer:
    """Analyzes authentication and authorization requirements for API endpoints."""
    
    def __init__(self):
        pass
    
    def analyze_auth_requirements(self, route: APIRoute) -> Tuple[bool, List[str]]:
        """
        Analyze authentication and authorization requirements for a route.
        
        Returns:
            Tuple of (auth_required: bool, roles_required: List[str])
        """
        return analyze_auth_requirements(route)
    
    def analyze_jwt_token_info(self, route: APIRoute) -> dict:
        """
        Extract JWT token information from route analysis.
        
        Returns:
            Dict with JWT token configuration details
        """
        jwt_info = analyze_jwt_token_info(route)
        return {
            'uses_jwt': jwt_info.uses_jwt,
            'token_location': jwt_info.token_location,
            'token_name': jwt_info.token_name,
            'algorithm': jwt_info.algorithm,
            'expiration_info': jwt_info.expiration_info
        }
    
    def analyze_middleware_auth(self, route: APIRoute) -> dict:
        """
        Analyze middleware authentication for a route.
        
        Returns:
            Dict with middleware authentication details
        """
        middleware_info = analyze_middleware_auth(route)
        return {
            'has_auth_middleware': middleware_info.has_auth_middleware,
            'middleware_types': middleware_info.middleware_types,
            'ip_whitelist_check': middleware_info.ip_whitelist_check,
            'session_management': middleware_info.session_management,
            'token_refresh': middleware_info.token_refresh
        }
    
    def get_auth_documentation(self, route: APIRoute) -> dict:
        """
        Generate comprehensive authentication documentation for a route.
        
        Returns:
            Dict with complete authentication information
        """
        auth_doc = get_auth_documentation(route)
        return {
            'authentication_required': auth_doc.authentication_required,
            'roles_required': auth_doc.roles_required,
            'jwt_info': {
                'uses_jwt': auth_doc.jwt_info.uses_jwt,
                'token_location': auth_doc.jwt_info.token_location,
                'token_name': auth_doc.jwt_info.token_name,
                'algorithm': auth_doc.jwt_info.algorithm,
                'expiration_info': auth_doc.jwt_info.expiration_info
            },
            'middleware_info': {
                'has_auth_middleware': auth_doc.middleware_info.has_auth_middleware,
                'middleware_types': auth_doc.middleware_info.middleware_types,
                'ip_whitelist_check': auth_doc.middleware_info.ip_whitelist_check,
                'session_management': auth_doc.middleware_info.session_management,
                'token_refresh': auth_doc.middleware_info.token_refresh
            },
            'public_endpoint': auth_doc.public_endpoint,
            'private_endpoint': auth_doc.private_endpoint,
            'auth_description': auth_doc.auth_description
        }