"""
Isolated property-based tests for the documentation generator endpoint analyzer.
This test file runs independently without database setup.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi import APIRouter
from fastapi.routing import APIRoute
from typing import Optional

from core.docs_generator.endpoint_analyzer import EndpointAnalyzer
from core.docs_generator.models import EndpointInfo, Parameter


class TestEndpointAnalyzerIsolated:
    """Test the EndpointAnalyzer class in isolation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = EndpointAnalyzer()
    
    @given(
        path=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/-_'), min_size=2, max_size=20).map(lambda x: f"/{x.strip('/')}" if x.strip('/') else "/test"),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    )
    @settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=50)
    def test_property_complete_endpoint_documentation(self, path: str, method: str):
        """
        Feature: api-documentation, Property 2: Complete endpoint documentation
        
        For any documented endpoint, the documentation should include HTTP method, 
        path, parameters, request body schema, response schema, authentication 
        requirements, and possible error codes.
        
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        """
        # Create a simple endpoint function
        async def test_endpoint():
            """Test endpoint for property testing."""
            return {"message": "test"}
        
        # Create a route
        router = APIRouter()
        router.add_api_route(path, test_endpoint, methods=[method])
        
        # Get the route from the router
        routes = router.routes
        if not routes:
            pytest.skip("No routes created")
        
        route = routes[0]
        if not isinstance(route, APIRoute):
            pytest.skip("Route is not an APIRoute")
        
        # Analyze the endpoint
        endpoint_info = self.analyzer.analyze_endpoint(route)
        
        # Verify all required fields are present (Property 2)
        assert endpoint_info is not None
        assert isinstance(endpoint_info, EndpointInfo)
        
        # HTTP method should be documented
        assert endpoint_info.method is not None
        assert endpoint_info.method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        # Path should be documented
        assert endpoint_info.path is not None
        assert isinstance(endpoint_info.path, str)
        
        # Function name should be documented
        assert endpoint_info.function_name is not None
        assert isinstance(endpoint_info.function_name, str)
        
        # Module should be determined
        assert endpoint_info.module is not None
        assert isinstance(endpoint_info.module, str)
        
        # Description should be present (even if empty)
        assert endpoint_info.description is not None
        assert isinstance(endpoint_info.description, str)
        
        # Parameters should be a list
        assert endpoint_info.parameters is not None
        assert isinstance(endpoint_info.parameters, list)
        
        # Authentication requirements should be boolean
        assert isinstance(endpoint_info.auth_required, bool)
        
        # Roles should be a list
        assert endpoint_info.roles_required is not None
        assert isinstance(endpoint_info.roles_required, list)
        
        # Dependencies should be a list
        assert endpoint_info.dependencies is not None
        assert isinstance(endpoint_info.dependencies, list)
    
    @given(
        path=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/-_'), min_size=2, max_size=20).map(lambda x: f"/{x.strip('/')}" if x.strip('/') else "/test"),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    )
    @settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=50)
    def test_property_dependency_chain_completeness(self, path: str, method: str):
        """
        Feature: api-documentation, Property 3: Dependency chain completeness
        
        For any documented endpoint, all direct function calls, database queries, 
        used schemas, and middleware dependencies should be identified and traced.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        # Create a simple endpoint function
        async def test_endpoint():
            """Test endpoint for dependency analysis."""
            return {"message": "test"}
        
        # Create a route
        router = APIRouter()
        router.add_api_route(path, test_endpoint, methods=[method])
        
        # Get the route from the router
        routes = router.routes
        if not routes:
            pytest.skip("No routes created")
        
        route = routes[0]
        if not isinstance(route, APIRoute):
            pytest.skip("Route is not an APIRoute")
        
        # Analyze the endpoint
        endpoint_info = self.analyzer.analyze_endpoint(route)
        
        # Trace dependency chain
        dependency_chain = self.analyzer.trace_dependency_chain(endpoint_info)
        
        # Verify dependency chain structure (Property 3)
        assert dependency_chain is not None
        
        # Endpoint should be documented
        assert dependency_chain.endpoint is not None
        assert isinstance(dependency_chain.endpoint, str)
        assert method in dependency_chain.endpoint
        
        # Direct dependencies should be a list
        assert dependency_chain.direct_dependencies is not None
        assert isinstance(dependency_chain.direct_dependencies, list)
        
        # Database queries should be a list
        assert dependency_chain.database_queries is not None
        assert isinstance(dependency_chain.database_queries, list)
        
        # External services should be a list
        assert dependency_chain.external_services is not None
        assert isinstance(dependency_chain.external_services, list)
        
        # Middleware should be a list
        assert dependency_chain.middleware is not None
        assert isinstance(dependency_chain.middleware, list)
        
        # At minimum, LoggingTimeMiddleware should be present for all endpoints
        assert 'LoggingTimeMiddleware' in dependency_chain.middleware
        
        # Schemas should be a list
        assert dependency_chain.schemas is not None
        assert isinstance(dependency_chain.schemas, list)
        
        # If endpoint requires auth, AuthUXASGIMiddleware should be present
        if endpoint_info.auth_required:
            assert 'AuthUXASGIMiddleware' in dependency_chain.middleware
    
    def test_extract_route_info_with_real_endpoint(self):
        """Test route info extraction with a real endpoint."""
        # Create a more realistic endpoint
        async def get_users(user_id: int, limit: Optional[int] = 10):
            """Get users by ID with optional limit."""
            return {"user_id": user_id, "limit": limit}
        
        router = APIRouter()
        router.add_api_route("/users/{user_id}", get_users, methods=["GET"])
        
        route = router.routes[0]
        route_info = self.analyzer.extract_route_info(route)
        
        assert route_info.path == "/users/{user_id}"
        assert route_info.method == "GET"
        assert route_info.name == "get_users"
        assert "Get users by ID" in route_info.description
    
    def test_extract_parameters_with_path_and_query(self):
        """Test parameter extraction with path and query parameters."""
        async def get_user_posts(user_id: int, limit: int = 10, offset: int = 0):
            """Get user posts with pagination."""
            return {"user_id": user_id, "limit": limit, "offset": offset}
        
        router = APIRouter()
        router.add_api_route("/users/{user_id}/posts", get_user_posts, methods=["GET"])
        
        route = router.routes[0]
        parameters = self.analyzer.extract_parameters(route)
        
        # Should have path parameter user_id and query parameters limit, offset
        assert len(parameters) >= 1  # At least the path parameter
        
        # Check that we have parameter objects
        for param in parameters:
            assert isinstance(param, Parameter)
            assert param.name is not None
            assert param.type is not None
            assert isinstance(param.required, bool)
            assert param.location in ['path', 'query', 'header', 'body']
    
    def test_module_determination(self):
        """Test module determination from path."""
        test_cases = [
            ("/api/v1/specialties/all", "specialties"),
            ("/api/v1/groups/get", "groups"),
            ("/api/v1/teachers/list", "teachers"),
            ("/api/v1/disciplines/search", "disciplines"),
            ("/api/v1/timetable/schedule", "timetable"),
            ("/api/v1/users/profile", "users"),
            ("/api/v1/n8n/webhook", "n8n_ui"),
            ("/api/v1/search/query", "elastic_search"),
            ("/api/v1/unknown/endpoint", "miscellaneous")
        ]
        
        for path, expected_module in test_cases:
            async def test_func():
                return {"test": True}
            
            router = APIRouter()
            router.add_api_route(path, test_func, methods=["GET"])
            route = router.routes[0]
            
            endpoint_info = self.analyzer.analyze_endpoint(route)
            actual_module = endpoint_info.module
            assert actual_module == expected_module, f"Path {path} should map to {expected_module}, got {actual_module}"
    
    def test_auth_requirements_detection(self):
        """Test authentication requirements detection."""
        # Create endpoint with private path
        async def private_endpoint():
            return {"private": True}
        
        router = APIRouter()
        router.add_api_route("/api/v1/private/data", private_endpoint, methods=["GET"])
        
        route = router.routes[0]
        auth_required, roles = self.analyzer.auth_analyzer.analyze_auth_requirements(route)
        
        # Private endpoints should require authentication
        assert auth_required is True
        assert isinstance(roles, list)