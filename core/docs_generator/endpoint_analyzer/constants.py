"""
Constants for endpoint analyzer.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModuleMappings:
    """Module mappings for endpoint paths."""
    PATH_TO_MODULE: Dict[str, str] = None
    MODULE_KEYWORDS: Dict[str, str] = None
    
    def __post_init__(self):
        if self.PATH_TO_MODULE is None:
            self.PATH_TO_MODULE = {
                '/specialties': 'specialties',
                '/groups': 'groups',
                '/teachers': 'teachers',
                '/disciplines': 'disciplines',
                '/timetable': 'timetable',
                '/users': 'users',
                '/n8n': 'n8n_ui',
                '/search': 'elastic_search',
                '/ttable_versions': 'ttable_versions'
            }
        
        if self.MODULE_KEYWORDS is None:
            self.MODULE_KEYWORDS = {
                'specialties': 'specialties',
                'groups': 'groups',
                'teachers': 'teachers',
                'disciplines': 'disciplines',
                'timetable': 'timetable',
                'users': 'users',
                'n8n': 'n8n_ui',
                'elastic_search': 'elastic_search'
            }


@dataclass
class ParameterTypes:
    """Parameter location types."""
    PATH: str = 'path'
    QUERY: str = 'query'
    HEADER: str = 'header'
    BODY: str = 'body'


@dataclass
class CommonParameters:
    """Common FastAPI parameter names to skip."""
    SKIP_PARAMS: List[str] = None
    
    def __post_init__(self):
        if self.SKIP_PARAMS is None:
            self.SKIP_PARAMS = ['request', 'db', '_', 'response']


# Создаем экземпляры для использования
MODULE_MAPPINGS = ModuleMappings()
PARAMETER_TYPES = ParameterTypes()
COMMON_PARAMETERS = CommonParameters()