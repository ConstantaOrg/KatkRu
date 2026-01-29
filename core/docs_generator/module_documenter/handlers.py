"""
Handler functions for module documentation operations.
"""

from typing import List, Dict, Set
from ..models import ModuleDocumentation, EndpointInfo
from .constants import (
    MODULE_DESCRIPTIONS, MODULE_RELATIONSHIPS, PATH_KEYWORDS, 
    FUNCTION_KEYWORDS, DEPENDENCY_KEYWORDS, MODULE_NAMES
)


def group_endpoints_by_modules(endpoints: List[EndpointInfo]) -> Dict[str, List[EndpointInfo]]:
    """Group endpoints by their modules."""
    grouped = {}
    
    for endpoint in endpoints:
        # Skip one_time_scripts as per requirements
        if 'one_time_scripts' in endpoint.function_name or 'one_time_scripts' in endpoint.module:
            continue
            
        module = categorize_endpoint(endpoint)
        if module not in grouped:
            grouped[module] = []
        grouped[module].append(endpoint)
    
    return grouped


def categorize_endpoint(endpoint: EndpointInfo) -> str:
    """Categorize an endpoint into appropriate module."""
    # First check the path for module indicators
    path_lower = endpoint.path.lower()
    
    # Check path keywords
    if any(keyword in path_lower for keyword in PATH_KEYWORDS.SPECIALTIES):
        return MODULE_NAMES.SPECIALTIES
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.GROUPS):
        return MODULE_NAMES.GROUPS
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.TEACHERS):
        return MODULE_NAMES.TEACHERS
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.DISCIPLINES):
        return MODULE_NAMES.DISCIPLINES
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.TIMETABLE):
        return MODULE_NAMES.TIMETABLE
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.USERS):
        return MODULE_NAMES.USERS
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.N8N_UI):
        return MODULE_NAMES.N8N_UI
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.ELASTIC_SEARCH):
        return MODULE_NAMES.ELASTIC_SEARCH
    elif any(keyword in path_lower for keyword in PATH_KEYWORDS.TTABLE_VERSIONS):
        return MODULE_NAMES.TTABLE_VERSIONS
    
    # Check module field if available
    if endpoint.module and endpoint.module != MODULE_NAMES.MISCELLANEOUS:
        return endpoint.module
    
    # Fallback to analyzing function name
    func_name_lower = endpoint.function_name.lower()
    
    if any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.SPECIALTIES):
        return MODULE_NAMES.SPECIALTIES
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.GROUPS):
        return MODULE_NAMES.GROUPS
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.TEACHERS):
        return MODULE_NAMES.TEACHERS
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.DISCIPLINES):
        return MODULE_NAMES.DISCIPLINES
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.TIMETABLE):
        return MODULE_NAMES.TIMETABLE
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.USERS):
        return MODULE_NAMES.USERS
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.N8N_UI):
        return MODULE_NAMES.N8N_UI
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.ELASTIC_SEARCH):
        return MODULE_NAMES.ELASTIC_SEARCH
    elif any(keyword in func_name_lower for keyword in FUNCTION_KEYWORDS.TTABLE_VERSIONS):
        return MODULE_NAMES.TTABLE_VERSIONS
    
    return MODULE_NAMES.MISCELLANEOUS


def analyze_module_relationships(module: str, all_endpoints: List[EndpointInfo]) -> List[str]:
    """Analyze relationships between modules based on dependencies."""
    related_modules = set()
    
    # Get predefined relationships
    if module in MODULE_RELATIONSHIPS.RELATIONSHIPS:
        related_modules.update(MODULE_RELATIONSHIPS.RELATIONSHIPS[module])
    
    # Analyze actual dependencies from endpoints
    module_endpoints = [ep for ep in all_endpoints if categorize_endpoint(ep) == module]
    
    for endpoint in module_endpoints:
        for dependency in endpoint.dependencies:
            # Check if dependency belongs to another module
            dep_module = determine_dependency_module(dependency.module)
            if dep_module and dep_module != module and dep_module != MODULE_NAMES.MISCELLANEOUS:
                related_modules.add(dep_module)
    
    return list(related_modules)


