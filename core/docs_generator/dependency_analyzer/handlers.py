"""
Handler functions for dependency analysis operations.
"""

import ast
import inspect
import importlib
from typing import List, Dict, Set, Optional, Callable, Any
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_dependant

from ..models import Dependency, DependencyChain, EndpointInfo
from ..sql_analyzer import SQLAnalyzer
from .models import FunctionCallVisitor, DatabaseCallVisitor, SQLQueryVisitor
from .constants import (
    DEPENDENCY_KEYWORDS, TABLE_TO_CLASS_MAPPING, MIDDLEWARE_TYPES,
    DEPENDENCY_TYPES, SERVICE_NAMES
)


def trace_function_calls(func: Callable, analyzed_functions: Set[str]) -> List[Dependency]:
    """Trace all function calls within a given function."""
    dependencies = []
    
    if not func or not hasattr(func, '__code__'):
        return dependencies
    
    func_key = f"{func.__module__}.{func.__name__}"
    if func_key in analyzed_functions:
        return dependencies
    
    analyzed_functions.add(func_key)
    
    try:
        # Get function source code
        source = inspect.getsource(func)
        tree = ast.parse(source)
        
        # Visit all nodes to find function calls
        visitor = FunctionCallVisitor()
        visitor.visit(tree)
        
        # Convert found calls to Dependency objects
        for call_info in visitor.function_calls:
            dependency = create_dependency_from_call(call_info, func)
            if dependency:
                dependencies.append(dependency)
        
    except (OSError, TypeError, SyntaxError):
        # If we can't get source code, try to analyze through inspection
        dependencies.extend(analyze_through_inspection(func))
    
    return dependencies


def analyze_fastapi_dependencies(route: APIRoute) -> List[Dependency]:
    """Analyze FastAPI-specific dependencies for a route."""
    dependencies = []
    
    if not route.endpoint:
        return dependencies
    
    try:
        # Get FastAPI dependant information
        dependant = get_dependant(path=route.path, call=route.endpoint)
        
        # Analyze route dependencies
        for dep in dependant.dependencies:
            if dep.call:
                dependency = Dependency(
                    name=getattr(dep.call, '__name__', str(dep.call)),
                    type=DEPENDENCY_TYPES.FASTAPI_DEPENDENCY,
                    module=getattr(dep.call, '__module__', 'unknown'),
                    description=f"FastAPI dependency: {getattr(dep.call, '__name__', str(dep.call))}"
                )
                dependencies.append(dependency)
        
        # Analyze sub-dependencies recursively
        analyzed_functions = set()
        for dep in dependant.dependencies:
            if dep.call and hasattr(dep.call, '__code__'):
                sub_deps = trace_function_calls(dep.call, analyzed_functions)
                dependencies.extend(sub_deps)
    
    except Exception:
        # If dependency analysis fails, continue without it
        pass
    
    return dependencies


def identify_middleware(route: APIRoute) -> List[str]:
    """Identify middleware that applies to a specific endpoint."""
    middleware = []
    
    # Check if route requires authentication (indicates AuthUXASGIMiddleware)
    if '/private/' in route.path:
        middleware.append(MIDDLEWARE_TYPES.AUTH_MIDDLEWARE)
    
    # All routes go through LoggingTimeMiddleware
    middleware.append(MIDDLEWARE_TYPES.LOGGING_MIDDLEWARE)
    
    # Check for role-based middleware
    if route.endpoint:
        try:
            dependant = get_dependant(path=route.path, call=route.endpoint)
            for dep in dependant.dependencies:
                if dep.call and hasattr(dep.call, '__name__'):
                    if 'role_require' in dep.call.__name__:
                        middleware.append(MIDDLEWARE_TYPES.ROLE_MIDDLEWARE)
                        break
        except Exception:
            pass
    
    return middleware


def extract_sql_queries(func: Callable, sql_queries_cache: Dict[str, List[str]], sql_analyzer: SQLAnalyzer) -> List[str]:
    """Extract SQL queries from function calls."""
    queries = []
    
    if not func or not hasattr(func, '__code__'):
        return queries
    
    func_key = f"{func.__module__}.{func.__name__}"
    if func_key in sql_queries_cache:
        return sql_queries_cache[func_key]
    
    try:
        # Get function source code
        source = inspect.getsource(func)
        tree = ast.parse(source)
        
        # Visit all nodes to find SQL queries
        visitor = SQLQueryVisitor()
        visitor.visit(tree)
        
        queries = visitor.sql_queries
        
        # Also check for queries through database method calls
        queries.extend(find_queries_through_db_calls(func, sql_analyzer))
        
        sql_queries_cache[func_key] = queries
        
    except (OSError, TypeError, SyntaxError):
        # If we can't get source code, try to find queries through call tracing
        queries = find_queries_through_calls(func)
        sql_queries_cache[func_key] = queries
    
    return queries


