"""
Module documenter for creating documentation for different API modules.
"""

from typing import List, Dict, Set
from .models import ModuleDocumentation, EndpointInfo


class ModuleDocumenter:
    """Creates documentation for different API modules."""
    
    def __init__(self):
        self.module_descriptions = {
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
        
        # Define module relationships
        self.module_relationships = {
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
    
    def group_endpoints_by_modules(self, endpoints: List[EndpointInfo]) -> Dict[str, List[EndpointInfo]]:
        """Group endpoints by their modules."""
        grouped = {}
        
        for endpoint in endpoints:
            # Skip one_time_scripts as per requirements
            if 'one_time_scripts' in endpoint.function_name or 'one_time_scripts' in endpoint.module:
                continue
                
            module = self.categorize_endpoint(endpoint)
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(endpoint)
        
        return grouped
    
    def categorize_endpoint(self, endpoint: EndpointInfo) -> str:
        """Categorize an endpoint into appropriate module."""
        # First check the path for module indicators
        path_lower = endpoint.path.lower()
        
        if '/specialties' in path_lower:
            return 'specialties'
        elif '/groups' in path_lower:
            return 'groups'
        elif '/teachers' in path_lower:
            return 'teachers'
        elif '/disciplines' in path_lower:
            return 'disciplines'
        elif '/timetable' in path_lower:
            return 'timetable'
        elif '/users' in path_lower:
            return 'users'
        elif '/n8n' in path_lower:
            return 'n8n_ui'
        elif '/search' in path_lower or '/elastic' in path_lower:
            return 'elastic_search'
        elif '/ttable_versions' in path_lower:
            return 'ttable_versions'
        
        # Check module field if available
        if endpoint.module and endpoint.module != 'miscellaneous':
            return endpoint.module
        
        # Fallback to analyzing function name or dependencies
        func_name_lower = endpoint.function_name.lower()
        
        if any(keyword in func_name_lower for keyword in ['specialty', 'specialties']):
            return 'specialties'
        elif any(keyword in func_name_lower for keyword in ['group', 'groups']):
            return 'groups'
        elif any(keyword in func_name_lower for keyword in ['teacher', 'teachers']):
            return 'teachers'
        elif any(keyword in func_name_lower for keyword in ['discipline', 'disciplines']):
            return 'disciplines'
        elif any(keyword in func_name_lower for keyword in ['timetable', 'ttable']):
            return 'timetable'
        elif any(keyword in func_name_lower for keyword in ['user', 'users']):
            return 'users'
        elif any(keyword in func_name_lower for keyword in ['n8n']):
            return 'n8n_ui'
        elif any(keyword in func_name_lower for keyword in ['search', 'elastic']):
            return 'elastic_search'
        elif any(keyword in func_name_lower for keyword in ['version']):
            return 'ttable_versions'
        
        return 'miscellaneous'
    
    def analyze_module_relationships(self, module: str, all_endpoints: List[EndpointInfo]) -> List[str]:
        """Analyze relationships between modules based on dependencies."""
        related_modules = set()
        
        # Get predefined relationships
        if module in self.module_relationships:
            related_modules.update(self.module_relationships[module])
        
        # Analyze actual dependencies from endpoints
        module_endpoints = [ep for ep in all_endpoints if self.categorize_endpoint(ep) == module]
        
        for endpoint in module_endpoints:
            for dependency in endpoint.dependencies:
                # Check if dependency belongs to another module
                dep_module = self._determine_dependency_module(dependency.module)
                if dep_module and dep_module != module and dep_module != 'miscellaneous':
                    related_modules.add(dep_module)
        
        return list(related_modules)
    
    def _determine_dependency_module(self, dependency_module_path: str) -> str:
        """Determine which module a dependency belongs to based on its module path."""
        if not dependency_module_path:
            return 'miscellaneous'
        
        path_lower = dependency_module_path.lower()
        
        if 'specialties' in path_lower:
            return 'specialties'
        elif 'groups' in path_lower:
            return 'groups'
        elif 'teachers' in path_lower:
            return 'teachers'
        elif 'disciplines' in path_lower:
            return 'disciplines'
        elif 'timetable' in path_lower:
            return 'timetable'
        elif 'users' in path_lower:
            return 'users'
        elif 'n8n' in path_lower:
            return 'n8n_ui'
        elif 'elastic' in path_lower or 'search' in path_lower:
            return 'elastic_search'
        elif 'ttable_versions' in path_lower:
            return 'ttable_versions'
        elif 'middleware' in path_lower:
            return 'middleware'
        
        return 'miscellaneous'
    
    def get_module_description(self, module_name: str) -> str:
        """Get description for a module."""
        return self.module_descriptions.get(module_name, 'Модуль системы')
    
    def create_module_documentation(self, module_name: str, endpoints: List[EndpointInfo], 
                                  all_endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Create documentation for a specific module."""
        # Filter endpoints for this module
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == module_name]
        
        # Extract unique schemas from endpoints
        schemas = set()
        for endpoint in module_endpoints:
            if endpoint.request_body:
                schemas.add(endpoint.request_body)
            if endpoint.response_model:
                schemas.add(endpoint.response_model)
        
        # Extract database tables from dependencies
        database_tables = set()
        for endpoint in module_endpoints:
            for dependency in endpoint.dependencies:
                if 'sql' in dependency.name.lower() or 'query' in dependency.name.lower():
                    # Extract table names from SQL-related dependencies
                    if 'groups' in dependency.name.lower():
                        database_tables.add('groups')
                    elif 'specialties' in dependency.name.lower():
                        database_tables.add('specialties')
                    elif 'teachers' in dependency.name.lower():
                        database_tables.add('teachers')
                    elif 'disciplines' in dependency.name.lower():
                        database_tables.add('disciplines')
                    elif 'timetable' in dependency.name.lower() or 'ttable' in dependency.name.lower():
                        database_tables.add('timetable')
                    elif 'users' in dependency.name.lower():
                        database_tables.add('users')
        
        # Analyze module relationships
        related_modules = self.analyze_module_relationships(module_name, all_endpoints)
        
        return ModuleDocumentation(
            name=module_name,
            description=self.get_module_description(module_name),
            endpoints=module_endpoints,
            schemas=list(schemas),
            database_tables=list(database_tables),
            examples=[]  # Examples will be populated by ExampleGenerator
        )
    
    def document_specialties_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the specialties module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'specialties']
        
        # Create base documentation
        doc = self.create_module_documentation('specialties', endpoints, endpoints)
        
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
    
    def document_groups_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the groups module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'groups']
        
        # Create base documentation
        doc = self.create_module_documentation('groups', endpoints, endpoints)
        
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
    
    def document_teachers_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the teachers module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'teachers']
        
        # Create base documentation
        doc = self.create_module_documentation('teachers', endpoints, endpoints)
        
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
    
    def document_disciplines_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the disciplines module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'disciplines']
        
        # Create base documentation
        doc = self.create_module_documentation('disciplines', endpoints, endpoints)
        
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
    
    def document_timetable_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the timetable module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'timetable']
        
        # Create base documentation
        doc = self.create_module_documentation('timetable', endpoints, endpoints)
        
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
    
    def document_users_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the users module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'users']
        
        # Create base documentation
        doc = self.create_module_documentation('users', endpoints, endpoints)
        
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
    
    def document_n8n_ui_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the N8N UI module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'n8n_ui']
        
        # Create base documentation
        doc = self.create_module_documentation('n8n_ui', endpoints, endpoints)
        
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
    
    def document_search_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the search module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'elastic_search']
        
        # Create base documentation
        doc = self.create_module_documentation('elastic_search', endpoints, endpoints)
        
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
    
    def document_ttable_versions_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the timetable versions module."""
        module_endpoints = [ep for ep in endpoints if self.categorize_endpoint(ep) == 'ttable_versions']
        
        # Create base documentation
        doc = self.create_module_documentation('ttable_versions', endpoints, endpoints)
        
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