def determine_dependency_module(dependency_module_path: str) -> str:
    """Determine which module a dependency belongs to based on its module path."""
    if not dependency_module_path:
        return MODULE_NAMES.MISCELLANEOUS
    
    path_lower = dependency_module_path.lower()
    
    if 'specialties' in path_lower:
        return MODULE_NAMES.SPECIALTIES
    elif 'groups' in path_lower:
        return MODULE_NAMES.GROUPS
    elif 'teachers' in path_lower:
        return MODULE_NAMES.TEACHERS
    elif 'disciplines' in path_lower:
        return MODULE_NAMES.DISCIPLINES
    elif 'timetable' in path_lower:
        return MODULE_NAMES.TIMETABLE
    elif 'users' in path_lower:
        return MODULE_NAMES.USERS
    elif 'n8n' in path_lower:
        return MODULE_NAMES.N8N_UI
    elif 'elastic' in path_lower or 'search' in path_lower:
        return MODULE_NAMES.ELASTIC_SEARCH
    elif 'ttable_versions' in path_lower:
        return MODULE_NAMES.TTABLE_VERSIONS
    elif 'middleware' in path_lower:
        return MODULE_NAMES.MIDDLEWARE
    
    return MODULE_NAMES.MISCELLANEOUS


def get_module_description(module_name: str) -> str:
    """Get description for a module."""
    return MODULE_DESCRIPTIONS.DESCRIPTIONS.get(module_name, 'Модуль системы')


def extract_schemas_from_endpoints(endpoints: List[EndpointInfo]) -> List:
    """Extract unique schemas from endpoints."""
    schemas = set()
    for endpoint in endpoints:
        if endpoint.request_body:
            schemas.add(endpoint.request_body)
        if endpoint.response_model:
            schemas.add(endpoint.response_model)
    return list(schemas)


def extract_database_tables_from_endpoints(endpoints: List[EndpointInfo]) -> List[str]:
    """Extract database tables from endpoint dependencies."""
    database_tables = set()
    
    for endpoint in endpoints:
        for dependency in endpoint.dependencies:
            if 'sql' in dependency.name.lower() or 'query' in dependency.name.lower():
                # Extract table names from SQL-related dependencies
                dep_name_lower = dependency.name.lower()
                
                if any(keyword in dep_name_lower for keyword in DEPENDENCY_KEYWORDS.GROUPS):
                    database_tables.add('groups')
                elif any(keyword in dep_name_lower for keyword in DEPENDENCY_KEYWORDS.SPECIALTIES):
                    database_tables.add('specialties')
                elif any(keyword in dep_name_lower for keyword in DEPENDENCY_KEYWORDS.TEACHERS):
                    database_tables.add('teachers')
                elif any(keyword in dep_name_lower for keyword in DEPENDENCY_KEYWORDS.DISCIPLINES):
                    database_tables.add('disciplines')
                elif any(keyword in dep_name_lower for keyword in DEPENDENCY_KEYWORDS.TIMETABLE):
                    database_tables.add('timetable')
                elif any(keyword in dep_name_lower for keyword in DEPENDENCY_KEYWORDS.USERS):
                    database_tables.add('users')
    
    return list(database_tables)


