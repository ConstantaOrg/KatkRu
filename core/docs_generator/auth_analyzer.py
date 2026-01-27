"""
Authentication and authorization analyzer for API endpoints.
"""

import ast
import inspect
from typing import List, Optional, Tuple, Callable, Any
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_dependant

from core.utils.anything import Roles


class AuthAnalyzer:
    """Analyzes authentication and authorization requirements for API endpoints."""
    
    def __init__(self):
        self.known_auth_dependencies = {
            'JWTCookieDep',
            'jwt_cookie_dep',
            'role_require'
        }
        self.known_roles = {
            Roles.methodist,
            Roles.read_all
        }
    
    def analyze_auth_requirements(self, route: APIRoute) -> Tuple[bool, List[str]]:
        """
        Analyze authentication and authorization requirements for a route.
        
        Returns:
            Tuple of (auth_required: bool, roles_required: List[str])
        """
        auth_required = False
        roles_required = []
        
        if not route.endpoint:
            return auth_required, roles_required
        
        # Check path-based authentication requirements
        if self._is_private_endpoint(route.path):
            auth_required = True
        
        # Analyze FastAPI dependencies
        dependant = get_dependant(path=route.path, call=route.endpoint)
        
        # Check dependencies for authentication requirements
        for dependency in dependant.dependencies:
            if dependency.call:
                auth_info = self._analyze_dependency_auth(dependency.call)
                if auth_info['requires_auth']:
                    auth_required = True
                if auth_info['roles']:
                    roles_required.extend(auth_info['roles'])
        
        # Check route dependencies (defined at router level)
        if hasattr(route, 'dependencies') and route.dependencies:
            for dependency in route.dependencies:
                if hasattr(dependency, 'dependency'):
                    auth_info = self._analyze_dependency_auth(dependency.dependency)
                    if auth_info['requires_auth']:
                        auth_required = True
                    if auth_info['roles']:
                        roles_required.extend(auth_info['roles'])
        
        # Remove duplicates from roles
        roles_required = list(set(roles_required))
        
        return auth_required, roles_required
    
    def _is_private_endpoint(self, path: str) -> bool:
        """Check if endpoint path indicates private/authenticated access."""
        private_indicators = ['/private/', '/server/']
        return any(indicator in path for indicator in private_indicators)
    
    def _analyze_dependency_auth(self, dependency_func: Callable) -> dict:
        """
        Analyze a dependency function for authentication requirements.
        
        Returns:
            Dict with 'requires_auth' (bool) and 'roles' (List[str])
        """
        result = {'requires_auth': False, 'roles': []}
        
        if not dependency_func:
            return result
        
        # Check function name for JWT/auth indicators
        func_name = getattr(dependency_func, '__name__', '')
        if any(indicator in func_name.lower() for indicator in ['jwt', 'auth', 'cookie']):
            result['requires_auth'] = True
        
        # Check if it's the role_require function
        if func_name == 'role_require':
            result['requires_auth'] = True
            # Try to extract roles from the function call
            roles = self._extract_roles_from_role_require(dependency_func)
            result['roles'] = roles
        
        # Check if it's a partial function (role_require with arguments)
        if hasattr(dependency_func, 'func') and hasattr(dependency_func, 'args'):
            if getattr(dependency_func.func, '__name__', '') == 'role_require':
                result['requires_auth'] = True
                # Extract roles from partial function arguments
                result['roles'] = [str(arg) for arg in dependency_func.args if isinstance(arg, str)]
        
        # Check module path for authentication indicators
        module_path = getattr(dependency_func, '__module__', '')
        if 'auth' in module_path or 'jwt' in module_path:
            result['requires_auth'] = True
        
        return result
    
    def _extract_roles_from_role_require(self, func: Callable) -> List[str]:
        """Extract role requirements from role_require function calls."""
        roles = []
        
        try:
            # Try to get the source code and parse it
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            # Look for role_require calls in the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if (isinstance(node.func, ast.Name) and 
                        node.func.id == 'role_require'):
                        # Extract string arguments
                        for arg in node.args:
                            if isinstance(arg, ast.Str):
                                roles.append(arg.s)
                            elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                roles.append(arg.value)
                            elif isinstance(arg, ast.Attribute):
                                # Handle Roles.methodist, Roles.read_all
                                if (isinstance(arg.value, ast.Name) and 
                                    arg.value.id == 'Roles'):
                                    roles.append(arg.attr)
        except (OSError, TypeError, SyntaxError):
            # If we can't parse the source, fall back to known roles
            pass
        
        return roles
    
    def analyze_jwt_token_info(self, route: APIRoute) -> dict:
        """
        Extract JWT token information from route analysis.
        
        Returns:
            Dict with JWT token configuration details
        """
        jwt_info = {
            'uses_jwt': False,
            'token_location': None,  # 'cookie', 'header', 'query'
            'token_name': None,
            'algorithm': None,
            'expiration_info': {}
        }
        
        if not route.endpoint:
            return jwt_info
        
        # Check if route uses JWT authentication
        auth_required, _ = self.analyze_auth_requirements(route)
        if not auth_required:
            return jwt_info
        
        # Analyze middleware and dependencies for JWT usage
        dependant = get_dependant(path=route.path, call=route.endpoint)
        
        for dependency in dependant.dependencies:
            if dependency.call:
                func_name = getattr(dependency.call, '__name__', '')
                if 'jwt' in func_name.lower() or 'cookie' in func_name.lower():
                    jwt_info['uses_jwt'] = True
                    
                    # Determine token location based on dependency name
                    if 'cookie' in func_name.lower():
                        jwt_info['token_location'] = 'cookie'
                        jwt_info['token_name'] = 'access_token'  # Based on middleware analysis
                    elif 'header' in func_name.lower():
                        jwt_info['token_location'] = 'header'
                        jwt_info['token_name'] = 'Authorization'
        
        # Add algorithm and expiration info from configuration
        if jwt_info['uses_jwt']:
            jwt_info['algorithm'] = 'RS256'  # Based on jwt_factory.py analysis
            jwt_info['expiration_info'] = {
                'access_token_ttl': 'Configurable via env.JWTs.ttl_aT',
                'refresh_token_ttl': 'Configurable via env.JWTs.ttl_rT',
                'websocket_token_ttl': 'Configurable via env.JWTs.ttl_wT'
            }
        
        return jwt_info
    
    def analyze_middleware_auth(self, route: APIRoute) -> dict:
        """
        Analyze middleware authentication for a route.
        
        Returns:
            Dict with middleware authentication details
        """
        middleware_info = {
            'has_auth_middleware': False,
            'middleware_types': [],
            'ip_whitelist_check': False,
            'session_management': False,
            'token_refresh': False
        }
        
        # Based on middleware.py analysis, all routes go through AuthUXASGIMiddleware
        middleware_info['has_auth_middleware'] = True
        middleware_info['middleware_types'] = ['AuthUXASGIMiddleware', 'LoggingTimeMiddleware']
        
        # Check if route requires authentication (not public)
        if not self._is_public_endpoint(route.path):
            middleware_info['ip_whitelist_check'] = True
            middleware_info['session_management'] = True
            middleware_info['token_refresh'] = True
        
        return middleware_info
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (doesn't require authentication)."""
        public_indicators = ['/public/', '/api/v1/public']
        return any(indicator in path for indicator in public_indicators)
    
    def get_auth_documentation(self, route: APIRoute) -> dict:
        """
        Generate comprehensive authentication documentation for a route.
        
        Returns:
            Dict with complete authentication information
        """
        auth_required, roles_required = self.analyze_auth_requirements(route)
        jwt_info = self.analyze_jwt_token_info(route)
        middleware_info = self.analyze_middleware_auth(route)
        
        return {
            'authentication_required': auth_required,
            'roles_required': roles_required,
            'jwt_info': jwt_info,
            'middleware_info': middleware_info,
            'public_endpoint': self._is_public_endpoint(route.path),
            'private_endpoint': self._is_private_endpoint(route.path),
            'auth_description': self._generate_auth_description(
                auth_required, roles_required, jwt_info, middleware_info
            )
        }
    
    def _generate_auth_description(self, auth_required: bool, roles_required: List[str], 
                                 jwt_info: dict, middleware_info: dict) -> str:
        """Generate human-readable authentication description."""
        if not auth_required:
            return "This endpoint is publicly accessible and does not require authentication."
        
        description_parts = []
        
        # Basic authentication requirement
        description_parts.append("This endpoint requires authentication.")
        
        # JWT token information
        if jwt_info['uses_jwt']:
            if jwt_info['token_location'] == 'cookie':
                description_parts.append(
                    f"Authentication is performed using JWT tokens stored in cookies "
                    f"(token name: '{jwt_info['token_name']}')."
                )
            elif jwt_info['token_location'] == 'header':
                description_parts.append(
                    f"Authentication is performed using JWT tokens in the "
                    f"'{jwt_info['token_name']}' header."
                )
        
        # Role requirements
        if roles_required:
            if len(roles_required) == 1:
                description_parts.append(f"Requires '{roles_required[0]}' role.")
            else:
                roles_str = "', '".join(roles_required)
                description_parts.append(f"Requires one of the following roles: '{roles_str}'.")
        
        # Middleware information
        if middleware_info['ip_whitelist_check']:
            description_parts.append(
                "IP whitelist checking is performed by the authentication middleware."
            )
        
        if middleware_info['token_refresh']:
            description_parts.append(
                "Automatic token refresh is handled by the middleware if the access token is expired "
                "but the refresh token is still valid."
            )
        
        return " ".join(description_parts)