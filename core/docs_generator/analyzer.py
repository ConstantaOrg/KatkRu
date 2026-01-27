"""
Endpoint analyzer for extracting API information.
"""

import inspect
import ast
from dataclasses import dataclass
from typing import List, Optional, Callable, Any, get_type_hints, get_origin, get_args
from fastapi.routing import APIRoute
from fastapi.params import Query, Path, Header, Body, Depends
from fastapi.dependencies.utils import get_dependant
from pydantic import BaseModel

from .models import EndpointInfo, Parameter, Dependency, DependencyChain
from .dependency_analyzer import DependencyAnalyzer
from .auth_analyzer import AuthAnalyzer


class EndpointAnalyzer:
    """Analyzes FastAPI endpoints and their dependencies."""
    
    def __init__(self):
        self.analyzed_functions = set()
        self.dependency_analyzer = DependencyAnalyzer()
        self.auth_analyzer = AuthAnalyzer()
    
    def extract_route_info(self, route: APIRoute) -> 'RouteInfo':
        """Extract basic information from a FastAPI route."""
        # Get HTTP methods for this route
        methods = list(route.methods)
        # Remove OPTIONS method as it's automatically added by FastAPI
        if 'OPTIONS' in methods:
            methods.remove('OPTIONS')
        
        # Get the primary method (usually there's only one)
        method = methods[0] if methods else 'GET'
        
        # Extract path
        path = route.path
        
        # Get the endpoint function
        endpoint_func = route.endpoint
        
        # Get function name
        func_name = endpoint_func.__name__ if endpoint_func else 'unknown'
        
        # Get summary and description from route or function docstring
        summary = route.summary
        description = route.description
        
        if not description and endpoint_func and endpoint_func.__doc__:
            description = endpoint_func.__doc__.strip()
        
        return RouteInfo(
            path=path,
            method=method,
            function=endpoint_func,
            name=func_name,
            summary=summary,
            description=description
        )
    
    def extract_parameters(self, route: APIRoute) -> List[Parameter]:
        """Extract parameters from a FastAPI route."""
        parameters = []
        
        if not route.endpoint:
            return parameters
        
        # Get the dependant information from FastAPI
        dependant = get_dependant(path=route.path, call=route.endpoint)
        
        # Extract path parameters
        for path_param in dependant.path_params:
            param_info = self._create_parameter_info(
                path_param, 'path', required=True
            )
            if param_info:
                parameters.append(param_info)
        
        # Extract query parameters
        for query_param in dependant.query_params:
            param_info = self._create_parameter_info(
                query_param, 'query', required=query_param.required
            )
            if param_info:
                parameters.append(param_info)
        
        # Extract header parameters
        for header_param in dependant.header_params:
            param_info = self._create_parameter_info(
                header_param, 'header', required=header_param.required
            )
            if param_info:
                parameters.append(param_info)
        
        # Extract body parameters
        if dependant.body_params:
            for body_param in dependant.body_params:
                param_info = self._create_parameter_info(
                    body_param, 'body', required=body_param.required
                )
                if param_info:
                    parameters.append(param_info)
        
        return parameters
    
    def _create_parameter_info(self, param, location: str, required: bool) -> Optional[Parameter]:
        """Create Parameter object from FastAPI parameter info."""
        try:
            name = param.alias or param.name
            param_type = self._get_type_string(param.type_)
            description = getattr(param, 'description', '') or ''
            
            return Parameter(
                name=name,
                type=param_type,
                required=required,
                description=description,
                location=location
            )
        except Exception:
            # If we can't extract parameter info, skip it
            return None
    
    def analyze_endpoint(self, route: APIRoute) -> EndpointInfo:
        """Analyze a complete endpoint and return EndpointInfo."""
        route_info = self.extract_route_info(route)
        parameters = self.extract_parameters(route)
        
        # Determine module from the route path or function module
        module = self._determine_module(route_info.path, route_info.function)
        
        # Check authentication requirements using AuthAnalyzer
        auth_required, roles_required = self.auth_analyzer.analyze_auth_requirements(route)
        
        # Extract request and response schemas
        request_schema = self.get_request_schema(route_info.function)
        
        # Try to get response schema from route first, then from function annotation
        response_schema = self.get_response_schema_from_route(route)
        if not response_schema:
            response_schema = self.get_response_schema(route_info.function)
        
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
    
    def _determine_module(self, path: str, function: Callable) -> str:
        """Determine which module an endpoint belongs to."""
        # Extract module from path
        if '/specialties' in path:
            return 'specialties'
        elif '/groups' in path:
            return 'groups'
        elif '/teachers' in path:
            return 'teachers'
        elif '/disciplines' in path:
            return 'disciplines'
        elif '/timetable' in path:
            return 'timetable'
        elif '/users' in path:
            return 'users'
        elif '/n8n' in path:
            return 'n8n_ui'
        elif '/search' in path:
            return 'elastic_search'
        elif '/ttable_versions' in path:
            return 'ttable_versions'
        
        # Fallback: try to extract from function module
        if function and hasattr(function, '__module__'):
            module_path = function.__module__
            if 'specialties' in module_path:
                return 'specialties'
            elif 'groups' in module_path:
                return 'groups'
            elif 'teachers' in module_path:
                return 'teachers'
            elif 'disciplines' in module_path:
                return 'disciplines'
            elif 'timetable' in module_path:
                return 'timetable'
            elif 'users' in module_path:
                return 'users'
            elif 'n8n' in module_path:
                return 'n8n_ui'
            elif 'elastic_search' in module_path:
                return 'elastic_search'
        
        return 'miscellaneous'
    
    def _get_type_string(self, type_annotation) -> str:
        """Convert type annotation to string representation."""
        if type_annotation is None:
            return 'Any'
        
        # Handle basic types
        if hasattr(type_annotation, '__name__'):
            return type_annotation.__name__
        
        # Handle generic types like List[str], Optional[int], etc.
        origin = get_origin(type_annotation)
        if origin is not None:
            args = get_args(type_annotation)
            if origin is list:
                if args:
                    return f"List[{self._get_type_string(args[0])}]"
                return "List"
            elif origin is dict:
                if len(args) >= 2:
                    return f"Dict[{self._get_type_string(args[0])}, {self._get_type_string(args[1])}]"
                return "Dict"
            elif hasattr(origin, '__name__'):
                return origin.__name__
        
        # Fallback to string representation
        return str(type_annotation)
    
    def analyze_dependencies(self, func: Callable) -> List[Dependency]:
        """Analyze dependencies of a function."""
        return self.dependency_analyzer.trace_function_calls(func)
    
    def get_request_schema(self, func: Callable) -> Optional[BaseModel]:
        """Extract request schema from function annotations."""
        if not func:
            return None
        
        try:
            # Get function signature
            sig = inspect.signature(func)
            
            # Look for parameters that are Pydantic models
            for param_name, param in sig.parameters.items():
                # Skip common FastAPI dependencies
                if param_name in ['request', 'db', '_', 'response']:
                    continue
                
                # Check if parameter annotation is a Pydantic model
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    if self._is_pydantic_model(param.annotation):
                        return param.annotation
                    
                    # Handle Optional types
                    origin = get_origin(param.annotation)
                    if origin is not None:
                        args = get_args(param.annotation)
                        for arg in args:
                            if self._is_pydantic_model(arg):
                                return arg
            
            return None
        except Exception:
            return None
    
    def get_response_schema(self, func: Callable) -> Optional[BaseModel]:
        """Extract response schema from function annotations."""
        if not func:
            return None
        
        try:
            # Get function signature and return annotation
            sig = inspect.signature(func)
            return_annotation = sig.return_annotation
            
            if return_annotation and return_annotation != inspect.Parameter.empty:
                # Handle direct Pydantic model
                if self._is_pydantic_model(return_annotation):
                    return return_annotation
                
                # Handle generic types like List[Model], Optional[Model], etc.
                origin = get_origin(return_annotation)
                if origin is not None:
                    args = get_args(return_annotation)
                    for arg in args:
                        if self._is_pydantic_model(arg):
                            return arg
            
            return None
        except Exception:
            return None
    
    def get_response_schema_from_route(self, route: APIRoute) -> Optional[BaseModel]:
        """Extract response schema from FastAPI route response_model."""
        try:
            if hasattr(route, 'response_model') and route.response_model:
                if self._is_pydantic_model(route.response_model):
                    return route.response_model
            return None
        except Exception:
            return None
    
    def _is_pydantic_model(self, annotation) -> bool:
        """Check if an annotation is a Pydantic model."""
        try:
            # Check if it's a class and inherits from BaseModel
            if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                return True
            return False
        except (TypeError, AttributeError):
            return False
    
    def analyze_schema_validation(self, model: BaseModel) -> dict:
        """Analyze validation rules from a Pydantic model."""
        if not model or not self._is_pydantic_model(model):
            return {}
        
        try:
            # Get model schema
            schema = model.model_json_schema() if hasattr(model, 'model_json_schema') else {}
            
            validation_info = {
                'title': schema.get('title', model.__name__),
                'description': schema.get('description', ''),
                'properties': schema.get('properties', {}),
                'required': schema.get('required', []),
                'type': schema.get('type', 'object')
            }
            
            return validation_info
        except Exception:
            return {
                'title': model.__name__ if hasattr(model, '__name__') else 'Unknown',
                'description': '',
                'properties': {},
                'required': [],
                'type': 'object'
            }
    
    def trace_dependency_chain(self, endpoint: EndpointInfo) -> DependencyChain:
        """Trace the complete dependency chain for an endpoint."""
        return self.dependency_analyzer.trace_dependency_chain(endpoint)


@dataclass
class RouteInfo:
    """Basic route information extracted from FastAPI."""
    path: str
    method: str
    function: Callable
    name: str
    summary: Optional[str] = None
    description: Optional[str] = None