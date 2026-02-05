"""
Models and AST visitors for dependency analysis.
"""

import ast
from typing import List, Dict, Any


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