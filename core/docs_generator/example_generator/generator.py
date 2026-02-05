"""
Example generator for creating HTTP request and response examples.
"""

from typing import List, Dict, Any, Optional
from ..models import EndpointInfo, Example
from . import handlers


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
        return handlers.generate_success_examples(endpoint, self.base_url)
    
    def create_error_examples(self, endpoint: EndpointInfo) -> List[Example]:
        """Create error handling examples for an endpoint."""
        return handlers.generate_error_examples(endpoint, self.base_url)
    
    def generate_curl_command(self, endpoint: EndpointInfo, request_data: Dict[str, Any]) -> str:
        """Generate a cURL command for testing the endpoint."""
        return handlers.generate_curl_command(endpoint, request_data, self.base_url)
    
    def generate_curl_with_auth(self, endpoint: EndpointInfo, token: str = "YOUR_JWT_TOKEN") -> str:
        """Generate a cURL command with authentication token."""
        return handlers.generate_curl_with_auth(endpoint, self.base_url, token)
    
    def generate_curl_without_auth(self, endpoint: EndpointInfo) -> str:
        """Generate a cURL command without authentication (for testing auth errors)."""
        return handlers.generate_curl_without_auth(endpoint, self.base_url)
    
    def generate_curl_with_custom_data(self, endpoint: EndpointInfo, custom_data: Dict[str, Any]) -> str:
        """Generate a cURL command with custom request data."""
        return handlers.generate_curl_with_custom_data(endpoint, self.base_url, custom_data)
    
    def format_curl_for_documentation(self, curl_command: str) -> str:
        """Format cURL command for better readability in documentation."""
        return handlers.format_curl_for_documentation(curl_command)
    
    def generate_curl_examples_set(self, endpoint: EndpointInfo) -> Dict[str, str]:
        """Generate a complete set of cURL examples for different scenarios."""
        return handlers.generate_curl_examples_set(endpoint, self.base_url)
    
    def _generate_request_data(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate example request data for an endpoint."""
        return handlers.generate_request_data(endpoint, self.base_url)
    
    def _generate_response_data(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate example response data for an endpoint."""
        return handlers.generate_response_data(endpoint)
    
    def _handle_body_parameter(self, request_data: dict, param_name: str, example_value: Any) -> None:
        """Handle body parameter assignment."""
        return handlers.handle_body_parameter(request_data, param_name, example_value)
    
    def _generate_parameter_value(self, param) -> Any:
        """Generate an example value for a parameter based on its type."""
        return handlers.generate_parameter_value(param)
    
    def _generate_pydantic_example(self, model) -> Dict[str, Any]:
        """Generate example data from a Pydantic model."""
        return handlers.generate_pydantic_example(model)
    
    def _generate_object_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an object from a JSON schema."""
        return handlers.generate_object_from_schema(schema)
    
    def _generate_generic_response(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate a generic response based on endpoint characteristics."""
        return handlers.generate_generic_response(endpoint)
    
    def _generate_get_response(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Generate GET response based on endpoint function name."""
        return handlers.generate_get_response(endpoint)
    
    def _build_url(self, endpoint: EndpointInfo, request_data: Dict[str, Any]) -> str:
        """Build the complete URL for the endpoint."""
        return handlers.build_url(endpoint, request_data, self.base_url)
    
    def _create_auth_error_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create an authentication error example."""
        return handlers.create_auth_error_example(endpoint, self.base_url)
    
    def _create_validation_error_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create a validation error example."""
        return handlers.create_validation_error_example(endpoint, self.base_url)
    
    def _create_not_found_error_example(self, endpoint: EndpointInfo) -> Optional[Example]:
        """Create a not found error example."""
        return handlers.create_not_found_error_example(endpoint, self.base_url)