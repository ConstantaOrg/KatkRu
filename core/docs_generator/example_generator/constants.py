"""
Constants for example generator.
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class HttpStatusCodes:
    """HTTP status codes for examples."""
    SUCCESS = 200
    CREATED = 201
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    VALIDATION_ERROR = 422
    INTERNAL_ERROR = 500


@dataclass
class ContentTypes:
    """Content types for HTTP requests/responses."""
    JSON = "application/json"
    FORM_DATA = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    TEXT = "text/plain"


@dataclass
class ParameterTypeExamples:
    """Example values for different parameter types."""
    STRING_EXAMPLES = {
        'str': 'example_string',
        'string': 'example_string'
    }
    
    NUMERIC_EXAMPLES = {
        'int': 123,
        'integer': 123,
        'float': 123.45,
        'number': 123.45
    }
    
    BOOLEAN_EXAMPLES = {
        'bool': True,
        'boolean': True
    }
    
    COLLECTION_EXAMPLES = {
        'list': ['item1', 'item2'],
        'array': ['item1', 'item2'],
        'dict': {'key': 'value'},
        'object': {'key': 'value'}
    }


@dataclass
class SpecialParameterNames:
    """Special parameter names with specific example values."""
    ID_PATTERNS = ['id', 'user_id', 'post_id', 'item_id']
    EMAIL_PATTERNS = ['email', 'user_email', 'contact_email']
    NAME_PATTERNS = ['name', 'username', 'full_name', 'display_name']
    PAGINATION_PATTERNS = ['limit', 'offset', 'page', 'per_page']
    
    EXAMPLES = {
        'id': 123,
        'email': 'user@example.com',
        'name': 'Example Name',
        'limit': 10,
        'offset': 0,
        'page': 1
    }


@dataclass
class ErrorTemplates:
    """Templates for error response examples."""
    UNAUTHORIZED = {
        "error": "Unauthorized",
        "message": "Authentication required"
    }
    
    VALIDATION_ERROR = {
        "error": "Validation Error",
        "message": "Required parameters missing",
        "details": [
            {
                "field": "required_field",
                "message": "This field is required"
            }
        ]
    }
    
    NOT_FOUND = {
        "error": "Not Found",
        "message": "Resource not found"
    }
    
    INTERNAL_ERROR = {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }


@dataclass
class ResponseTemplates:
    """Templates for success response examples."""
    GET_SINGLE = {
        "id": 123,
        "name": "Example Item",
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    GET_LIST = {
        "data": [
            {"id": 1, "name": "Example Item 1"},
            {"id": 2, "name": "Example Item 2"}
        ],
        "total": 2
    }
    
    POST_CREATED = {
        "id": 123,
        "message": "Resource created successfully",
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    PUT_UPDATED = {
        "id": 123,
        "message": "Resource updated successfully",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    DELETE_SUCCESS = {
        "message": "Resource deleted successfully"
    }


@dataclass
class CurlTemplates:
    """Templates for cURL command generation."""
    BASE_COMMAND = "curl"
    VERBOSE_FLAG = "-v"
    METHOD_FLAG = "-X"
    HEADER_FLAG = "-H"
    DATA_FLAG = "-d"
    
    AUTH_HEADER_TEMPLATE = "Authorization: Bearer {token}"
    CONTENT_TYPE_HEADER = "Content-Type: application/json"
    
    DEFAULT_TOKEN = "YOUR_JWT_TOKEN"
    
    MULTILINE_SEPARATOR = " \\"
    LINE_INDENT = "  "