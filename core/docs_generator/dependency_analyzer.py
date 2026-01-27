"""
Dependency analyzer for tracing function calls and dependencies.
"""

import ast
import inspect
import importlib
from typing import List, Dict, Set, Optional, Callable, Any
from fastapi.routing import APIRoute
from fastapi.dependencies.utils import get_dependant

from .models import Dependency, DependencyChain, EndpointInfo
from .sql_analyzer import SQLAnalyzer


class DependencyAnalyzer:
    """Analyzes dependencies and traces function call chains."""
    
    def __init__(self):
        self.analyzed_functions: Set[str] = set()
        self.sql_queries_cache: Dict[str, List[str]] = {}
        self.middleware_cache: List[str] = []
        self.sql_analyzer = SQLAnalyzer()
    
    def trace_function_calls(self, func: Callable) -> List[Dependency]:
        """Trace all function calls within a given function."""
        dependencies = []
        
        if not func or not hasattr(func, '__code__'):
            return dependencies
        
        func_key = f"{func.__module__}.{func.__name__}"
        if func_key in self.analyzed_functions:
            return dependencies
        
        self.analyzed_functions.add(func_key)
        
        try:
            # Get function source code
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            # Visit all nodes to find function calls
            visitor = FunctionCallVisitor()
            visitor.visit(tree)
            
            # Convert found calls to Dependency objects
            for call_info in visitor.function_calls:
                dependency = self._create_dependency_from_call(call_info, func)
                if dependency:
                    dependencies.append(dependency)
            
        except (OSError, TypeError, SyntaxError):
            # If we can't get source code, try to analyze through inspection
            dependencies.extend(self._analyze_through_inspection(func))
        
        return dependencies
    
    def analyze_fastapi_dependencies(self, route: APIRoute) -> List[Dependency]:
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
                        type='fastapi_dependency',
                        module=getattr(dep.call, '__module__', 'unknown'),
                        description=f"FastAPI dependency: {getattr(dep.call, '__name__', str(dep.call))}"
                    )
                    dependencies.append(dependency)
            
            # Analyze sub-dependencies recursively
            for dep in dependant.dependencies:
                if dep.call and hasattr(dep.call, '__code__'):
                    sub_deps = self.trace_function_calls(dep.call)
                    dependencies.extend(sub_deps)
        
        except Exception:
            # If dependency analysis fails, continue without it
            pass
        
        return dependencies
    
    def identify_middleware(self, route: APIRoute) -> List[str]:
        """Identify middleware that applies to a specific endpoint."""
        middleware = []
        
        # Check if route requires authentication (indicates AuthUXASGIMiddleware)
        if '/private/' in route.path:
            middleware.append('AuthUXASGIMiddleware')
        
        # All routes go through LoggingTimeMiddleware
        middleware.append('LoggingTimeMiddleware')
        
        # Check for role-based middleware
        if route.endpoint:
            try:
                dependant = get_dependant(path=route.path, call=route.endpoint)
                for dep in dependant.dependencies:
                    if dep.call and hasattr(dep.call, '__name__'):
                        if 'role_require' in dep.call.__name__:
                            middleware.append('RoleRequirementMiddleware')
                            break
            except Exception:
                pass
        
        return middleware
    
    def extract_sql_queries(self, func: Callable) -> List[str]:
        """Extract SQL queries from function calls."""
        queries = []
        
        if not func or not hasattr(func, '__code__'):
            return queries
        
        func_key = f"{func.__module__}.{func.__name__}"
        if func_key in self.sql_queries_cache:
            return self.sql_queries_cache[func_key]
        
        try:
            # Get function source code
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            # Visit all nodes to find SQL queries
            visitor = SQLQueryVisitor()
            visitor.visit(tree)
            
            queries = visitor.sql_queries
            
            # Also check for queries through database method calls
            queries.extend(self._find_queries_through_db_calls(func))
            
            self.sql_queries_cache[func_key] = queries
            
        except (OSError, TypeError, SyntaxError):
            # If we can't get source code, try to find queries through call tracing
            queries = self._find_queries_through_calls(func)
            self.sql_queries_cache[func_key] = queries
        
        return queries
    
    def _find_queries_through_db_calls(self, func: Callable) -> List[str]:
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
                    query = self._find_query_in_class(table_name, method_name)
                    if query:
                        queries.append(query)
            
        except (OSError, TypeError, SyntaxError):
            pass
        
        return queries
    
    def _find_query_in_class(self, table_name: str, method_name: str) -> Optional[str]:
        """Find a specific query in a queries class."""
        # Map table names to queries classes
        table_to_class = {
            'groups': 'core.data.sql_queries.groups_sql.GroupsQueries',
            'specialties': 'core.data.sql_queries.specialties_sql.SpecsQueries',
            'teachers': 'core.data.sql_queries.teachers_sql.TeachersQueries',
            'ttable': 'core.data.sql_queries.ttable_sql.TimetableQueries',
            'users': 'core.data.sql_queries.users_sql.UsersQueries',
            'auth': 'core.data.sql_queries.users_sql.AuthQueries',
            'n8n_ui': 'core.data.sql_queries.n8n_iu_sql.N8NIUQueries'
        }
        
        class_path = table_to_class.get(table_name)
        if not class_path:
            return None
        
        try:
            # Get all queries from the SQL analyzer
            all_queries = self.sql_analyzer.extract_queries_from_classes()
            
            # Find the specific query
            class_name = class_path.split('.')[-1]
            if class_name in all_queries:
                for query_info in all_queries[class_name]:
                    if query_info.method_name == method_name:
                        return query_info.query
        except Exception:
            pass
        
        return None
    
    def analyze_database_tables(self, queries: List[str]) -> List[str]:
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
    
    def trace_dependency_chain(self, endpoint_info: EndpointInfo) -> DependencyChain:
        """Trace the complete dependency chain for an endpoint."""
        # Get the endpoint function from the route
        endpoint_func = None
        
        # Try to find the function by name in the module
        try:
            if endpoint_info.module and endpoint_info.function_name:
                module_path = f"core.api.{endpoint_info.module}"
                if endpoint_info.module == 'elastic_search':
                    module_path = "core.api.elastic_search"
                elif endpoint_info.module == 'n8n_ui':
                    module_path = "core.api.n8n_ui"
                elif endpoint_info.module == 'ttable_versions':
                    module_path = "core.api.ttable_versions_tab"
                elif endpoint_info.module == 'timetable':
                    module_path = "core.api.timetable.timetable_api"
                elif endpoint_info.module == 'users':
                    module_path = "core.api.users.users_api"
                
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
            deps = self.trace_function_calls(endpoint_func)
            direct_dependencies = [dep.name for dep in deps]
            
            # Extract SQL queries
            queries = self.extract_sql_queries(endpoint_func)
            database_queries = queries
            
            # Identify external services
            for dep in deps:
                if 'redis' in dep.name.lower() or 'redis' in dep.module.lower():
                    external_services.append('Redis')
                elif 'elastic' in dep.name.lower() or 'elastic' in dep.module.lower():
                    external_services.append('Elasticsearch')
                elif 'postgre' in dep.name.lower() or 'postgre' in dep.module.lower():
                    external_services.append('PostgreSQL')
            
            # Get schemas from endpoint info
            if endpoint_info.request_body:
                schemas.append(endpoint_info.request_body.__name__)
            if endpoint_info.response_model:
                schemas.append(endpoint_info.response_model.__name__)
        
        # Get middleware (this would need route information)
        middleware = ['LoggingTimeMiddleware']
        if endpoint_info.auth_required:
            middleware.append('AuthUXASGIMiddleware')
        if endpoint_info.roles_required:
            middleware.append('RoleRequirementMiddleware')
        
        return DependencyChain(
            endpoint=f"{endpoint_info.method} {endpoint_info.path}",
            direct_dependencies=direct_dependencies,
            database_queries=database_queries,
            external_services=list(set(external_services)),
            middleware=middleware,
            schemas=schemas
        )
    
    def _create_dependency_from_call(self, call_info: Dict[str, Any], parent_func: Callable) -> Optional[Dependency]:
        """Create a Dependency object from call information."""
        try:
            func_name = call_info.get('name', '')
            attr_name = call_info.get('attr', '')
            
            # Determine dependency type
            dep_type = 'function'
            if attr_name:
                if any(keyword in attr_name.lower() for keyword in ['query', 'fetch', 'execute']):
                    dep_type = 'database'
                elif any(keyword in attr_name.lower() for keyword in ['redis', 'cache']):
                    dep_type = 'external_service'
                elif any(keyword in attr_name.lower() for keyword in ['elastic', 'search']):
                    dep_type = 'external_service'
            
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
    
    def _analyze_through_inspection(self, func: Callable) -> List[Dependency]:
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
                            name='PostgreSQL',
                            type='database',
                            module='core.data.postgre',
                            description='PostgreSQL database dependency'
                        ))
                    elif 'Redis' in annotation_str:
                        dependencies.append(Dependency(
                            name='Redis',
                            type='external_service',
                            module='core.data.redis_storage',
                            description='Redis cache dependency'
                        ))
        except Exception:
            pass
        
        return dependencies
    
    def _find_queries_through_calls(self, func: Callable) -> List[str]:
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


