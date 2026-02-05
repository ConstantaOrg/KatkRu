"""
Main endpoint analyzer class.
"""

from typing import List
from fastapi.routing import APIRoute

from .models import RouteInfo
from .handlers import (
    extract_route_info, extract_parameters, determine_module,
    get_request_schema, get_response_schema, get_response_schema_from_route,
    analyze_schema_validation
)
from ..models import EndpointInfo, DependencyChain
from ..dependency_analyzer import DependencyAnalyzer
from ..auth_analyzer import AuthAnalyzer


class EndpointAnalyzer:
    """Analyzes FastAPI endpoints and their dependencies."""
    
    def __init__(self):
        self.analyzed_functions = set()
        self.dependency_analyzer = DependencyAnalyzer()
        self.auth_analyzer = AuthAnalyzer()
    
    def extract_route_info(self, route: APIRoute) -> RouteInfo:
        """Extract basic information from a FastAPI route."""
        return extract_route_info(route)
    
    def extract_parameters(self, route: APIRoute) -> List:
        """Extract parameters from a FastAPI route."""
        return extract_parameters(route)
    
    def analyze_endpoint(self, route: APIRoute) -> EndpointInfo:
        """Analyze a complete endpoint and return EndpointInfo."""
        route_info = self.extract_route_info(route)
        parameters = self.extract_parameters(route)
        
        # Determine module from the route path or function module
        module = determine_module(route_info.path, route_info.function)
        
        # Check authentication requirements using AuthAnalyzer
        auth_required, roles_required = self.auth_analyzer.analyze_auth_requirements(route)
        
        # Extract request and response schemas
        request_schema = get_request_schema(route_info.function)
        
        # Try to get response schema from route first, then from function annotation
        response_schema = get_response_schema_from_route(route)
        if not response_schema:
            response_schema = get_response_schema(route_info.function)
        
        # Analyze dependencies using DependencyAnalyzer
        dependencies = []
        if route_info.function:
            # Trace function dependencies
            func_deps = self.dependency_analyzer.trace_function_calls(route_info.function)
            dependencies.extend(func_deps)
            
            # Analyze FastAPI dependencies
            fastapi_deps = self.dependency_analyzer.analyze_fastapi_dependencies(route)
            dependencies.extend(fastapi_deps)
        
        # Create EndpointInfo object
        return EndpointInfo(
            path=route_info.path,
            method=route_info.method,
            function_name=route_info.name,
            module=module,
            description=route_info.description or route_info.summary or '',
            parameters=parameters,
            request_body=request_schema,
            response_model=response_schema,
            auth_required=auth_required,
            roles_required=roles_required,
            dependencies=dependencies
        )
    
    def analyze_dependencies(self, func) -> List:
        """Analyze dependencies of a function."""
        return self.dependency_analyzer.trace_function_calls(func)
    
    def get_request_schema(self, func):
        """Extract request schema from function annotations."""
        return get_request_schema(func)
    
    def get_response_schema(self, func):
        """Extract response schema from function annotations."""
        return get_response_schema(func)
    
    def get_response_schema_from_route(self, route: APIRoute):
        """Extract response schema from FastAPI route response_model."""
        return get_response_schema_from_route(route)
    
    def analyze_schema_validation(self, model) -> dict:
        """Analyze validation rules from a Pydantic model."""
        return analyze_schema_validation(model)
    
    def trace_dependency_chain(self, endpoint: EndpointInfo) -> DependencyChain:
        """Trace the complete dependency chain for an endpoint."""
        return self.dependency_analyzer.trace_dependency_chain(endpoint)