def find_queries_through_db_calls(func: Callable, sql_analyzer: SQLAnalyzer) -> List[str]:
    """Find SQL queries by analyzing database method calls."""
    queries = []
    
    try:
        # Get function source code
        source = inspect.getsource(func)
        tree = ast.parse(source)
        
        # Look for database method calls like db.groups.get_all()
        visitor = DatabaseCallVisitor()
        visitor.visit(tree)
        
        # For each database call, try to find the corresponding SQL query
        for call_info in visitor.db_calls:
            table_name = call_info.get('table')
            method_name = call_info.get('method')
            
            if table_name and method_name:
                # Try to find the query in the corresponding queries class
                query = find_query_in_class(table_name, method_name, sql_analyzer)
                if query:
                    queries.append(query)
        
    except (OSError, TypeError, SyntaxError):
        pass
    
    return queries


def find_query_in_class(table_name: str, method_name: str, sql_analyzer: SQLAnalyzer) -> Optional[str]:
    """Find a specific query in a queries class."""
    class_path = TABLE_TO_CLASS_MAPPING.MAPPINGS.get(table_name)
    if not class_path:
        return None
    
    try:
        # Get all queries from the SQL analyzer
        all_queries = sql_analyzer.extract_queries_from_classes()
        
        # Find the specific query
        class_name = class_path.split('.')[-1]
        if class_name in all_queries:
            for query_info in all_queries[class_name]:
                if query_info.method_name == method_name:
                    return query_info.query
    except Exception:
        pass
    
    return None


def analyze_database_tables(queries: List[str]) -> List[str]:
    """Analyze which database tables are used in SQL queries."""
    tables = set()
    
    for query in queries:
        # Simple regex-like parsing to find table names
        query_upper = query.upper()
        
        # Find tables in FROM clauses
        if ' FROM ' in query_upper:
            parts = query_upper.split(' FROM ')
            if len(parts) > 1:
                table_part = parts[1].split()[0]
                # Remove common SQL keywords and get table name
                table_name = table_part.split(',')[0].strip()
                if table_name and not table_name.startswith('('):
                    tables.add(table_name.lower())
        
        # Find tables in INSERT INTO clauses
        if 'INSERT INTO ' in query_upper:
            parts = query_upper.split('INSERT INTO ')
            if len(parts) > 1:
                table_part = parts[1].split()[0]
                table_name = table_part.split('(')[0].strip()
                if table_name:
                    tables.add(table_name.lower())
        
        # Find tables in UPDATE clauses
        if 'UPDATE ' in query_upper:
            parts = query_upper.split('UPDATE ')
            if len(parts) > 1:
                table_part = parts[1].split()[0]
                table_name = table_part.split()[0].strip()
                if table_name and table_name != 'SET':
                    tables.add(table_name.lower())
    
    return list(tables)


