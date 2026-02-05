"""
Handler functions for SQL analysis operations.
"""

import ast
import inspect
from typing import List, Callable, Set

from .models import SQLQueryInfo
from .constants import SQL_KEYWORDS


def extract_queries_from_class(queries_class: type, module_path: str) -> List[SQLQueryInfo]:
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
        method_queries = extract_queries_from_method(
            method, method_name, queries_class.__name__, module_path
        )
        queries.extend(method_queries)
    
    return queries


def extract_queries_from_method(method: Callable, method_name: str, 
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
                tables=extract_tables_from_query(query_text),
                operation_type=get_operation_type(query_text)
            )
            queries.append(query_info)
            
    except (OSError, TypeError, SyntaxError):
        # If we can't get source code, skip this method
        pass
    
    return queries


def extract_tables_from_query(query: str) -> List[str]:
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
            for keyword in SQL_KEYWORDS.SPLIT_KEYWORDS:
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
    for join_keyword in SQL_KEYWORDS.JOIN_KEYWORDS:
        if join_keyword in query_clean:
            parts = query_clean.split(join_keyword)
            for i in range(1, len(parts)):
                table_candidates = parts[i].split()
                if table_candidates:
                    table_name = table_candidates[0].strip()
                    if table_name and not table_name.startswith('('):
                        tables.add(table_name.lower())
    
    return list(tables)


def get_operation_type(query: str) -> str:
    """Determine the operation type of a SQL query."""
    query_upper = query.upper().strip()

    for operation in SQL_KEYWORDS.OPERATIONS:
        if query_upper.startswith(operation):
            return operation
    
    return 'UNKNOWN'


def is_sql_query(text: str) -> bool:
    """Check if a string looks like a SQL query."""
    if not isinstance(text, str) or len(text.strip()) < 10:
        return False
    
    text_upper = text.upper().strip()
    
    # Check if it starts with SQL keywords and contains common SQL patterns
    starts_with_sql = any(text_upper.startswith(keyword) for keyword in SQL_KEYWORDS.OPERATIONS)
    has_sql_patterns = any(pattern in text_upper for pattern in [' FROM ', ' WHERE ', ' SET ', ' VALUES '])
    
    return starts_with_sql and (has_sql_patterns or len(text_upper) > 50)


class SQLQueryVisitor(ast.NodeVisitor):
    """AST visitor to find SQL queries in source code."""
    
    def __init__(self):
        self.sql_queries = []
    
    def visit_Str(self, node):
        """Visit string nodes that might contain SQL queries."""
        if is_sql_query(node.s):
            self.sql_queries.append(node.s.strip())
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Visit constant nodes (Python 3.8+) that might contain SQL queries."""
        if isinstance(node.value, str) and is_sql_query(node.value):
            self.sql_queries.append(node.value.strip())
        self.generic_visit(node)