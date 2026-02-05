"""
Constants and mappings for dependency analysis.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DependencyKeywords:
    """Keywords for identifying different types of dependencies."""
    DATABASE_KEYWORDS: List[str] = None
    CACHE_KEYWORDS: List[str] = None
    SEARCH_KEYWORDS: List[str] = None
    SQL_KEYWORDS: List[str] = None
    
    def __post_init__(self):
        if self.DATABASE_KEYWORDS is None:
            self.DATABASE_KEYWORDS = ['query', 'fetch', 'execute', 'select', 'insert', 'update', 'delete']
        if self.CACHE_KEYWORDS is None:
            self.CACHE_KEYWORDS = ['redis', 'cache']
        if self.SEARCH_KEYWORDS is None:
            self.SEARCH_KEYWORDS = ['elastic', 'search']
        if self.SQL_KEYWORDS is None:
            self.SQL_KEYWORDS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']


@dataclass
class TableToClassMapping:
    """Mapping of table names to their corresponding queries classes."""
    MAPPINGS: Dict[str, str] = None
    
    def __post_init__(self):
        if self.MAPPINGS is None:
            self.MAPPINGS = {
                'groups': 'core.data.sql_queries.groups_sql.GroupsQueries',
                'specialties': 'core.data.sql_queries.specialties_sql.SpecsQueries',
                'teachers': 'core.data.sql_queries.teachers_sql.TeachersQueries',
                'ttable': 'core.data.sql_queries.ttable_sql.TimetableQueries',
                'users': 'core.data.sql_queries.users_sql.UsersQueries',
                'auth': 'core.data.sql_queries.users_sql.AuthQueries',
                'n8n_ui': 'core.data.sql_queries.n8n_iu_sql.N8NIUQueries'
            }


@dataclass
class MiddlewareTypes:
    """Types of middleware that can be applied to endpoints."""
    AUTH_MIDDLEWARE: str = 'AuthUXASGIMiddleware'
    LOGGING_MIDDLEWARE: str = 'LoggingTimeMiddleware'
    ROLE_MIDDLEWARE: str = 'RoleRequirementMiddleware'


@dataclass
class DependencyTypes:
    """Types of dependencies that can be identified."""
    FUNCTION: str = 'function'
    DATABASE: str = 'database'
    EXTERNAL_SERVICE: str = 'external_service'
    FASTAPI_DEPENDENCY: str = 'fastapi_dependency'


@dataclass
class ServiceNames:
    """Names of external services."""
    REDIS: str = 'Redis'
    ELASTICSEARCH: str = 'Elasticsearch'
    POSTGRESQL: str = 'PostgreSQL'


# Create instances for easy access
DEPENDENCY_KEYWORDS = DependencyKeywords()
TABLE_TO_CLASS_MAPPING = TableToClassMapping()
MIDDLEWARE_TYPES = MiddlewareTypes()
DEPENDENCY_TYPES = DependencyTypes()
SERVICE_NAMES = ServiceNames()