def create_base_module_documentation(module_name: str, endpoints: List[EndpointInfo], 
                                   all_endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create base documentation for a specific module."""
    # Filter endpoints for this module
    module_endpoints = [ep for ep in endpoints if categorize_endpoint(ep) == module_name]
    
    # Extract unique schemas from endpoints
    schemas = extract_schemas_from_endpoints(module_endpoints)
    
    # Extract database tables from dependencies
    database_tables = extract_database_tables_from_endpoints(module_endpoints)
    
    # Analyze module relationships
    related_modules = analyze_module_relationships(module_name, all_endpoints)
    
    return ModuleDocumentation(
        name=module_name,
        description=get_module_description(module_name),
        endpoints=module_endpoints,
        schemas=schemas,
        database_tables=database_tables,
        examples=[]  # Examples will be populated by ExampleGenerator
    )


def create_specialties_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the specialties module."""
    doc = create_base_module_documentation(MODULE_NAMES.SPECIALTIES, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления специальностями учебного заведения. "
        "Предоставляет функциональность для просмотра списка специальностей "
        "и получения детальной информации о конкретной специальности. "
        "Используется для организации учебного процесса и группировки студентов по направлениям обучения."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['specialties', 'groups'])
    doc.database_tables = list(set(doc.database_tables))  # Remove duplicates
    
    return doc


def create_groups_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the groups module."""
    doc = create_base_module_documentation(MODULE_NAMES.GROUPS, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления учебными группами. "
        "Предоставляет функциональность для создания, обновления и просмотра учебных групп. "
        "Включает управление статусами групп (активные/устаревшие) и привязку к зданиям. "
        "Требует аутентификации и роли методиста для модификации данных."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['groups', 'buildings', 'specialties'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_teachers_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the teachers module."""
    doc = create_base_module_documentation(MODULE_NAMES.TEACHERS, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления преподавателями. "
        "Предоставляет функциональность для добавления, обновления и просмотра информации о преподавателях. "
        "Включает управление статусами преподавателей и предотвращение дублирования записей. "
        "Требует аутентификации и роли методиста для модификации данных."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['teachers', 'disciplines'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_disciplines_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the disciplines module."""
    doc = create_base_module_documentation(MODULE_NAMES.DISCIPLINES, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления дисциплинами (предметами). "
        "Предоставляет функциональность для создания, обновления и просмотра учебных дисциплин. "
        "Связывает дисциплины с преподавателями и специальностями. "
        "Используется для формирования учебных планов и расписания занятий."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['disciplines', 'teachers', 'specialties', 'timetable'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_timetable_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the timetable module."""
    doc = create_base_module_documentation(MODULE_NAMES.TIMETABLE, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления расписанием занятий. "
        "Центральный модуль системы, объединяющий группы, преподавателей и дисциплины в единое расписание. "
        "Предоставляет функциональность для создания, обновления и просмотра расписания. "
        "Поддерживает версионирование расписания и различные форматы вывода."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['timetable', 'groups', 'teachers', 'disciplines', 'ttable_versions'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_users_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the users module."""
    doc = create_base_module_documentation(MODULE_NAMES.USERS, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления пользователями системы. "
        "Предоставляет функциональность для аутентификации, авторизации и управления пользователями. "
        "Включает систему ролей (методист, администратор, только чтение) и JWT токены. "
        "Обеспечивает безопасность доступа к функциям системы."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['users', 'roles', 'user_sessions'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_n8n_ui_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the N8N UI module."""
    doc = create_base_module_documentation(MODULE_NAMES.N8N_UI, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль интеграции с N8N для автоматизации рабочих процессов. "
        "Предоставляет специализированные API endpoints для интеграции с внешними системами автоматизации. "
        "Включает адаптированные схемы данных и форматы ответов для совместимости с N8N workflows. "
        "Обеспечивает мост между системой управления расписанием и внешними инструментами автоматизации."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['specialties', 'groups', 'teachers', 'disciplines'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_search_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the search module."""
    doc = create_base_module_documentation(MODULE_NAMES.ELASTIC_SEARCH, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль поиска на базе Elasticsearch. "
        "Предоставляет мощные возможности полнотекстового поиска по всем данным системы. "
        "Включает поиск по специальностям, группам, преподавателям и дисциплинам. "
        "Поддерживает сложные запросы, фильтрацию и ранжирование результатов. "
        "Обеспечивает быстрый доступ к информации для пользователей системы."
    )
    
    # Add specific database tables (search indexes)
    doc.database_tables.extend(['elasticsearch_indexes', 'search_cache'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc


def create_ttable_versions_documentation(endpoints: List[EndpointInfo]) -> ModuleDocumentation:
    """Create documentation for the timetable versions module."""
    doc = create_base_module_documentation(MODULE_NAMES.TTABLE_VERSIONS, endpoints, endpoints)
    
    # Add specific module details
    doc.description = (
        "Модуль управления версиями расписания. "
        "Предоставляет функциональность для создания, хранения и управления различными версиями расписания. "
        "Позволяет отслеживать изменения в расписании, создавать резервные копии и откатываться к предыдущим версиям. "
        "Обеспечивает историю изменений и возможность сравнения различных версий расписания."
    )
    
    # Add specific database tables
    doc.database_tables.extend(['ttable_versions', 'timetable', 'version_history'])
    doc.database_tables = list(set(doc.database_tables))
    
    return doc