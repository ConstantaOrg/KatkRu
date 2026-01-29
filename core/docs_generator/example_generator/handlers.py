"""
Handler functions for example generator.
"""

import json
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel

from ..models import EndpointInfo, Example, Parameter
from .models import ExampleRequest, ExampleResponse, CurlOptions
from .constants import (
    HttpStatusCodes, ContentTypes, ParameterTypeExamples, SpecialParameterNames,
    ErrorTemplates, ResponseTemplates, CurlTemplates
)


def generate_success_examples(endpoint: EndpointInfo, base_url: str) -> Optional[Example]:
    """Generate a successful request/response example for an endpoint."""
    try:
        # Generate example request
        request_data = generate_request_data(endpoint, base_url)
        
        # Generate example response
        response_data = generate_response_data(endpoint)
        
        # Generate cURL command
        curl_command = generate_curl_command(endpoint, request_data, base_url)
        
        # Create example title and description
        title = f"Successful {endpoint.method} request to {endpoint.path}"
        description = f"Example of a successful {endpoint.method.lower()} request to the {endpoint.function_name} endpoint."
        
        return Example(
            title=title,
            description=description,
            request=request_data,
            response=response_data,
            curl_command=curl_command
        )
    except Exception:
        # If we can't generate an example, return None
        return None


def generate_error_examples(endpoint: EndpointInfo, base_url: str) -> List[Example]:
    """Generate error handling examples for an endpoint."""
    examples = []
    
    # Authentication error (if endpoint requires auth)
    if endpoint.auth_required:
        auth_error = create_auth_error_example(endpoint, base_url)
        if auth_error:
            examples.append(auth_error)
    
    # Validation error (if endpoint has required parameters)
    required_params = [p for p in endpoint.parameters if p.required]
    if required_params:
        validation_error = create_validation_error_example(endpoint, base_url)
        if validation_error:
            examples.append(validation_error)
    
    # Not found error (for endpoints with path parameters)
    path_params = [p for p in endpoint.parameters if p.location == 'path']
    if path_params:
        not_found_error = create_not_found_error_example(endpoint, base_url)
        if not_found_error:
            examples.append(not_found_error)
    
    return examples


def generate_curl_command(endpoint: EndpointInfo, request_data: Dict[str, Any], base_url: str) -> str:
    """Generate a cURL command for testing the endpoint."""
    # Build the URL
    url = build_url(endpoint, request_data, base_url)
    
    # Start building the cURL command
    curl_parts = [CurlTemplates.BASE_COMMAND, CurlTemplates.METHOD_FLAG, endpoint.method]
    
    # Add verbose flag for better debugging
    curl_parts.append(CurlTemplates.VERBOSE_FLAG)
    
    # Add authentication headers if required
    if endpoint.auth_required and request_data.get('headers', {}).get('Authorization'):
        auth_header = request_data['headers']['Authorization']
        curl_parts.extend([CurlTemplates.HEADER_FLAG, f'"{CurlTemplates.AUTH_HEADER_TEMPLATE.format(token=auth_header.split(" ")[1])}"'])
    
    # Add other headers
    headers = request_data.get('headers', {})
    for header_name, header_value in headers.items():
        if header_name != 'Authorization':  # Already handled above
            curl_parts.extend([CurlTemplates.HEADER_FLAG, f'"{header_name}: {header_value}"'])
    
    # Add content-type header for requests with body
    if endpoint.method in ['POST', 'PUT', 'PATCH'] and request_data.get('body'):
        if 'Content-Type' not in headers:
            curl_parts.extend([CurlTemplates.HEADER_FLAG, f'"{CurlTemplates.CONTENT_TYPE_HEADER}"'])
    
    # Add request body if present
    if request_data.get('body'):
        body_json = json.dumps(request_data['body'], separators=(',', ':'), ensure_ascii=False)
        curl_parts.extend([CurlTemplates.DATA_FLAG, f"'{body_json}'"])
    
    # Add the URL
    curl_parts.append(f'"{url}"')
    
    return " ".join(curl_parts)


