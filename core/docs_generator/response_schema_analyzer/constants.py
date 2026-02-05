"""
Constants for response schema analyzer.
"""

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class RouterMethods:
    """HTTP methods supported by FastAPI router."""
    SUPPORTED_METHODS: Set[str] = None
    
    def __post_init__(self):
        if self.SUPPORTED_METHODS is None:
            self.SUPPORTED_METHODS = {'get', 'post', 'put', 'delete', 'patch'}


@dataclass
class SchemaPatterns:
    """Patterns for detecting response schema types."""
    RESPONSE_PATTERNS: Dict[str, str] = None
    SCHEMA_SUGGESTIONS: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.RESPONSE_PATTERNS is None:
            self.RESPONSE_PATTERNS = {
                'success': 'SuccessResponse',
                'groups': 'GroupsResponse', 
                'specialties': 'SpecialtiesResponse',
                'users': 'UsersResponse',
                'teachers': 'TeachersResponse',
                'disciplines': 'DisciplinesResponse',
                'timetable': 'TimetableResponse',
                'ttable': 'TimetableResponse',
                'n8n': 'N8NResponse',
                'cards': 'CardsResponse',
                'error': 'ErrorResponse'
            }
        
        if self.SCHEMA_SUGGESTIONS is None:
            self.SCHEMA_SUGGESTIONS = {
                'POST': ['SuccessWithIdResponse', 'CreatedResponse'],
                'PUT': ['SuccessResponse', 'UpdatedResponse'],
                'DELETE': ['SuccessResponse', 'DeletedResponse'],
                'GET': ['DataResponse', 'ListResponse']
            }


@dataclass
class FilePatterns:
    """File patterns for API analysis."""
    EXCLUDED_FILES: Set[str] = None
    EXCLUDED_DIRS: Set[str] = None
    API_FILE_EXTENSION: str = '.py'
    
    def __post_init__(self):
        if self.EXCLUDED_FILES is None:
            self.EXCLUDED_FILES = {'__init__.py', 'middleware.py'}
        
        if self.EXCLUDED_DIRS is None:
            self.EXCLUDED_DIRS = {'__pycache__', 'one_time_scripts'}


@dataclass
class SchemaNamePatterns:
    """Patterns for generating schema names."""
    FUNCTION_PREFIXES: List[str] = None
    METHOD_SUFFIXES: Dict[str, str] = None
    
    def __post_init__(self):
        if self.FUNCTION_PREFIXES is None:
            self.FUNCTION_PREFIXES = ['get_', 'add_', 'update_', 'delete_', 'create_', 'fetch_']
        
        if self.METHOD_SUFFIXES is None:
            self.METHOD_SUFFIXES = {
                'POST': 'Create',
                'PUT': 'Update', 
                'DELETE': 'Delete',
                'PATCH': 'Patch'
            }


@dataclass
class AnalysisConfig:
    """Configuration for analysis process."""
    MAX_RETURN_STATEMENTS: int = 10
    MAX_LINE_LENGTH: int = 200
    ENCODING: str = 'utf-8'


# Create instances for use
ROUTER_METHODS = RouterMethods()
SCHEMA_PATTERNS = SchemaPatterns()
FILE_PATTERNS = FilePatterns()
SCHEMA_NAME_PATTERNS = SchemaNamePatterns()
ANALYSIS_CONFIG = AnalysisConfig()