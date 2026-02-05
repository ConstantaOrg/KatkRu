"""
Constants and mappings for module documentation.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModuleDescriptions:
    """Descriptions for different API modules."""
    DESCRIPTIONS: Dict[str, str] = None
    
    def __post_init__(self):
        if self.DESCRIPTIONS is None:
            self.DESCRIPTIONS = {
                'specialties': 'Управление специальностями учебного заведения',
                'groups': 'Управление учебными группами',
                'teachers': 'Управление преподавателями',
                'disciplines': 'Управление дисциплинами',
                'timetable': 'Управление расписанием занятий',
                'users': 'Управление пользователями системы',
                'n8n_ui': 'Интерфейс для интеграции с N8N',
                'elastic_search': 'Поиск по данным системы',
                'ttable_versions': 'Управление версиями расписания',
                'middleware': 'Промежуточное ПО системы'
            }


@dataclass
class ModuleRelationships:
    """Relationships between different modules."""
    RELATIONSHIPS: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.RELATIONSHIPS is None:
            self.RELATIONSHIPS = {
                'specialties': ['groups', 'disciplines'],
                'groups': ['specialties', 'users', 'timetable'],
                'teachers': ['disciplines', 'timetable'],
                'disciplines': ['specialties', 'teachers', 'timetable'],
                'timetable': ['groups', 'teachers', 'disciplines', 'ttable_versions'],
                'users': ['groups'],
                'n8n_ui': ['specialties', 'groups', 'teachers', 'disciplines'],
                'elastic_search': ['specialties', 'groups', 'teachers', 'disciplines'],
                'ttable_versions': ['timetable'],
                'middleware': []  # Middleware affects all modules
            }


@dataclass
class PathKeywords:
    """Keywords for categorizing endpoints by path."""
    SPECIALTIES: List[str] = None
    GROUPS: List[str] = None
    TEACHERS: List[str] = None
    DISCIPLINES: List[str] = None
    TIMETABLE: List[str] = None
    USERS: List[str] = None
    N8N_UI: List[str] = None
    ELASTIC_SEARCH: List[str] = None
    TTABLE_VERSIONS: List[str] = None
    
    def __post_init__(self):
        if self.SPECIALTIES is None:
            self.SPECIALTIES = ['/specialties']
        if self.GROUPS is None:
            self.GROUPS = ['/groups']
        if self.TEACHERS is None:
            self.TEACHERS = ['/teachers']
        if self.DISCIPLINES is None:
            self.DISCIPLINES = ['/disciplines']
        if self.TIMETABLE is None:
            self.TIMETABLE = ['/timetable']
        if self.USERS is None:
            self.USERS = ['/users']
        if self.N8N_UI is None:
            self.N8N_UI = ['/n8n']
        if self.ELASTIC_SEARCH is None:
            self.ELASTIC_SEARCH = ['/search', '/elastic']
        if self.TTABLE_VERSIONS is None:
            self.TTABLE_VERSIONS = ['/ttable_versions']


@dataclass
class FunctionKeywords:
    """Keywords for categorizing endpoints by function name."""
    SPECIALTIES: List[str] = None
    GROUPS: List[str] = None
    TEACHERS: List[str] = None
    DISCIPLINES: List[str] = None
    TIMETABLE: List[str] = None
    USERS: List[str] = None
    N8N_UI: List[str] = None
    ELASTIC_SEARCH: List[str] = None
    TTABLE_VERSIONS: List[str] = None
    
    def __post_init__(self):
        if self.SPECIALTIES is None:
            self.SPECIALTIES = ['specialty', 'specialties']
        if self.GROUPS is None:
            self.GROUPS = ['group', 'groups']
        if self.TEACHERS is None:
            self.TEACHERS = ['teacher', 'teachers']
        if self.DISCIPLINES is None:
            self.DISCIPLINES = ['discipline', 'disciplines']
        if self.TIMETABLE is None:
            self.TIMETABLE = ['timetable', 'ttable']
        if self.USERS is None:
            self.USERS = ['user', 'users']
        if self.N8N_UI is None:
            self.N8N_UI = ['n8n']
        if self.ELASTIC_SEARCH is None:
            self.ELASTIC_SEARCH = ['search', 'elastic']
        if self.TTABLE_VERSIONS is None:
            self.TTABLE_VERSIONS = ['version']


@dataclass
class DependencyKeywords:
    """Keywords for identifying database tables from dependencies."""
    GROUPS: List[str] = None
    SPECIALTIES: List[str] = None
    TEACHERS: List[str] = None
    DISCIPLINES: List[str] = None
    TIMETABLE: List[str] = None
    USERS: List[str] = None
    
    def __post_init__(self):
        if self.GROUPS is None:
            self.GROUPS = ['groups']
        if self.SPECIALTIES is None:
            self.SPECIALTIES = ['specialties']
        if self.TEACHERS is None:
            self.TEACHERS = ['teachers']
        if self.DISCIPLINES is None:
            self.DISCIPLINES = ['disciplines']
        if self.TIMETABLE is None:
            self.TIMETABLE = ['timetable', 'ttable']
        if self.USERS is None:
            self.USERS = ['users']


@dataclass
class ModuleNames:
    """Standard module names."""
    SPECIALTIES: str = 'specialties'
    GROUPS: str = 'groups'
    TEACHERS: str = 'teachers'
    DISCIPLINES: str = 'disciplines'
    TIMETABLE: str = 'timetable'
    USERS: str = 'users'
    N8N_UI: str = 'n8n_ui'
    ELASTIC_SEARCH: str = 'elastic_search'
    TTABLE_VERSIONS: str = 'ttable_versions'
    MIDDLEWARE: str = 'middleware'
    MISCELLANEOUS: str = 'miscellaneous'


# Create instances for easy access
MODULE_DESCRIPTIONS = ModuleDescriptions()
MODULE_RELATIONSHIPS = ModuleRelationships()
PATH_KEYWORDS = PathKeywords()
FUNCTION_KEYWORDS = FunctionKeywords()
DEPENDENCY_KEYWORDS = DependencyKeywords()
MODULE_NAMES = ModuleNames()