def generate_curl_with_auth(endpoint: EndpointInfo, base_url: str, token: str = CurlTemplates.DEFAULT_TOKEN) -> str:
    """Generate a cURL command with authentication token."""
    request_data = generate_request_data(endpoint, base_url)
    request_data['headers']['Authorization'] = f'Bearer {token}'
    return generate_curl_command(endpoint, request_data, base_url)


def generate_curl_without_auth(endpoint: EndpointInfo, base_url: str) -> str:
    """Generate a cURL command without authentication (for testing auth errors)."""
    request_data = generate_request_data(endpoint, base_url)
    # Remove auth header if present
    if 'Authorization' in request_data.get('headers', {}):
        del request_data['headers']['Authorization']
    return generate_curl_command(endpoint, request_data, base_url)


def generate_curl_with_custom_data(endpoint: EndpointInfo, base_url: str, custom_data: Dict[str, Any]) -> str:
    """Generate a cURL command with custom request data."""
    request_data = generate_request_data(endpoint, base_url)
    
    # Override with custom data
    if 'body' in custom_data:
        request_data['body'] = custom_data['body']
    if 'query_params' in custom_data:
        request_data['query_params'].update(custom_data['query_params'])
    if 'headers' in custom_data:
        request_data['headers'].update(custom_data['headers'])
    if 'path_params' in custom_data:
        request_data['path_params'].update(custom_data['path_params'])
    
    # Rebuild URL with updated parameters
    request_data['url'] = build_url(endpoint, request_data, base_url)
    
    return generate_curl_command(endpoint, request_data, base_url)


def format_curl_for_documentation(curl_command: str) -> str:
    """Format cURL command for better readability in documentation."""
    # Split the command into parts for multi-line formatting
    parts = curl_command.split(' ')
    
    formatted_parts = []
    i = 0
    while i < len(parts):
        part = parts[i]
        
        if part == CurlTemplates.BASE_COMMAND:
            formatted_parts.append(part)
        elif part == CurlTemplates.METHOD_FLAG:
            formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part} {parts[i+1]}{CurlTemplates.MULTILINE_SEPARATOR}")
            i += 1
        elif part == CurlTemplates.HEADER_FLAG:
            formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part} {parts[i+1]}{CurlTemplates.MULTILINE_SEPARATOR}")
            i += 1
        elif part == CurlTemplates.DATA_FLAG:
            formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part} {parts[i+1]}{CurlTemplates.MULTILINE_SEPARATOR}")
            i += 1
        elif part == CurlTemplates.VERBOSE_FLAG:
            formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part}{CurlTemplates.MULTILINE_SEPARATOR}")
        elif part.startswith('"http'):
            formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part}")
        else:
            if i == len(parts) - 1:  # Last part
                formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part}")
            else:
                formatted_parts.append(f"{CurlTemplates.LINE_INDENT}{part}{CurlTemplates.MULTILINE_SEPARATOR}")
        i += 1
    
    return '\n'.join(formatted_parts)


def generate_curl_examples_set(endpoint: EndpointInfo, base_url: str) -> Dict[str, str]:
    """Generate a complete set of cURL examples for different scenarios."""
    examples = {}
    
    # Success example
    examples['success'] = generate_curl_with_auth(endpoint, base_url)
    
    # Authentication error example
    if endpoint.auth_required:
        examples['auth_error'] = generate_curl_without_auth(endpoint, base_url)
    
    # Validation error example (missing required parameters)
    required_params = [p for p in endpoint.parameters if p.required]
    if required_params:
        # Create request with missing required parameters
        incomplete_data = {'body': {}, 'query_params': {}, 'path_params': {}}
        examples['validation_error'] = generate_curl_with_custom_data(endpoint, base_url, incomplete_data)
    
    # Custom data example
    if endpoint.method in ['POST', 'PUT', 'PATCH']:
        custom_data = {
            'body': {
                'name': 'Custom Example',
                'description': 'This is a custom example with specific data'
            }
        }
        examples['custom_data'] = generate_curl_with_custom_data(endpoint, base_url, custom_data)
    
    return examples


