"""
Data models for SQL analyzer.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SQLQueryInfo:
    """Information about a SQL query."""
    query: str
    method_name: str
    class_name: str
    module: str
    tables: List[str]
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE