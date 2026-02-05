"""
Handler functions for auth analysis operations.
"""

import ast
import inspect
from typing import List, Tuple, Callable
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_dependant

from .models import AuthInfo, JWTInfo, MiddlewareInfo, AuthDocumentation
from .constants import (
    AUTH_DEPENDENCIES, KNOWN_ROLES, PATH_INDICATORS, AUTH_KEYWORDS,
    JWT_DEFAULTS, MIDDLEWARE_DEFAULTS
)


def analyze_auth_requirements(route: APIRoute) -> Tuple[bool, List[str]]:
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
    if is_private_endpoint(route.path):
        auth_required = True
    
    # Analyze FastAPI dependencies
    dependant = get_dependant(path=route.path, call=route.endpoint)
    
    # Check dependencies for authentication requirements
    for dependency in dependant.dependencies:
        if dependency.call:
            auth_info = analyze_dependency_auth(dependency.call)
            if auth_info.requires_auth:
                auth_required = True
            if auth_info.roles:
                roles_required.extend(auth_info.roles)
    
    # Check route dependencies (defined at router level)
    if hasattr(route, 'dependencies') and route.dependencies:
        for dependency in route.dependencies:
            if hasattr(dependency, 'dependency'):
                auth_info = analyze_dependency_auth(dependency.dependency)
                if auth_info.requires_auth:
                    auth_required = True
                if auth_info.roles:
                    roles_required.extend(auth_info.roles)
    
    # Remove duplicates from roles
    roles_required = list(set(roles_required))
    
    return auth_required, roles_required


def is_private_endpoint(path: str) -> bool:
    """Check if endpoint path indicates private/authenticated access."""
    return any(indicator in path for indicator in PATH_INDICATORS.PRIVATE_INDICATORS)


def is_public_endpoint(path: str) -> bool:
    """Check if endpoint is public (doesn't require authentication)."""
    return any(indicator in path for indicator in PATH_INDICATORS.PUBLIC_INDICATORS)


def analyze_dependency_auth(dependency_func: Callable) -> AuthInfo:
    """
    Analyze a dependency function for authentication requirements.
    
    Returns:
        AuthInfo with requires_auth and roles information
    """
    auth_info = AuthInfo()
    
    if not dependency_func:
        return auth_info
    
    # Check function name for JWT/auth indicators
    func_name = getattr(dependency_func, '__name__', '')
    if any(indicator in func_name.lower() for indicator in AUTH_KEYWORDS.AUTH_KEYWORDS):
        auth_info.requires_auth = True
    
    # Check if it's the role_require function
    if func_name == 'role_require':
        auth_info.requires_auth = True
        # Try to extract roles from the function call
        roles = extract_roles_from_role_require(dependency_func)
        auth_info.roles = roles
    
    # Check if it's a partial function (role_require with arguments)
    if hasattr(dependency_func, 'func') and hasattr(dependency_func, 'args'):
        if getattr(dependency_func.func, '__name__', '') == 'role_require':
            auth_info.requires_auth = True
            # Extract roles from partial function arguments
            auth_info.roles = [str(arg) for arg in dependency_func.args if isinstance(arg, str)]
    
    # Check module path for authentication indicators
    module_path = getattr(dependency_func, '__module__', '')
    if 'auth' in module_path or 'jwt' in module_path:
        auth_info.requires_auth = True
    
    return auth_info


def extract_roles_from_role_require(func: Callable) -> List[str]:
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


def analyze_jwt_token_info(route: APIRoute) -> JWTInfo:
    """
    Extract JWT token information from route analysis.
    
    Returns:
        JWTInfo with JWT token configuration details
    """
    jwt_info = JWTInfo()
    
    if not route.endpoint:
        return jwt_info
    
    # Check if route uses JWT authentication
    auth_required, _ = analyze_auth_requirements(route)
    if not auth_required:
        return jwt_info
    
    # Analyze middleware and dependencies for JWT usage
    dependant = get_dependant(path=route.path, call=route.endpoint)
    
    for dependency in dependant.dependencies:
        if dependency.call:
            func_name = getattr(dependency.call, '__name__', '')
            if any(keyword in func_name.lower() for keyword in AUTH_KEYWORDS.JWT_KEYWORDS):
                jwt_info.uses_jwt = True
                
                # Determine token location based on dependency name
                if 'cookie' in func_name.lower():
                    jwt_info.token_location = 'cookie'
                    jwt_info.token_name = JWT_DEFAULTS.COOKIE_TOKEN_NAME
                elif 'header' in func_name.lower():
                    jwt_info.token_location = 'header'
                    jwt_info.token_name = JWT_DEFAULTS.HEADER_TOKEN_NAME
    
    # Add algorithm and expiration info from configuration
    if jwt_info.uses_jwt:
        jwt_info.algorithm = JWT_DEFAULTS.ALGORITHM
        jwt_info.expiration_info = JWT_DEFAULTS.EXPIRATION_INFO.copy()
    
    return jwt_info


def analyze_middleware_auth(route: APIRoute) -> MiddlewareInfo:
    """
    Analyze middleware authentication for a route.
    
    Returns:
        MiddlewareInfo with middleware authentication details
    """
    middleware_info = MiddlewareInfo()
    
    # Based on middleware.py analysis, all routes go through AuthUXASGIMiddleware
    middleware_info.has_auth_middleware = True
    middleware_info.middleware_types = MIDDLEWARE_DEFAULTS.MIDDLEWARE_TYPES.copy()
    
    # Check if route requires authentication (not public)
    if not is_public_endpoint(route.path):
        middleware_info.ip_whitelist_check = True
        middleware_info.session_management = True
        middleware_info.token_refresh = True
    
    return middleware_info


def generate_auth_description(auth_required: bool, roles_required: List[str], 
                            jwt_info: JWTInfo, middleware_info: MiddlewareInfo) -> str:
    """Generate human-readable authentication description."""
    if not auth_required:
        return "This endpoint is publicly accessible and does not require authentication."
    
    description_parts = []
    
    # Basic authentication requirement
    description_parts.append("This endpoint requires authentication.")
    
    # JWT token information
    if jwt_info.uses_jwt:
        if jwt_info.token_location == 'cookie':
            description_parts.append(
                f"Authentication is performed using JWT tokens stored in cookies "
                f"(token name: '{jwt_info.token_name}')."
            )
        elif jwt_info.token_location == 'header':
            description_parts.append(
                f"Authentication is performed using JWT tokens in the "
                f"'{jwt_info.token_name}' header."
            )
    
    # Role requirements
    if roles_required:
        if len(roles_required) == 1:
            description_parts.append(f"Requires '{roles_required[0]}' role.")
        else:
            roles_str = "', '".join(roles_required)
            description_parts.append(f"Requires one of the following roles: '{roles_str}'.")
    
    # Middleware information
    if middleware_info.ip_whitelist_check:
        description_parts.append(
            "IP whitelist checking is performed by the authentication middleware."
        )
    
    if middleware_info.token_refresh:
        description_parts.append(
            "Automatic token refresh is handled by the middleware if the access token is expired "
            "but the refresh token is still valid."
        )
    
    return " ".join(description_parts)


def get_auth_documentation(route: APIRoute) -> AuthDocumentation:
    """
    Generate comprehensive authentication documentation for a route.
    
    Returns:
        AuthDocumentation with complete authentication information
    """
    auth_required, roles_required = analyze_auth_requirements(route)
    jwt_info = analyze_jwt_token_info(route)
    middleware_info = analyze_middleware_auth(route)
    
    return AuthDocumentation(
        authentication_required=auth_required,
        roles_required=roles_required,
        jwt_info=jwt_info,
        middleware_info=middleware_info,
        public_endpoint=is_public_endpoint(route.path),
        private_endpoint=is_private_endpoint(route.path),
        auth_description=generate_auth_description(
            auth_required, roles_required, jwt_info, middleware_info
        )
    )