def generate_request_data(endpoint: EndpointInfo, base_url: str) -> Dict[str, Any]:
    """Generate example request data for an endpoint."""
    request_data = {
        "method": endpoint.method,
        "url": build_url(endpoint, {}, base_url),
        "headers": {},
        "query_params": {},
        "path_params": {},
        "body": None
    }
    
    # Add authentication header if required
    if endpoint.auth_required:
        request_data["headers"]["Authorization"] = f"Bearer {CurlTemplates.DEFAULT_TOKEN}"
    
    # Generate parameter values
    for param in endpoint.parameters:
        example_value = generate_parameter_value(param)
        
        # Import constants
        from core.utils.anything import ParameterLocations
        
        # Parameter location handlers
        location_handlers = {
            ParameterLocations.query: lambda: request_data["query_params"].__setitem__(param.name, example_value),
            ParameterLocations.path: lambda: request_data["path_params"].__setitem__(param.name, example_value),
            ParameterLocations.header: lambda: request_data["headers"].__setitem__(param.name, example_value),
            ParameterLocations.body: lambda: handle_body_parameter(request_data, param.name, example_value),
        }
        
        # Execute the appropriate handler
        handler = location_handlers.get(param.location)
        if handler:
            handler()
    
    # Generate request body from Pydantic model if available
    if endpoint.request_body and endpoint.method in ['POST', 'PUT', 'PATCH']:
        request_data["body"] = generate_pydantic_example(endpoint.request_body)
        request_data["headers"]["Content-Type"] = ContentTypes.JSON
    
    # Update URL with actual parameter values
    request_data["url"] = build_url(endpoint, request_data, base_url)
    
    return request_data


def generate_response_data(endpoint: EndpointInfo) -> Dict[str, Any]:
    """Generate example response data for an endpoint."""
    response_data = {
        "status_code": HttpStatusCodes.SUCCESS,
        "headers": {
            "Content-Type": ContentTypes.JSON
        },
        "body": {}
    }
    
    # Generate response body from Pydantic model if available
    if endpoint.response_model:
        response_data["body"] = generate_pydantic_example(endpoint.response_model)
    else:
        # Generate generic response based on endpoint type
        response_data["body"] = generate_generic_response(endpoint)
    
    return response_data


def handle_body_parameter(request_data: dict, param_name: str, example_value: Any) -> None:
    """Handle body parameter assignment."""
    if request_data["body"] is None:
        request_data["body"] = {}
    request_data["body"][param_name] = example_value


def generate_parameter_value(param: Parameter) -> Any:
    """Generate an example value for a parameter based on its type."""
    # Combine all type examples
    all_type_examples = {
        **ParameterTypeExamples.STRING_EXAMPLES,
        **ParameterTypeExamples.NUMERIC_EXAMPLES,
        **ParameterTypeExamples.BOOLEAN_EXAMPLES,
        **ParameterTypeExamples.COLLECTION_EXAMPLES
    }
    
    # Handle specific parameter names
    param_lower = param.name.lower()
    
    # Check for special parameter patterns
    for pattern in SpecialParameterNames.ID_PATTERNS:
        if pattern in param_lower:
            return SpecialParameterNames.EXAMPLES['id']
    
    for pattern in SpecialParameterNames.EMAIL_PATTERNS:
        if pattern in param_lower:
            return SpecialParameterNames.EXAMPLES['email']
    
    for pattern in SpecialParameterNames.NAME_PATTERNS:
        if pattern in param_lower:
            return SpecialParameterNames.EXAMPLES['name']
    
    for pattern in SpecialParameterNames.PAGINATION_PATTERNS:
        if pattern in param_lower:
            return SpecialParameterNames.EXAMPLES.get(pattern, 10)
    
    # Use type-based example
    param_type = param.type.lower()
    return all_type_examples.get(param_type, 'example_value')