def trace_dependency_chain(endpoint_info: EndpointInfo, analyzed_functions: Set[str], 
                          sql_queries_cache: Dict[str, List[str]], sql_analyzer: SQLAnalyzer) -> DependencyChain:
    """Trace the complete dependency chain for an endpoint."""
    # Get the endpoint function from the route
    endpoint_func = None
    
    # Try to find the function by name in the module
    try:
        if endpoint_info.module and endpoint_info.function_name:
            # Import constants
            from core.utils.anything import ModulePaths
            
            # Module path mapping
            module_paths = {
                'elastic_search': ModulePaths.elastic_search,
                'n8n_ui': ModulePaths.n8n_ui,
                'ttable_versions': ModulePaths.ttable_versions,
                'timetable': ModulePaths.timetable,
                'users': ModulePaths.users,
            }
            
            # Get module path or use default pattern
            module_path = module_paths.get(
                endpoint_info.module, 
                f"core.api.{endpoint_info.module}"
            )
            
            try:
                module = importlib.import_module(module_path)
                endpoint_func = getattr(module, endpoint_info.function_name, None)
            except (ImportError, AttributeError):
                pass
    except Exception:
        pass
    
    # Trace dependencies
    direct_dependencies = []
    database_queries = []
    external_services = []
    middleware = []
    schemas = []
    
    if endpoint_func:
        # Trace function calls
        deps = trace_function_calls(endpoint_func, analyzed_functions)
        direct_dependencies = [dep.name for dep in deps]
        
        # Extract SQL queries
        queries = extract_sql_queries(endpoint_func, sql_queries_cache, sql_analyzer)
        database_queries = queries
        
        # Identify external services
        for dep in deps:
            if 'redis' in dep.name.lower() or 'redis' in dep.module.lower():
                external_services.append(SERVICE_NAMES.REDIS)
            elif 'elastic' in dep.name.lower() or 'elastic' in dep.module.lower():
                external_services.append(SERVICE_NAMES.ELASTICSEARCH)
            elif 'postgre' in dep.name.lower() or 'postgre' in dep.module.lower():
                external_services.append(SERVICE_NAMES.POSTGRESQL)
        
        # Get schemas from endpoint info
        if endpoint_info.request_body:
            schemas.append(endpoint_info.request_body.__name__)
        if endpoint_info.response_model:
            schemas.append(endpoint_info.response_model.__name__)
    
    # Get middleware (this would need route information)
    middleware = [MIDDLEWARE_TYPES.LOGGING_MIDDLEWARE]
    if endpoint_info.auth_required:
        middleware.append(MIDDLEWARE_TYPES.AUTH_MIDDLEWARE)
    if endpoint_info.roles_required:
        middleware.append(MIDDLEWARE_TYPES.ROLE_MIDDLEWARE)
    
    return DependencyChain(
        endpoint=f"{endpoint_info.method} {endpoint_info.path}",
        direct_dependencies=direct_dependencies,
        database_queries=database_queries,
        external_services=list(set(external_services)),
        middleware=middleware,
        schemas=schemas
    )


def create_dependency_from_call(call_info: Dict[str, Any], parent_func: Callable) -> Optional[Dependency]:
    """Create a Dependency object from call information."""
    try:
        func_name = call_info.get('name', '')
        attr_name = call_info.get('attr', '')
        
        # Determine dependency type
        dep_type = DEPENDENCY_TYPES.FUNCTION
        if attr_name:
            if any(keyword in attr_name.lower() for keyword in DEPENDENCY_KEYWORDS.DATABASE_KEYWORDS):
                dep_type = DEPENDENCY_TYPES.DATABASE
            elif any(keyword in attr_name.lower() for keyword in DEPENDENCY_KEYWORDS.CACHE_KEYWORDS):
                dep_type = DEPENDENCY_TYPES.EXTERNAL_SERVICE
            elif any(keyword in attr_name.lower() for keyword in DEPENDENCY_KEYWORDS.SEARCH_KEYWORDS):
                dep_type = DEPENDENCY_TYPES.EXTERNAL_SERVICE
        
        # Determine module
        module = getattr(parent_func, '__module__', 'unknown')
        
        # Create description
        full_name = f"{func_name}.{attr_name}" if attr_name else func_name
        description = f"Function call: {full_name}"
        
        return Dependency(
            name=full_name,
            type=dep_type,
            module=module,
            description=description
        )
    except Exception:
        return None


def analyze_through_inspection(func: Callable) -> List[Dependency]:
    """Analyze dependencies through function inspection when source is not available."""
    dependencies = []
    
    try:
        # Get function signature
        sig = inspect.signature(func)
        
        # Analyze parameters for dependency injection patterns
        for param_name, param in sig.parameters.items():
            if param.annotation and param.annotation != inspect.Parameter.empty:
                # Check for common dependency patterns
                annotation_str = str(param.annotation)
                
                if 'PgSql' in annotation_str:
                    dependencies.append(Dependency(
                        name=SERVICE_NAMES.POSTGRESQL,
                        type=DEPENDENCY_TYPES.DATABASE,
                        module='core.data.postgre',
                        description='PostgreSQL database dependency'
                    ))
                elif 'Redis' in annotation_str:
                    dependencies.append(Dependency(
                        name=SERVICE_NAMES.REDIS,
                        type=DEPENDENCY_TYPES.EXTERNAL_SERVICE,
                        module='core.data.redis_storage',
                        description='Redis cache dependency'
                    ))
    except Exception:
        pass
    
    return dependencies


def find_queries_through_calls(func: Callable) -> List[str]:
    """Find SQL queries by tracing function calls when source is not available."""
    queries = []
    
    # This is a simplified approach - in a real implementation,
    # we might need more sophisticated analysis
    try:
        func_name = func.__name__
        module_name = func.__module__
        
        # Check if this function is likely to contain SQL queries
        if any(keyword in func_name.lower() for keyword in ['get', 'add', 'update', 'delete', 'fetch']):
            # Add a placeholder query indication
            queries.append(f"-- SQL query in {module_name}.{func_name}")
    except Exception:
        pass
    
    return queries