class FunctionCallVisitor(ast.NodeVisitor):
    """AST visitor to find function calls in source code."""
    
    def __init__(self):
        self.function_calls = []
    
    def visit_Call(self, node):
        """Visit function call nodes."""
        call_info = {}
        
        if isinstance(node.func, ast.Name):
            call_info['name'] = node.func.id
        elif isinstance(node.func, ast.Attribute):
            call_info['name'] = self._get_full_name(node.func.value)
            call_info['attr'] = node.func.attr
        
        if call_info:
            self.function_calls.append(call_info)
        
        self.generic_visit(node)
    
    def _get_full_name(self, node):
        """Get the full name of a nested attribute access."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_full_name(node.value)}.{node.attr}"
        else:
            return "unknown"


class DatabaseCallVisitor(ast.NodeVisitor):
    """AST visitor to find database method calls like db.groups.get_all()."""
    
    def __init__(self):
        self.db_calls = []
    
    def visit_Call(self, node):
        """Visit function call nodes to find database calls."""
        if isinstance(node.func, ast.Attribute):
            # Check for patterns like db.table.method()
            if isinstance(node.func.value, ast.Attribute):
                if isinstance(node.func.value.value, ast.Name):
                    if node.func.value.value.id == 'db':
                        call_info = {
                            'table': node.func.value.attr,
                            'method': node.func.attr
                        }
                        self.db_calls.append(call_info)
        
        self.generic_visit(node)


class SQLQueryVisitor(ast.NodeVisitor):
    """AST visitor to find SQL queries in source code."""
    
    def __init__(self):
        self.sql_queries = []
    
    def visit_Str(self, node):
        """Visit string nodes that might contain SQL queries."""
        if self._is_sql_query(node.s):
            self.sql_queries.append(node.s.strip())
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Visit constant nodes (Python 3.8+) that might contain SQL queries."""
        if isinstance(node.value, str) and self._is_sql_query(node.value):
            self.sql_queries.append(node.value.strip())
        self.generic_visit(node)
    
    def _is_sql_query(self, text: str) -> bool:
        """Check if a string looks like a SQL query."""
        if not isinstance(text, str):
            return False
        
        text_upper = text.upper().strip()
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        return any(text_upper.startswith(keyword) for keyword in sql_keywords)