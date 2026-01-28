"""
Main SQL analyzer class.
"""

import importlib
from typing import List, Dict, Set

from .models import SQLQueryInfo
from .constants import QUERIES_CLASSES
from .handlers import extract_queries_from_class
from ..models import Dependency


class SQLAnalyzer:
    """Analyzes SQL queries from *Queries classes."""
    
    def __init__(self):
        self.queries_cache: Dict[str, List[SQLQueryInfo]] = {}
        self.queries_classes = QUERIES_CLASSES.CLASSES
    
    def extract_queries_from_classes(self) -> Dict[str, List[SQLQueryInfo]]:
        """Extract all SQL queries from *Queries classes."""
        all_queries = {}
        
        for class_path in self.queries_classes:
            try:
                module_path, class_name = class_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                queries_class = getattr(module, class_name)
                
                queries = extract_queries_from_class(queries_class, module_path)
                if queries:
                    all_queries[class_name] = queries
                    
            except (ImportError, AttributeError) as e:
                # Skip classes that can't be imported
                continue
        
        return all_queries
    
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