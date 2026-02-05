"""
Unit tests for AuthAnalyzer class.
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_dependant

from core.docs_generator.auth_analyzer import AuthAnalyzer
from core.docs_generator.auth_analyzer.handlers import (
    is_private_endpoint, is_public_endpoint, analyze_dependency_auth, 
    generate_auth_description
)
from core.docs_generator.auth_analyzer.models import JWTInfo, MiddlewareInfo
from core.utils.anything import Roles


class TestAuthAnalyzer:
    """Test cases for AuthAnalyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = AuthAnalyzer()
    
    def test_init(self):
        """Test AuthAnalyzer initialization."""
        # AuthAnalyzer should initialize without errors
        assert self.analyzer is not None
    
    def test_is_private_endpoint(self):
        """Test private endpoint detection."""
        # Test private endpoints
        assert is_private_endpoint('/private/users/profile')
        assert is_private_endpoint('/server/admin/settings')
        
        # Test public endpoints
        assert not is_private_endpoint('/public/users/login')
        assert not is_private_endpoint('/api/v1/public/health')
        assert not is_private_endpoint('/docs')
    
    def test_is_public_endpoint(self):
        """Test public endpoint detection."""
        # Test public endpoints
        assert is_public_endpoint('/public/users/login')
        assert is_public_endpoint('/api/v1/public/health')
        
        # Test private endpoints
        assert not is_public_endpoint('/private/users/profile')
        assert not is_public_endpoint('/server/admin/settings')
    
    def test_analyze_dependency_auth_jwt_dependency(self):
        """Test authentication analysis for JWT dependencies."""
        # Mock JWT dependency
        jwt_dep = Mock()
        jwt_dep.__name__ = 'jwt_cookie_dep'
        jwt_dep.__module__ = 'core.schemas.cookie_settings_schema'
        
        result = analyze_dependency_auth(jwt_dep)
        
        assert result.requires_auth is True
        assert result.roles == []
    
    def test_analyze_dependency_auth_role_require(self):
        """Test authentication analysis for role_require dependencies."""
        # Mock role_require dependency
        role_dep = Mock()
        role_dep.__name__ = 'role_require'
        role_dep.func = Mock()
        role_dep.func.__name__ = 'role_require'
        role_dep.args = [Roles.methodist, Roles.read_all]
        
        result = analyze_dependency_auth(role_dep)
        
        assert result.requires_auth is True
        assert Roles.methodist in result.roles
        assert Roles.read_all in result.roles
    
    def test_analyze_dependency_auth_no_auth(self):
        """Test authentication analysis for non-auth dependencies."""
        # Mock regular dependency
        regular_dep = Mock()
        regular_dep.__name__ = 'get_database'
        regular_dep.__module__ = 'core.data.postgre'
        
        result = analyze_dependency_auth(regular_dep)
        
        assert result.requires_auth is False
        assert result.roles == []
    
    def test_analyze_auth_requirements_private_path(self):
        """Test auth requirements analysis for private paths."""
        # Mock route with private path
        route = Mock(spec=APIRoute)
        route.path = '/private/users/profile'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'get_profile'
        
        # Mock get_dependant to return empty dependencies
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = []
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            auth_required, roles_required = self.analyzer.analyze_auth_requirements(route)
        
        assert auth_required is True
        assert roles_required == []
    
    def test_analyze_auth_requirements_with_jwt_dependency(self):
        """Test auth requirements analysis with JWT dependency."""
        # Mock route
        route = Mock(spec=APIRoute)
        route.path = '/api/users/profile'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'get_profile'
        route.dependencies = None
        
        # Mock dependency with JWT
        jwt_dep = Mock()
        jwt_dep.call = Mock()
        jwt_dep.call.__name__ = 'jwt_cookie_dep'
        
        # Mock get_dependant
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = [jwt_dep]
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            auth_required, roles_required = self.analyzer.analyze_auth_requirements(route)
        
        assert auth_required is True
        assert roles_required == []
    
    def test_analyze_auth_requirements_with_role_dependency(self):
        """Test auth requirements analysis with role dependency."""
        # Mock route
        route = Mock(spec=APIRoute)
        route.path = '/api/admin/settings'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'get_settings'
        
        # Mock route-level dependency with role requirement
        role_dep = Mock()
        role_dep.dependency = Mock()
        role_dep.dependency.__name__ = 'role_require'
        role_dep.dependency.func = Mock()
        role_dep.dependency.func.__name__ = 'role_require'
        role_dep.dependency.args = [Roles.methodist]
        
        route.dependencies = [role_dep]
        
        # Mock get_dependant
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = []
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            auth_required, roles_required = self.analyzer.analyze_auth_requirements(route)
        
        assert auth_required is True
        assert Roles.methodist in roles_required
    
    def test_analyze_auth_requirements_public_endpoint(self):
        """Test auth requirements analysis for public endpoints."""
        # Mock route with public path
        route = Mock(spec=APIRoute)
        route.path = '/public/users/login'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'login'
        route.dependencies = None
        
        # Mock get_dependant to return empty dependencies
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = []
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            auth_required, roles_required = self.analyzer.analyze_auth_requirements(route)
        
        assert auth_required is False
        assert roles_required == []
    
    def test_analyze_jwt_token_info_with_jwt(self):
        """Test JWT token information analysis."""
        # Mock route with JWT authentication
        route = Mock(spec=APIRoute)
        route.path = '/private/users/profile'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'get_profile'
        
        # Mock JWT dependency
        jwt_dep = Mock()
        jwt_dep.call = Mock()
        jwt_dep.call.__name__ = 'jwt_cookie_dep'
        
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = [jwt_dep]
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            jwt_info = self.analyzer.analyze_jwt_token_info(route)
        
        assert jwt_info['uses_jwt'] is True
        assert jwt_info['token_location'] == 'cookie'
        assert jwt_info['token_name'] == 'access_token'
        assert jwt_info['algorithm'] == 'RS256'
        assert 'access_token_ttl' in jwt_info['expiration_info']
    
    def test_analyze_jwt_token_info_no_jwt(self):
        """Test JWT token information analysis for non-JWT endpoints."""
        # Mock route without JWT
        route = Mock(spec=APIRoute)
        route.path = '/public/users/login'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'login'
        
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = []
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            jwt_info = self.analyzer.analyze_jwt_token_info(route)
        
        assert jwt_info['uses_jwt'] is False
        assert jwt_info['token_location'] is None
        assert jwt_info['token_name'] is None
    
    def test_analyze_middleware_auth(self):
        """Test middleware authentication analysis."""
        # Mock private route
        route = Mock(spec=APIRoute)
        route.path = '/private/users/profile'
        
        middleware_info = self.analyzer.analyze_middleware_auth(route)
        
        assert middleware_info['has_auth_middleware'] is True
        assert 'AuthUXASGIMiddleware' in middleware_info['middleware_types']
        assert 'LoggingTimeMiddleware' in middleware_info['middleware_types']
        assert middleware_info['ip_whitelist_check'] is True
        assert middleware_info['session_management'] is True
        assert middleware_info['token_refresh'] is True
    
    def test_analyze_middleware_auth_public(self):
        """Test middleware authentication analysis for public endpoints."""
        # Mock public route
        route = Mock(spec=APIRoute)
        route.path = '/public/users/login'
        
        middleware_info = self.analyzer.analyze_middleware_auth(route)
        
        assert middleware_info['has_auth_middleware'] is True
        assert middleware_info['ip_whitelist_check'] is False
        assert middleware_info['session_management'] is False
        assert middleware_info['token_refresh'] is False
    
    def test_get_auth_documentation_private_with_roles(self):
        """Test comprehensive auth documentation for private endpoint with roles."""
        # Mock route with authentication and roles
        route = Mock(spec=APIRoute)
        route.path = '/private/admin/settings'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'get_settings'
        
        # Mock role dependency
        role_dep = Mock()
        role_dep.dependency = Mock()
        role_dep.dependency.__name__ = 'role_require'
        role_dep.dependency.func = Mock()
        role_dep.dependency.func.__name__ = 'role_require'
        role_dep.dependency.args = [Roles.methodist]
        
        route.dependencies = [role_dep]
        
        # Mock JWT dependency
        jwt_dep = Mock()
        jwt_dep.call = Mock()
        jwt_dep.call.__name__ = 'jwt_cookie_dep'
        
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = [jwt_dep]
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            auth_doc = self.analyzer.get_auth_documentation(route)
        
        assert auth_doc['authentication_required'] is True
        assert Roles.methodist in auth_doc['roles_required']
        assert auth_doc['jwt_info']['uses_jwt'] is True
        assert auth_doc['middleware_info']['has_auth_middleware'] is True
        assert auth_doc['public_endpoint'] is False
        assert auth_doc['private_endpoint'] is True
        assert 'requires authentication' in auth_doc['auth_description'].lower()
        assert 'methodist' in auth_doc['auth_description'].lower()
    
    def test_get_auth_documentation_public(self):
        """Test comprehensive auth documentation for public endpoint."""
        # Mock public route
        route = Mock(spec=APIRoute)
        route.path = '/public/users/login'
        route.endpoint = Mock()
        route.endpoint.__name__ = 'login'
        route.dependencies = None
        
        with pytest.MonkeyPatch().context() as m:
            mock_dependant = Mock()
            mock_dependant.dependencies = []
            m.setattr('core.docs_generator.auth_analyzer.handlers.get_dependant', 
                     lambda path, call: mock_dependant)
            
            auth_doc = self.analyzer.get_auth_documentation(route)
        
        assert auth_doc['authentication_required'] is False
        assert auth_doc['roles_required'] == []
        assert auth_doc['jwt_info']['uses_jwt'] is False
        assert auth_doc['public_endpoint'] is True
        assert auth_doc['private_endpoint'] is False
        assert 'publicly accessible' in auth_doc['auth_description'].lower()
    
    def test_generate_auth_description_no_auth(self):
        """Test auth description generation for non-authenticated endpoints."""
        jwt_info = JWTInfo(uses_jwt=False)
        middleware_info = MiddlewareInfo(ip_whitelist_check=False)
        
        description = generate_auth_description(
            auth_required=False,
            roles_required=[],
            jwt_info=jwt_info,
            middleware_info=middleware_info
        )
        
        assert 'publicly accessible' in description.lower()
        assert 'does not require authentication' in description.lower()
    
    def test_generate_auth_description_with_auth_and_roles(self):
        """Test auth description generation for authenticated endpoints with roles."""
        jwt_info = JWTInfo(
            uses_jwt=True,
            token_location='cookie',
            token_name='access_token'
        )
        middleware_info = MiddlewareInfo(
            ip_whitelist_check=True,
            token_refresh=True
        )
        
        description = generate_auth_description(
            auth_required=True,
            roles_required=[Roles.methodist, Roles.read_all],
            jwt_info=jwt_info,
            middleware_info=middleware_info
        )
        
        assert 'requires authentication' in description.lower()
        assert 'jwt tokens' in description.lower()
        assert 'cookie' in description.lower()
        assert 'access_token' in description.lower()
        assert 'methodist' in description.lower()
        assert 'read_all' in description.lower()
        assert 'ip whitelist' in description.lower()
        assert 'token refresh' in description.lower()
    
    def test_generate_auth_description_single_role(self):
        """Test auth description generation for single role requirement."""
        jwt_info = JWTInfo(uses_jwt=False)
        middleware_info = MiddlewareInfo(ip_whitelist_check=False, token_refresh=False)
        
        description = generate_auth_description(
            auth_required=True,
            roles_required=[Roles.methodist],
            jwt_info=jwt_info,
            middleware_info=middleware_info
        )
        
        assert 'requires authentication' in description.lower()
        assert f"requires '{Roles.methodist}' role" in description.lower()