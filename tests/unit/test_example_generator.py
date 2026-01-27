"""
Property-based tests for ExampleGenerator.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import List

from core.docs_generator.example_generator import ExampleGenerator
from core.docs_generator.models import EndpointInfo, Parameter, Dependency, Example


class TestExampleGenerator:
    """Test ExampleGenerator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ExampleGenerator()
    
    @given(st.builds(
        EndpointInfo,
        path=st.one_of(
            st.just('/specialties'),
            st.just('/groups/{id}'),
            st.just('/teachers/list'),
            st.just('/disciplines/search'),
            st.just('/timetable/schedule'),
            st.just('/users/profile'),
            st.just('/n8n/webhook'),
            st.just('/search/query')
        ),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']),
        function_name=st.text(min_size=1, max_size=50),
        module=st.sampled_from(['specialties', 'groups', 'teachers', 'disciplines', 
                              'timetable', 'users', 'n8n_ui', 'elastic_search']),
        description=st.text(max_size=200),
        parameters=st.lists(
            st.builds(
                Parameter,
                name=st.one_of(
                    st.just('id'),
                    st.just('limit'),
                    st.just('offset'),
                    st.just('email'),
                    st.just('name'),
                    st.text(min_size=1, max_size=20)
                ),
                type=st.sampled_from(['str', 'int', 'bool', 'float', 'string', 'integer', 'number', 'boolean']),
                required=st.booleans(),
                description=st.text(max_size=100),
                location=st.sampled_from(['query', 'path', 'header', 'body'])
            ),
            max_size=5
        ),
        request_body=st.none(),
        response_model=st.none(),
        auth_required=st.booleans(),
        roles_required=st.lists(st.text(min_size=1, max_size=20), max_size=3),
        dependencies=st.lists(
            st.builds(
                Dependency,
                name=st.text(min_size=1, max_size=30),
                type=st.sampled_from(['function', 'class', 'middleware', 'external_service']),
                module=st.text(min_size=1, max_size=50),
                description=st.text(max_size=100)
            ),
            max_size=5
        )
    ))
    @settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=100)
    def test_property_example_completeness(self, endpoint: EndpointInfo):
        """
        Feature: api-documentation, Property 5: Example completeness
        
        For any documented endpoint, there should be HTTP request examples, 
        response examples, and error handling examples provided.
        
        **Validates: Requirements 5.1, 5.2, 5.4**
        """
        # Generate examples for the endpoint
        examples = self.generator.generate_examples(endpoint)
        
        # Property 1: Examples should be generated for all endpoints
        assert examples is not None, "Examples should not be None"
        assert isinstance(examples, list), "Examples should be a list"
        assert len(examples) > 0, "At least one example should be generated"
        
        # Property 2: Each example should have complete structure
        for example in examples:
            assert isinstance(example, Example), "Each example should be an Example object"
            
            # Title should be present and non-empty
            assert example.title is not None, "Example title should not be None"
            assert isinstance(example.title, str), "Example title should be a string"
            assert len(example.title) > 0, "Example title should not be empty"
            
            # Description should be present and non-empty
            assert example.description is not None, "Example description should not be None"
            assert isinstance(example.description, str), "Example description should be a string"
            assert len(example.description) > 0, "Example description should not be empty"
            
            # Request should be present and have required structure
            assert example.request is not None, "Example request should not be None"
            assert isinstance(example.request, dict), "Example request should be a dictionary"
            
            # Request should have method and URL
            assert 'method' in example.request, "Request should have method"
            assert 'url' in example.request, "Request should have URL"
            assert example.request['method'] in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], \
                "Request method should be valid HTTP method"
            assert isinstance(example.request['url'], str), "Request URL should be a string"
            assert len(example.request['url']) > 0, "Request URL should not be empty"
            
            # Response should be present and have required structure
            assert example.response is not None, "Example response should not be None"
            assert isinstance(example.response, dict), "Example response should be a dictionary"
            
            # Response should have status code and body
            assert 'status_code' in example.response, "Response should have status_code"
            assert 'body' in example.response, "Response should have body"
            assert isinstance(example.response['status_code'], int), "Status code should be integer"
            assert 100 <= example.response['status_code'] <= 599, "Status code should be valid HTTP status"
            
            # cURL command should be present and non-empty
            assert example.curl_command is not None, "cURL command should not be None"
            assert isinstance(example.curl_command, str), "cURL command should be a string"
            assert len(example.curl_command) > 0, "cURL command should not be empty"
            assert 'curl' in example.curl_command, "cURL command should contain 'curl'"
        
        # Property 3: Should have at least one success example
        success_examples = [ex for ex in examples if 200 <= ex.response['status_code'] < 300]
        assert len(success_examples) > 0, "Should have at least one success example"
        
        # Property 4: Should have error examples if endpoint has error conditions
        error_examples = [ex for ex in examples if ex.response['status_code'] >= 400]
        
        # If endpoint requires authentication, should have auth error example
        if endpoint.auth_required:
            auth_errors = [ex for ex in error_examples if ex.response['status_code'] == 401]
            assert len(auth_errors) > 0, "Should have authentication error example for auth-required endpoints"
        
        # If endpoint has required parameters, should have validation error example
        required_params = [p for p in endpoint.parameters if p.required]
        if required_params:
            validation_errors = [ex for ex in error_examples if ex.response['status_code'] == 422]
            assert len(validation_errors) > 0, "Should have validation error example for endpoints with required params"
        
        # If endpoint has path parameters, should have not found error example
        path_params = [p for p in endpoint.parameters if p.location == 'path']
        if path_params:
            not_found_errors = [ex for ex in error_examples if ex.response['status_code'] == 404]
            assert len(not_found_errors) > 0, "Should have not found error example for endpoints with path params"
        
        # Property 5: cURL commands should be valid and executable
        for example in examples:
            curl_cmd = example.curl_command
            
            # Should start with curl
            assert curl_cmd.startswith('curl'), "cURL command should start with 'curl'"
            
            # Should contain HTTP method
            assert f'-X {example.request["method"]}' in curl_cmd, \
                f"cURL command should contain method {example.request['method']}"
            
            # Should contain URL
            assert example.request['url'] in curl_cmd, "cURL command should contain the URL"
            
            # If auth required, should contain auth header
            if endpoint.auth_required and example.response['status_code'] != 401:
                assert 'Authorization: Bearer' in curl_cmd, \
                    "cURL command should contain auth header for authenticated endpoints"
            
            # If has body, should contain data flag
            if example.request.get('body'):
                assert '-d' in curl_cmd, "cURL command should contain data flag when body is present"
        
        # Property 6: Examples should cover different scenarios
        example_types = set()
        for example in examples:
            if 200 <= example.response['status_code'] < 300:
                example_types.add('success')
            elif example.response['status_code'] == 401:
                example_types.add('auth_error')
            elif example.response['status_code'] == 422:
                example_types.add('validation_error')
            elif example.response['status_code'] == 404:
                example_types.add('not_found_error')
            else:
                example_types.add('other_error')
        
        # Should always have success example
        assert 'success' in example_types, "Should always have success example"
        
        # Should have appropriate error examples based on endpoint characteristics
        if endpoint.auth_required:
            assert 'auth_error' in example_types, "Should have auth error for auth-required endpoints"
        
        if any(p.required for p in endpoint.parameters):
            assert 'validation_error' in example_types, "Should have validation error for endpoints with required params"
        
        if any(p.location == 'path' for p in endpoint.parameters):
            assert 'not_found_error' in example_types, "Should have not found error for endpoints with path params"
    
    def test_success_example_generation(self):
        """Test generation of success examples."""
        endpoint = EndpointInfo(
            path='/users/{id}',
            method='GET',
            function_name='get_user',
            module='users',
            description='Get user by ID',
            parameters=[
                Parameter(name='id', type='int', required=True, description='User ID', location='path'),
                Parameter(name='limit', type='int', required=False, description='Limit results', location='query')
            ],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['user'],
            dependencies=[]
        )
        
        success_example = self.generator.create_success_example(endpoint)
        
        assert success_example is not None
        assert success_example.title == "Successful GET request to /users/{id}"
        assert "successful get request" in success_example.description.lower()
        assert success_example.request['method'] == 'GET'
        assert success_example.response['status_code'] == 200
        assert 'Authorization: Bearer' in success_example.curl_command
    
    def test_error_examples_generation(self):
        """Test generation of error examples."""
        endpoint = EndpointInfo(
            path='/users/{id}',
            method='GET',
            function_name='get_user',
            module='users',
            description='Get user by ID',
            parameters=[
                Parameter(name='id', type='int', required=True, description='User ID', location='path'),
                Parameter(name='email', type='str', required=True, description='User email', location='query')
            ],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['user'],
            dependencies=[]
        )
        
        error_examples = self.generator.create_error_examples(endpoint)
        
        # Should have multiple error examples
        assert len(error_examples) >= 2  # Auth error + validation error + not found error
        
        # Check for auth error
        auth_errors = [ex for ex in error_examples if ex.response['status_code'] == 401]
        assert len(auth_errors) > 0
        
        # Check for validation error
        validation_errors = [ex for ex in error_examples if ex.response['status_code'] == 422]
        assert len(validation_errors) > 0
        
        # Check for not found error
        not_found_errors = [ex for ex in error_examples if ex.response['status_code'] == 404]
        assert len(not_found_errors) > 0
    
    def test_curl_command_generation(self):
        """Test cURL command generation."""
        endpoint = EndpointInfo(
            path='/users',
            method='POST',
            function_name='create_user',
            module='users',
            description='Create new user',
            parameters=[],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['admin'],
            dependencies=[]
        )
        
        request_data = {
            'method': 'POST',
            'url': 'https://api.example.com/users',
            'headers': {'Authorization': 'Bearer YOUR_JWT_TOKEN', 'Content-Type': 'application/json'},
            'body': {'name': 'John Doe', 'email': 'john@example.com'}
        }
        
        curl_command = self.generator.generate_curl_command(endpoint, request_data)
        
        assert curl_command.startswith('curl')
        assert '-X POST' in curl_command
        assert 'Authorization: Bearer YOUR_JWT_TOKEN' in curl_command
        assert 'Content-Type: application/json' in curl_command
        assert '-d' in curl_command
        assert 'https://api.example.com/users' in curl_command
    
    def test_curl_with_auth_generation(self):
        """Test cURL command generation with authentication."""
        endpoint = EndpointInfo(
            path='/users/{id}',
            method='GET',
            function_name='get_user',
            module='users',
            description='Get user by ID',
            parameters=[
                Parameter(name='id', type='int', required=True, description='User ID', location='path')
            ],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['user'],
            dependencies=[]
        )
        
        curl_command = self.generator.generate_curl_with_auth(endpoint, 'test_token_123')
        
        assert 'curl' in curl_command
        assert '-X GET' in curl_command
        assert 'Authorization: Bearer test_token_123' in curl_command
        assert '/users/' in curl_command
        assert '-v' in curl_command  # Verbose flag should be included
    
    def test_curl_without_auth_generation(self):
        """Test cURL command generation without authentication."""
        endpoint = EndpointInfo(
            path='/users',
            method='GET',
            function_name='list_users',
            module='users',
            description='List all users',
            parameters=[],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['admin'],
            dependencies=[]
        )
        
        curl_command = self.generator.generate_curl_without_auth(endpoint)
        
        assert 'curl' in curl_command
        assert '-X GET' in curl_command
        assert 'Authorization' not in curl_command
        assert 'https://api.example.com/users' in curl_command
    
    def test_curl_with_custom_data(self):
        """Test cURL command generation with custom data."""
        endpoint = EndpointInfo(
            path='/users',
            method='POST',
            function_name='create_user',
            module='users',
            description='Create new user',
            parameters=[],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['admin'],
            dependencies=[]
        )
        
        custom_data = {
            'body': {'name': 'Custom User', 'email': 'custom@example.com'},
            'headers': {'X-Custom-Header': 'custom_value'}
        }
        
        curl_command = self.generator.generate_curl_with_custom_data(endpoint, custom_data)
        
        assert 'curl' in curl_command
        assert '-X POST' in curl_command
        assert 'Custom User' in curl_command
        assert 'custom@example.com' in curl_command
        assert 'X-Custom-Header: custom_value' in curl_command
    
    def test_curl_formatting_for_documentation(self):
        """Test cURL command formatting for documentation."""
        curl_command = 'curl -X POST -H "Authorization: Bearer token" -H "Content-Type: application/json" -d \'{"name":"test"}\' "https://api.example.com/users"'
        
        formatted = self.generator.format_curl_for_documentation(curl_command)
        
        assert 'curl' in formatted
        assert '\\' in formatted  # Should have line continuation characters
        assert '\n' in formatted  # Should be multi-line
        lines = formatted.split('\n')
        assert len(lines) > 1  # Should be multiple lines
    
    def test_curl_examples_set_generation(self):
        """Test generation of complete cURL examples set."""
        endpoint = EndpointInfo(
            path='/users/{id}',
            method='PUT',
            function_name='update_user',
            module='users',
            description='Update user',
            parameters=[
                Parameter(name='id', type='int', required=True, description='User ID', location='path'),
                Parameter(name='email', type='str', required=True, description='Email', location='body')
            ],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=['admin'],
            dependencies=[]
        )
        
        examples_set = self.generator.generate_curl_examples_set(endpoint)
        
        # Should have success example
        assert 'success' in examples_set
        assert 'curl' in examples_set['success']
        assert 'Authorization' in examples_set['success']
        
        # Should have auth error example
        assert 'auth_error' in examples_set
        assert 'curl' in examples_set['auth_error']
        assert 'Authorization' not in examples_set['auth_error']
        
        # Should have validation error example
        assert 'validation_error' in examples_set
        assert 'curl' in examples_set['validation_error']
        
        # Should have custom data example for PUT method
        assert 'custom_data' in examples_set
        assert 'curl' in examples_set['custom_data']
        assert 'Custom Example' in examples_set['custom_data']
    
    def test_curl_with_query_parameters(self):
        """Test cURL command generation with query parameters."""
        endpoint = EndpointInfo(
            path='/users',
            method='GET',
            function_name='list_users',
            module='users',
            description='List users with filters',
            parameters=[
                Parameter(name='limit', type='int', required=False, description='Limit results', location='query'),
                Parameter(name='offset', type='int', required=False, description='Offset results', location='query')
            ],
            request_body=None,
            response_model=None,
            auth_required=False,
            roles_required=[],
            dependencies=[]
        )
        
        request_data = self.generator._generate_request_data(endpoint)
        curl_command = self.generator.generate_curl_command(endpoint, request_data)
        
        assert 'curl' in curl_command
        assert '-X GET' in curl_command
        assert 'limit=' in curl_command
        assert 'offset=' in curl_command
        assert '?' in curl_command  # Should have query string
    
    def test_curl_with_path_parameters(self):
        """Test cURL command generation with path parameters."""
        endpoint = EndpointInfo(
            path='/users/{user_id}/posts/{post_id}',
            method='GET',
            function_name='get_user_post',
            module='users',
            description='Get specific user post',
            parameters=[
                Parameter(name='user_id', type='int', required=True, description='User ID', location='path'),
                Parameter(name='post_id', type='int', required=True, description='Post ID', location='path')
            ],
            request_body=None,
            response_model=None,
            auth_required=False,
            roles_required=[],
            dependencies=[]
        )
        
        request_data = self.generator._generate_request_data(endpoint)
        curl_command = self.generator.generate_curl_command(endpoint, request_data)
        
        assert 'curl' in curl_command
        assert '-X GET' in curl_command
        assert '/users/123/posts/123' in curl_command  # Path params should be replaced
        assert '{user_id}' not in curl_command  # Template should be replaced
        assert '{post_id}' not in curl_command  # Template should be replaced
    
    def test_curl_with_headers(self):
        """Test cURL command generation with custom headers."""
        endpoint = EndpointInfo(
            path='/users',
            method='GET',
            function_name='list_users',
            module='users',
            description='List users',
            parameters=[
                Parameter(name='Accept-Language', type='str', required=False, description='Language', location='header')
            ],
            request_body=None,
            response_model=None,
            auth_required=True,
            roles_required=[],
            dependencies=[]
        )
        
        request_data = self.generator._generate_request_data(endpoint)
        curl_command = self.generator.generate_curl_command(endpoint, request_data)
        
        assert 'curl' in curl_command
        assert '-H' in curl_command
        assert 'Accept-Language' in curl_command
        assert 'Authorization' in curl_command
    
    def test_parameter_value_generation(self):
        """Test parameter value generation based on type and name."""
        test_cases = [
            (Parameter('user_id', 'int', True, 'User ID', 'path'), int),
            (Parameter('email', 'str', True, 'Email address', 'query'), str),
            (Parameter('name', 'string', False, 'User name', 'body'), str),
            (Parameter('active', 'bool', False, 'Is active', 'query'), bool),
            (Parameter('limit', 'integer', False, 'Limit results', 'query'), int),
            (Parameter('score', 'float', False, 'Score value', 'body'), float)
        ]
        
        for param, expected_type in test_cases:
            value = self.generator._generate_parameter_value(param)
            assert isinstance(value, expected_type), \
                f"Parameter {param.name} of type {param.type} should generate {expected_type}, got {type(value)}"
            
            # Check specific value patterns
            if 'id' in param.name.lower():
                assert isinstance(value, int) and value > 0
            elif 'email' in param.name.lower():
                assert '@' in str(value)
            elif 'limit' in param.name.lower():
                assert isinstance(value, int) and value >= 0