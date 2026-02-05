"""
Handler functions for endpoint analysis operations.
"""

import inspect
from typing import List, Optional, Callable, get_type_hints, get_origin, get_args
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_dependant
from pydantic import BaseModel

from .models import RouteInfo
from .constants import MODULE_MAPPINGS, PARAMETER_TYPES, COMMON_PARAMETERS
from ..models import Parameter


def extract_route_info(route: APIRoute) -> RouteInfo:
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


def extract_parameters(route: APIRoute) -> List[Parameter]:
    """Extract parameters from a FastAPI route."""
    parameters = []
    
    if not route.endpoint:
        return parameters
    
    # Get the dependant information from FastAPI
    dependant = get_dependant(path=route.path, call=route.endpoint)
    
    # Extract path parameters
    for path_param in dependant.path_params:
        param_info = create_parameter_info(
            path_param, PARAMETER_TYPES.PATH, required=True
        )
        if param_info:
            parameters.append(param_info)
    
    # Extract query parameters
    for query_param in dependant.query_params:
        param_info = create_parameter_info(
            query_param, PARAMETER_TYPES.QUERY, required=query_param.required
        )
        if param_info:
            parameters.append(param_info)
    
    # Extract header parameters
    for header_param in dependant.header_params:
        param_info = create_parameter_info(
            header_param, PARAMETER_TYPES.HEADER, required=header_param.required
        )
        if param_info:
            parameters.append(param_info)
    
    # Extract body parameters
    if dependant.body_params:
        for body_param in dependant.body_params:
            param_info = create_parameter_info(
                body_param, PARAMETER_TYPES.BODY, required=body_param.required
            )
            if param_info:
                parameters.append(param_info)
    
    return parameters


def create_parameter_info(param, location: str, required: bool) -> Optional[Parameter]:
    """Create Parameter object from FastAPI parameter info."""
    try:
        name = param.alias or param.name
        param_type = get_type_string(param.type_)
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


def determine_module(path: str, function: Callable) -> str:
    """Determine which module an endpoint belongs to."""
    # Extract module from path using dictionary lookup
    for path_pattern, module_name in MODULE_MAPPINGS.PATH_TO_MODULE.items():
        if path_pattern in path:
            return module_name
    
    # Fallback: try to extract from function module
    if function and hasattr(function, '__module__'):
        module_path = function.__module__
        for keyword, module_name in MODULE_MAPPINGS.MODULE_KEYWORDS.items():
            if keyword in module_path:
                return module_name
    
    return 'miscellaneous'


def get_type_string(type_annotation) -> str:
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
                return f"List[{get_type_string(args[0])}]"
            return "List"
        elif origin is dict:
            if len(args) >= 2:
                return f"Dict[{get_type_string(args[0])}, {get_type_string(args[1])}]"
            return "Dict"
        elif hasattr(origin, '__name__'):
            return origin.__name__
    
    # Fallback to string representation
    return str(type_annotation)


def get_request_schema(func: Callable) -> Optional[BaseModel]:
    """Extract request schema from function annotations."""
    if not func:
        return None
    
    try:
        # Get function signature
        sig = inspect.signature(func)
        
        # Look for parameters that are Pydantic models
        for param_name, param in sig.parameters.items():
            # Skip common FastAPI dependencies
            if param_name in COMMON_PARAMETERS.SKIP_PARAMS:
                continue
            
            # Check if parameter annotation is a Pydantic model
            if param.annotation and param.annotation != inspect.Parameter.empty:
                if is_pydantic_model(param.annotation):
                    return param.annotation
                
                # Handle Optional types
                origin = get_origin(param.annotation)
                if origin is not None:
                    args = get_args(param.annotation)
                    for arg in args:
                        if is_pydantic_model(arg):
                            return arg
        
        return None
    except Exception:
        return None


def get_response_schema(func: Callable) -> Optional[BaseModel]:
    """Extract response schema from function annotations."""
    if not func:
        return None
    
    try:
        # Get function signature and return annotation
        sig = inspect.signature(func)
        return_annotation = sig.return_annotation
        
        if return_annotation and return_annotation != inspect.Parameter.empty:
            # Handle direct Pydantic model
            if is_pydantic_model(return_annotation):
                return return_annotation
            
            # Handle generic types like List[Model], Optional[Model], etc.
            origin = get_origin(return_annotation)
            if origin is not None:
                args = get_args(return_annotation)
                for arg in args:
                    if is_pydantic_model(arg):
                        return arg
        
        return None
    except Exception:
        return None


def get_response_schema_from_route(route: APIRoute) -> Optional[BaseModel]:
    """Extract response schema from FastAPI route response_model."""
    try:
        if hasattr(route, 'response_model') and route.response_model:
            if is_pydantic_model(route.response_model):
                return route.response_model
        return None
    except Exception:
        return None


def is_pydantic_model(annotation) -> bool:
    """Check if an annotation is a Pydantic model."""
    try:
        # Check if it's a class and inherits from BaseModel
        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            return True
        return False
    except (TypeError, AttributeError):
        return False


def analyze_schema_validation(model: BaseModel) -> dict:
    """Analyze validation rules from a Pydantic model."""
    if not model or not is_pydantic_model(model):
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