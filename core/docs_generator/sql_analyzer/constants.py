"""
Constants for SQL analyzer.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SQLKeywords:
    """SQL keywords for query analysis."""
    OPERATIONS: List[str] = None
    JOIN_KEYWORDS: List[str] = None
    SPLIT_KEYWORDS: List[str] = None
    
    def __post_init__(self):
        if self.OPERATIONS is None:
            self.OPERATIONS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        if self.JOIN_KEYWORDS is None:
            self.JOIN_KEYWORDS = [' JOIN ', ' LEFT JOIN ', ' RIGHT JOIN ', ' INNER JOIN ', ' OUTER JOIN ']
        
        if self.SPLIT_KEYWORDS is None:
            self.SPLIT_KEYWORDS = [
                ' WHERE ', ' JOIN ', ' LEFT ', ' RIGHT ', ' INNER ', ' OUTER ', 
                ' GROUP ', ' ORDER ', ' HAVING ', ' LIMIT ', ' OFFSET '
            ]


@dataclass
class QueriesClasses:
    """SQL queries classes paths."""
    CLASSES: List[str] = None
    
    def __post_init__(self):
        if self.CLASSES is None:
            self.CLASSES = [
                'core.data.sql_queries.groups_sql.GroupsQueries',
                'core.data.sql_queries.specialties_sql.SpecsQueries',
                'core.data.sql_queries.teachers_sql.TeachersQueries',
                'core.data.sql_queries.ttable_sql.TimetableQueries',
                'core.data.sql_queries.users_sql.UsersQueries',
                'core.data.sql_queries.users_sql.AuthQueries',
                'core.data.sql_queries.n8n_iu_sql.N8NIUQueries'
            ]


# Создаем экземпляры для использования
SQL_KEYWORDS = SQLKeywords()
QUERIES_CLASSES = QueriesClasses()