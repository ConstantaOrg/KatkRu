"""
Main dependency analyzer class.
"""

from typing import List, Dict, Set, Callable
from fastapi.routing import APIRoute

from ..models import Dependency, DependencyChain, EndpointInfo
from ..sql_analyzer import SQLAnalyzer
from .handlers import (
    trace_function_calls, analyze_fastapi_dependencies, identify_middleware,
    extract_sql_queries, analyze_database_tables, trace_dependency_chain
)


class DependencyAnalyzer:
    """Analyzes dependencies and traces function call chains."""
    
    def __init__(self):
        self.analyzed_functions: Set[str] = set()
        self.sql_queries_cache: Dict[str, List[str]] = {}
        self.middleware_cache: List[str] = []
        self.sql_analyzer = SQLAnalyzer()
    
    def trace_function_calls(self, func: Callable) -> List[Dependency]:
        """Trace all function calls within a given function."""
        return trace_function_calls(func, self.analyzed_functions)
    
    def analyze_fastapi_dependencies(self, route: APIRoute) -> List[Dependency]:
        """Analyze FastAPI-specific dependencies for a route."""
        return analyze_fastapi_dependencies(route)
    
    def identify_middleware(self, route: APIRoute) -> List[str]:
        """Identify middleware that applies to a specific endpoint."""
        return identify_middleware(route)
    
    def extract_sql_queries(self, func: Callable) -> List[str]:
        """Extract SQL queries from function calls."""
        return extract_sql_queries(func, self.sql_queries_cache, self.sql_analyzer)
    
    def analyze_database_tables(self, queries: List[str]) -> List[str]:
        """Analyze which database tables are used in SQL queries."""
        return analyze_database_tables(queries)
    
    def trace_dependency_chain(self, endpoint_info: EndpointInfo) -> DependencyChain:
        """Trace the complete dependency chain for an endpoint."""
        return trace_dependency_chain(
            endpoint_info, 
            self.analyzed_functions, 
            self.sql_queries_cache, 
            self.sql_analyzer
        )