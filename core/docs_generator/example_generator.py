"""
Example generator for creating HTTP request and response examples.
"""

import json
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
from fastapi.routing import APIRoute

from .models import EndpointInfo, Example, Parameter


class ExampleGenerator:
    """Generates examples for API endpoints including HTTP requests, responses, and error handling."""
    
    def __init__(self):
        self.base_url = "https://api.example.com"
    
    def generate_examples(self, endpoint: EndpointInfo) -> List[Example]:
        """Generate complete examples for an endpoint including success and error cases."""
        examples = []
        
        # Generate success example
        success_example = self.create_success_example(endpoint)
        if success_example:
            examples.append(success_example)
        
        # Generate error examples
        error_examples = self.create_error_examples(endpoint)
        examples.extend(error_examples)
        
        return examples
    
    def create_success_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create a successful request/response example for an endpoint."""
        try:
            # Generate example request
            request_data = self._generate_request_data(endpoint)
            
            # Generate example response
            response_data = self._generate_response_data(endpoint)
            
            # Generate cURL command
            curl_command = self.generate_curl_command(endpoint, request_data)
            
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
    
    def create_error_examples(self, endpoint: EndpointInfo) -> List[Example]:
        """Create error handling examples for an endpoint."""
        examples = []
        
        # Authentication error (if endpoint requires auth)
        if endpoint.auth_required:
            auth_error = self._create_auth_error_example(endpoint)
            if auth_error:
                examples.append(auth_error)
        
        # Validation error (if endpoint has required parameters)
        required_params = [p for p in endpoint.parameters if p.required]
        if required_params:
            validation_error = self._create_validation_error_example(endpoint)
            if validation_error:
                examples.append(validation_error)
        
        # Not found error (for endpoints with path parameters)
        path_params = [p for p in endpoint.parameters if p.location == 'path']
        if path_params:
            not_found_error = self._create_not_found_error_example(endpoint)
            if not_found_error:
                examples.append(not_found_error)
        
        return examples
    
    def generate_curl_command(self, endpoint: EndpointInfo, request_data: Dict[str, Any]) -> str:
        """Generate a cURL command for testing the endpoint."""
        # Build the URL
        url = self._build_url(endpoint, request_data)
        
        # Start building the cURL command
        curl_parts = ["curl", "-X", endpoint.method]
        
        # Add verbose flag for better debugging
        curl_parts.append("-v")
        
        # Add authentication headers if required
        if endpoint.auth_required and request_data.get('headers', {}).get('Authorization'):
            auth_header = request_data['headers']['Authorization']
            curl_parts.extend(["-H", f'"Authorization: {auth_header}"'])
        
        # Add other headers
        headers = request_data.get('headers', {})
        for header_name, header_value in headers.items():
            if header_name != 'Authorization':  # Already handled above
                curl_parts.extend(["-H", f'"{header_name}: {header_value}"'])
        
        # Add content-type header for requests with body
        if endpoint.method in ['POST', 'PUT', 'PATCH'] and request_data.get('body'):
            if 'Content-Type' not in headers:
                curl_parts.extend(["-H", '"Content-Type: application/json"'])
        
        # Add request body if present
        if request_data.get('body'):
            body_json = json.dumps(request_data['body'], separators=(',', ':'), ensure_ascii=False)
            curl_parts.extend(["-d", f"'{body_json}'"])
        
        # Add the URL
        curl_parts.append(f'"{url}"')
        
        return " ".join(curl_parts)
    
    def generate_curl_with_auth(self, endpoint: EndpointInfo, token: str = "YOUR_JWT_TOKEN") -> str:
        """Generate a cURL command with authentication token."""
        request_data = self._generate_request_data(endpoint)
        request_data['headers']['Authorization'] = f'Bearer {token}'
        return self.generate_curl_command(endpoint, request_data)
    
    def generate_curl_without_auth(self, endpoint: EndpointInfo) -> str:
        """Generate a cURL command without authentication (for testing auth errors)."""
        request_data = self._generate_request_data(endpoint)
        # Remove auth header if present
        if 'Authorization' in request_data.get('headers', {}):
            del request_data['headers']['Authorization']
        return self.generate_curl_command(endpoint, request_data)
    
    def generate_curl_with_custom_data(self, endpoint: EndpointInfo, custom_data: Dict[str, Any]) -> str:
        """Generate a cURL command with custom request data."""
        request_data = self._generate_request_data(endpoint)
        
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
        request_data['url'] = self._build_url(endpoint, request_data)
        
        return self.generate_curl_command(endpoint, request_data)
    
    def format_curl_for_documentation(self, curl_command: str) -> str:
        """Format cURL command for better readability in documentation."""
        # Split the command into parts for multi-line formatting
        parts = curl_command.split(' ')
        
        formatted_parts = []
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if part == 'curl':
                formatted_parts.append(part)
            elif part == '-X':
                formatted_parts.append(f"  {part} {parts[i+1]} \\")
                i += 1
            elif part == '-H':
                formatted_parts.append(f"  {part} {parts[i+1]} \\")
                i += 1
            elif part == '-d':
                formatted_parts.append(f"  {part} {parts[i+1]} \\")
                i += 1
            elif part == '-v':
                formatted_parts.append(f"  {part} \\")
            elif part.startswith('"http'):
                formatted_parts.append(f"  {part}")
            else:
                if i == len(parts) - 1:  # Last part
                    formatted_parts.append(f"  {part}")
                else:
                    formatted_parts.append(f"  {part} \\")
            i += 1
        
        return '\n'.join(formatted_parts)
    
    def generate_curl_examples_set(self, endpoint: EndpointInfo) -> Dict[str, str]:
        """Generate a complete set of cURL examples for different scenarios."""
        examples = {}
        
        # Success example
        examples['success'] = self.generate_curl_with_auth(endpoint)
        
        # Authentication error example
        if endpoint.auth_required:
            examples['auth_error'] = self.generate_curl_without_auth(endpoint)
        
        # Validation error example (missing required parameters)
        required_params = [p for p in endpoint.parameters if p.required]
        if required_params:
            # Create request with missing required parameters
            incomplete_data = {'body': {}, 'query_params': {}, 'path_params': {}}
            examples['validation_error'] = self.generate_curl_with_custom_data(endpoint, incomplete_data)
        
        # Custom data example
        if endpoint.method in ['POST', 'PUT', 'PATCH']:
            custom_data = {
                'body': {
                    'name': 'Custom Example',
                    'description': 'This is a custom example with specific data'
                }
            }
            examples['custom_data'] = self.generate_curl_with_custom_data(endpoint, custom_data)
        
        return examples
    
    def _generate_request_data(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate example request data for an endpoint."""
        request_data = {
            "method": endpoint.method,
            "url": self._build_url(endpoint, {}),
            "headers": {},
            "query_params": {},
            "path_params": {},
            "body": None
        }
        
        # Add authentication header if required
        if endpoint.auth_required:
            request_data["headers"]["Authorization"] = "Bearer YOUR_JWT_TOKEN"
        
        # Generate parameter values
        for param in endpoint.parameters:
            example_value = self._generate_parameter_value(param)
            
            if param.location == 'query':
                request_data["query_params"][param.name] = example_value
            elif param.location == 'path':
                request_data["path_params"][param.name] = example_value
            elif param.location == 'header':
                request_data["headers"][param.name] = example_value
            elif param.location == 'body':
                if request_data["body"] is None:
                    request_data["body"] = {}
                request_data["body"][param.name] = example_value
        
        # Generate request body from Pydantic model if available
        if endpoint.request_body and endpoint.method in ['POST', 'PUT', 'PATCH']:
            request_data["body"] = self._generate_pydantic_example(endpoint.request_body)
            request_data["headers"]["Content-Type"] = "application/json"
        
        # Update URL with actual parameter values
        request_data["url"] = self._build_url(endpoint, request_data)
        
        return request_data
    
    def _generate_response_data(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate example response data for an endpoint."""
        response_data = {
            "status_code": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {}
        }
        
        # Generate response body from Pydantic model if available
        if endpoint.response_model:
            response_data["body"] = self._generate_pydantic_example(endpoint.response_model)
        else:
            # Generate generic response based on endpoint type
            response_data["body"] = self._generate_generic_response(endpoint)
        
        return response_data
    
    def _generate_parameter_value(self, param: Parameter) -> Any:
        """Generate an example value for a parameter based on its type."""
        type_examples = {
            'str': 'example_string',
            'string': 'example_string',
            'int': 123,
            'integer': 123,
            'float': 123.45,
            'number': 123.45,
            'bool': True,
            'boolean': True,
            'list': ['item1', 'item2'],
            'array': ['item1', 'item2'],
            'dict': {'key': 'value'},
            'object': {'key': 'value'}
        }
        
        # Handle specific parameter names
        if 'id' in param.name.lower():
            return 123
        elif 'email' in param.name.lower():
            return 'user@example.com'
        elif 'name' in param.name.lower():
            return 'Example Name'
        elif 'limit' in param.name.lower():
            return 10
        elif 'offset' in param.name.lower():
            return 0
        elif 'page' in param.name.lower():
            return 1
        
        # Use type-based example
        param_type = param.type.lower()
        return type_examples.get(param_type, 'example_value')
    
    def _generate_pydantic_example(self, model: BaseModel) -> Dict[str, Any]:
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
                            self._generate_object_from_schema(items_schema),
                            self._generate_object_from_schema(items_schema)
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
    
    def _generate_object_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _generate_generic_response(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate a generic response based on endpoint characteristics."""
        # Generate response based on HTTP method
        if endpoint.method == 'GET':
            if 'list' in endpoint.function_name.lower() or 'all' in endpoint.function_name.lower():
                return {
                    "data": [
                        {"id": 1, "name": "Example Item 1"},
                        {"id": 2, "name": "Example Item 2"}
                    ],
                    "total": 2
                }
            else:
                return {
                    "id": 123,
                    "name": "Example Item",
                    "created_at": "2024-01-01T00:00:00Z"
                }
        elif endpoint.method == 'POST':
            return {
                "id": 123,
                "message": "Resource created successfully",
                "created_at": "2024-01-01T00:00:00Z"
            }
        elif endpoint.method == 'PUT':
            return {
                "id": 123,
                "message": "Resource updated successfully",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        elif endpoint.method == 'DELETE':
            return {
                "message": "Resource deleted successfully"
            }
        else:
            return {
                "message": "Operation completed successfully"
            }
    
    def _build_url(self, endpoint: EndpointInfo, request_data: Dict[str, Any]) -> str:
        """Build the complete URL for the endpoint."""
        url = self.base_url + endpoint.path
        
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
    
    def _create_auth_error_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create an authentication error example."""
        try:
            request_data = {
                "method": endpoint.method,
                "url": self._build_url(endpoint, {}),
                "headers": {},
                "query_params": {},
                "path_params": {},
                "body": None
            }
            
            # Don't include auth header to trigger error
            
            response_data = {
                "status_code": 401,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "error": "Unauthorized",
                    "message": "Authentication required"
                }
            }
            
            curl_command = self.generate_curl_without_auth(endpoint)
            
            return Example(
                title=f"Authentication Error - {endpoint.method} {endpoint.path}",
                description="Example of an authentication error when no valid JWT token is provided.",
                request=request_data,
                response=response_data,
                curl_command=curl_command
            )
        except Exception:
            return None
    
    def _create_validation_error_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create a validation error example."""
        try:
            request_data = {
                "method": endpoint.method,
                "url": self._build_url(endpoint, {}),
                "headers": {},
                "query_params": {},
                "path_params": {},
                "body": None
            }
            
            if endpoint.auth_required:
                request_data["headers"]["Authorization"] = "Bearer YOUR_JWT_TOKEN"
            
            # Don't include required parameters to trigger validation error
            
            response_data = {
                "status_code": 422,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "error": "Validation Error",
                    "message": "Required parameters missing",
                    "details": [
                        {
                            "field": "required_field",
                            "message": "This field is required"
                        }
                    ]
                }
            }
            
            curl_command = self.generate_curl_command(endpoint, request_data)
            
            return Example(
                title=f"Validation Error - {endpoint.method} {endpoint.path}",
                description="Example of a validation error when required parameters are missing.",
                request=request_data,
                response=response_data,
                curl_command=curl_command
            )
        except Exception:
            return None
    
    def _create_not_found_error_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create a not found error example."""
        try:
            request_data = self._generate_request_data(endpoint)
            
            # Use a non-existent ID for path parameters
            for param in endpoint.parameters:
                if param.location == 'path' and 'id' in param.name.lower():
                    request_data["path_params"][param.name] = 99999
            
            request_data["url"] = self._build_url(endpoint, request_data)
            
            response_data = {
                "status_code": 404,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "error": "Not Found",
                    "message": "Resource not found"
                }
            }
            
            curl_command = self.generate_curl_command(endpoint, request_data)
            
            return Example(
                title=f"Not Found Error - {endpoint.method} {endpoint.path}",
                description="Example of a not found error when the requested resource doesn't exist.",
                request=request_data,
                response=response_data,
                curl_command=curl_command
            )
        except Exception:
            return None