def generate_pydantic_example(model: BaseModel) -> Dict[str, Any]:
    """Generate example data from a Pydantic model."""
    try:
        # Try to get schema from the model
        if hasattr(model, 'model_json_schema'):
            schema = model.model_json_schema()
        elif hasattr(model, 'schema'):
            schema = model.schema()
        else:
            return {"message": "Example response"}
        
        # Check if there's a predefined example in Config
        if hasattr(model, 'Config') and hasattr(model.Config, 'json_schema_extra'):
            config_extra = model.Config.json_schema_extra
            if isinstance(config_extra, dict) and 'example' in config_extra:
                return config_extra['example']
        
        # Generate example based on schema properties
        example = {}
        properties = schema.get('properties', {})
        
        for field_name, field_info in properties.items():
            # Check if field has predefined example
            if 'example' in field_info:
                example[field_name] = field_info['example']
                continue
            
            field_type = field_info.get('type', 'string')
            
            if field_type == 'string':
                if 'email' in field_name.lower():
                    example[field_name] = 'user@example.com'
                elif 'name' in field_name.lower():
                    example[field_name] = 'Example Name'
                elif 'message' in field_name.lower():
                    example[field_name] = 'Operation completed successfully'
                else:
                    example[field_name] = 'example_string'
            elif field_type == 'integer':
                if 'id' in field_name.lower():
                    example[field_name] = 123
                elif 'count' in field_name.lower():
                    example[field_name] = 5
                else:
                    example[field_name] = 42
            elif field_type == 'number':
                example[field_name] = 123.45
            elif field_type == 'boolean':
                if 'success' in field_name.lower():
                    example[field_name] = True
                else:
                    example[field_name] = True
            elif field_type == 'array':
                # Handle arrays with items schema
                items_schema = field_info.get('items', {})
                if items_schema.get('type') == 'object':
                    # Generate array of objects
                    example[field_name] = [
                        generate_object_from_schema(items_schema),
                        generate_object_from_schema(items_schema)
                    ]
                else:
                    # Simple array
                    example[field_name] = ['item1', 'item2']
            elif field_type == 'object':
                example[field_name] = {'key': 'value'}
            else:
                example[field_name] = 'example_value'
        
        return example if example else {"message": "Example response"}
    except Exception as e:
        print(f"Error generating Pydantic example: {e}")
        return {"message": "Example response"}


