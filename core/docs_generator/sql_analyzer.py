"""
SQL query analyzer for extracting and analyzing database queries.
"""

import ast
import inspect
import importlib
from typing import List, Dict, Set, Optional, Callable, Any
from dataclasses import dataclass

from .models import Dependency


@dataclass
class SQLQueryInfo:
    """Information about a SQL query."""
    query: str
    method_name: str
    class_name: str
    module: str
    tables: List[str]
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE


class SQLAnalyzer:
    """Analyzes SQL queries from *Queries classes."""
    
    def __init__(self):
        self.queries_cache: Dict[str, List[SQLQueryInfo]] = {}
        self.queries_classes = [
            'core.data.sql_queries.groups_sql.GroupsQueries',
            'core.data.sql_queries.specialties_sql.SpecsQueries',
            'core.data.sql_queries.teachers_sql.TeachersQueries',
            'core.data.sql_queries.ttable_sql.TimetableQueries',
            'core.data.sql_queries.users_sql.UsersQueries',
            'core.data.sql_queries.users_sql.AuthQueries',
            'core.data.sql_queries.n8n_iu_sql.N8NIUQueries'
        ]
    
    def extract_queries_from_classes(self) -> Dict[str, List[SQLQueryInfo]]:
        """Extract all SQL queries from *Queries classes."""
        all_queries = {}
        
        for class_path in self.queries_classes:
            try:
                module_path, class_name = class_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                queries_class = getattr(module, class_name)
                
                queries = self._extract_queries_from_class(queries_class, module_path)
                if queries:
                    all_queries[class_name] = queries
                    
            except (ImportError, AttributeError) as e:
                # Skip classes that can't be imported
                continue
        
        return all_queries
    
    def _extract_queries_from_class(self, queries_class: type, module_path: str) -> List[SQLQueryInfo]:
        """Extract SQL queries from a specific queries class."""
        queries = []
        
        # Get all methods from the class
        for method_name in dir(queries_class):
            if method_name.startswith('_'):
                continue
                
            method = getattr(queries_class, method_name)
            if not callable(method):
                continue
            
            # Extract queries from this method
            method_queries = self._extract_queries_from_method(
                method, method_name, queries_class.__name__, module_path
            )
            queries.extend(method_queries)
        
        return queries
    
    def _extract_queries_from_method(self, method: Callable, method_name: str, 
                                   class_name: str, module_path: str) -> List[SQLQueryInfo]:
        """Extract SQL queries from a specific method."""
        queries = []
        
        try:
            # Get method source code
            source = inspect.getsource(method)
            tree = ast.parse(source)
            
            # Visit all nodes to find SQL queries
            visitor = SQLQueryVisitor()
            visitor.visit(tree)
            
            # Convert found queries to SQLQueryInfo objects
            for query_text in visitor.sql_queries:
                query_info = SQLQueryInfo(
                    query=query_text,
                    method_name=method_name,
                    class_name=class_name,
                    module=module_path,
                    tables=self._extract_tables_from_query(query_text),
                    operation_type=self._get_operation_type(query_text)
                )
                queries.append(query_info)
                
        except (OSError, TypeError, SyntaxError):
            # If we can't get source code, skip this method
            pass
        
        return queries
    
    def _extract_tables_from_query(self, query: str) -> List[str]:
        """Extract table names from a SQL query."""
        tables = set()
        query_upper = query.upper().strip()
        
        # Remove comments and normalize whitespace
        lines = [line.strip() for line in query_upper.split('\n') 
                if line.strip() and not line.strip().startswith('--')]
        query_clean = ' '.join(lines)
        
        # Find tables in FROM clauses
        if ' FROM ' in query_clean:
            parts = query_clean.split(' FROM ')
            for i in range(1, len(parts)):
                # Get the part after FROM
                from_part = parts[i]
                # Split by common SQL keywords to isolate table name
                for keyword in [' WHERE ', ' JOIN ', ' LEFT ', ' RIGHT ', ' INNER ', 
                              ' OUTER ', ' GROUP ', ' ORDER ', ' HAVING ', ' LIMIT ', ' OFFSET ']:
                    from_part = from_part.split(keyword)[0]
                
                # Extract table name (first word, remove aliases)
                table_candidates = from_part.strip().split()
                if table_candidates:
                    table_name = table_candidates[0].strip(',')
                    if table_name and not table_name.startswith('('):
                        tables.add(table_name.lower())
        
        # Find tables in INSERT INTO clauses
        if 'INSERT INTO ' in query_clean:
            parts = query_clean.split('INSERT INTO ')
            for i in range(1, len(parts)):
                table_part = parts[i].split()[0]
                table_name = table_part.split('(')[0].strip()
                if table_name:
                    tables.add(table_name.lower())
        
        # Find tables in UPDATE clauses
        if 'UPDATE ' in query_clean:
            parts = query_clean.split('UPDATE ')
            for i in range(1, len(parts)):
                table_candidates = parts[i].split()
                if table_candidates:
                    table_name = table_candidates[0].strip()
                    if table_name and table_name != 'SET':
                        tables.add(table_name.lower())
        
        # Find tables in JOIN clauses
        join_keywords = [' JOIN ', ' LEFT JOIN ', ' RIGHT JOIN ', ' INNER JOIN ', ' OUTER JOIN ']
        for join_keyword in join_keywords:
            if join_keyword in query_clean:
                parts = query_clean.split(join_keyword)
                for i in range(1, len(parts)):
                    table_candidates = parts[i].split()
                    if table_candidates:
                        table_name = table_candidates[0].strip()
                        if table_name and not table_name.startswith('('):
                            tables.add(table_name.lower())
        
        return list(tables)
    
    def _get_operation_type(self, query: str) -> str:
        """Determine the operation type of a SQL query."""
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'UNKNOWN'
    
    def link_queries_to_endpoints(self, endpoint_dependencies: List[Dependency]) -> List[SQLQueryInfo]:
        """Link SQL queries to endpoints through dependency chain."""
        linked_queries = []
        
        # Get all queries from classes
        all_queries = self.extract_queries_from_classes()
        
        # Check which queries are used by the endpoint dependencies
        for dependency in endpoint_dependencies:
            # Check if dependency is related to database operations
            if dependency.type in ['database', 'function']:
                # Look for matching queries based on dependency name
                for class_name, queries in all_queries.items():
                    for query_info in queries:
                        # Match by method name or class name
                        if (dependency.name in query_info.method_name or 
                            query_info.method_name in dependency.name or
                            class_name.lower() in dependency.name.lower()):
                            linked_queries.append(query_info)
        
        return linked_queries
    
    def get_all_database_tables(self) -> Set[str]:
        """Get all database tables used across all queries."""
        tables = set()
        all_queries = self.extract_queries_from_classes()
        
        for queries_list in all_queries.values():
            for query_info in queries_list:
                tables.update(query_info.tables)
        
        return tables


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
        if not isinstance(text, str) or len(text.strip()) < 10:
            return False
        
        text_upper = text.upper().strip()
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        # Check if it starts with SQL keywords and contains common SQL patterns
        starts_with_sql = any(text_upper.startswith(keyword) for keyword in sql_keywords)
        has_sql_patterns = any(pattern in text_upper for pattern in [' FROM ', ' WHERE ', ' SET ', ' VALUES '])
        
        return starts_with_sql and (has_sql_patterns or len(text_upper) > 50)