def generate_object_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an object from a JSON schema."""
    obj = {}
    properties = schema.get('properties', {})
    
    for field_name, field_info in properties.items():
        field_type = field_info.get('type', 'string')
        
        if field_type == 'string':
            if 'id' in field_name.lower():
                obj[field_name] = 'abc123'
            elif 'name' in field_name.lower():
                obj[field_name] = 'Example Name'
            else:
                obj[field_name] = 'example_string'
        elif field_type == 'integer':
            if 'id' in field_name.lower():
                obj[field_name] = 123
            else:
                obj[field_name] = 42
        elif field_type == 'boolean':
            obj[field_name] = True
        else:
            obj[field_name] = 'example_value'
    
    return obj if obj else {'id': 123, 'name': 'Example Item'}


def generate_generic_response(endpoint: EndpointInfo) -> Dict[str, Any]:
    """Generate a generic response based on endpoint characteristics."""
    # Import constants
    from core.utils.anything import HttpMethods
    
    # Response generators for different HTTP methods
    response_generators = {
        HttpMethods.GET: lambda ep: generate_get_response(ep),
        HttpMethods.POST: lambda ep: ResponseTemplates.POST_CREATED,
        HttpMethods.PUT: lambda ep: ResponseTemplates.PUT_UPDATED,
        HttpMethods.DELETE: lambda ep: ResponseTemplates.DELETE_SUCCESS
    }
    
    # Get the appropriate response generator
    generator = response_generators.get(endpoint.method)
    if generator:
        return generator(endpoint)
    else:
        # Default response for unknown methods
        return {"message": "Operation completed successfully"}


def generate_get_response(endpoint: EndpointInfo) -> Dict[str, Any]:
    """Generate GET response based on endpoint function name."""
    if 'list' in endpoint.function_name.lower() or 'all' in endpoint.function_name.lower():
        return ResponseTemplates.GET_LIST
    else:
        return ResponseTemplates.GET_SINGLE


def build_url(endpoint: EndpointInfo, request_data: Dict[str, Any], base_url: str) -> str:
    """Build the complete URL for the endpoint."""
    url = base_url + endpoint.path
    
    # Replace path parameters
    path_params = request_data.get('path_params', {})
    for param_name, param_value in path_params.items():
        url = url.replace(f'{{{param_name}}}', str(param_value))
    
    # Add query parameters
    query_params = request_data.get('query_params', {})
    if query_params:
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        url += f"?{query_string}"
    
    return url


def create_auth_error_example(endpoint: EndpointInfo, base_url: str) -> Optional[Example]:
    """Create an authentication error example."""
    try:
        request_data = {
            "method": endpoint.method,
            "url": build_url(endpoint, {}, base_url),
            "headers": {},
            "query_params": {},
            "path_params": {},
            "body": None
        }
        
        # Don't include auth header to trigger error
        
        response_data = {
            "status_code": HttpStatusCodes.UNAUTHORIZED,
            "headers": {
                "Content-Type": ContentTypes.JSON
            },
            "body": ErrorTemplates.UNAUTHORIZED
        }
        
        curl_command = generate_curl_without_auth(endpoint, base_url)
        
        return Example(
            title=f"Authentication Error - {endpoint.method} {endpoint.path}",
            description="Example of an authentication error when no valid JWT token is provided.",
            request=request_data,
            response=response_data,
            curl_command=curl_command
        )
    except Exception:
        return None


def create_validation_error_example(endpoint: EndpointInfo, base_url: str) -> Optional[Example]:
    """Create a validation error example."""
    try:
        request_data = {
            "method": endpoint.method,
            "url": build_url(endpoint, {}, base_url),
            "headers": {},
            "query_params": {},
            "path_params": {},
            "body": None
        }
        
        if endpoint.auth_required:
            request_data["headers"]["Authorization"] = f"Bearer {CurlTemplates.DEFAULT_TOKEN}"
        
        # Don't include required parameters to trigger validation error
        
        response_data = {
            "status_code": HttpStatusCodes.VALIDATION_ERROR,
            "headers": {
                "Content-Type": ContentTypes.JSON
            },
            "body": ErrorTemplates.VALIDATION_ERROR
        }
        
        curl_command = generate_curl_command(endpoint, request_data, base_url)
        
        return Example(
            title=f"Validation Error - {endpoint.method} {endpoint.path}",
            description="Example of a validation error when required parameters are missing.",
            request=request_data,
            response=response_data,
            curl_command=curl_command
        )
    except Exception:
        return None


def create_not_found_error_example(endpoint: EndpointInfo, base_url: str) -> Optional[Example]:
    """Create a not found error example."""
    try:
        request_data = generate_request_data(endpoint, base_url)
        
        # Use a non-existent ID for path parameters
        for param in endpoint.parameters:
            if param.location == 'path' and 'id' in param.name.lower():
                request_data["path_params"][param.name] = 99999
        
        request_data["url"] = build_url(endpoint, request_data, base_url)
        
        response_data = {
            "status_code": HttpStatusCodes.NOT_FOUND,
            "headers": {
                "Content-Type": ContentTypes.JSON
            },
            "body": ErrorTemplates.NOT_FOUND
        }
        
        curl_command = generate_curl_command(endpoint, request_data, base_url)
        
        return Example(
            title=f"Not Found Error - {endpoint.method} {endpoint.path}",
            description="Example of a not found error when the requested resource doesn't exist.",
            request=request_data,
            response=response_data,
            curl_command=curl_command
        )
    except Exception:
        return None