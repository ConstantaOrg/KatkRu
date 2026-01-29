"""
Main module documenter class.
"""

from typing import List, Dict
from ..models import ModuleDocumentation, EndpointInfo
from .handlers import (
    group_endpoints_by_modules, categorize_endpoint, analyze_module_relationships,
    get_module_description, create_base_module_documentation,
    create_specialties_documentation, create_groups_documentation,
    create_teachers_documentation, create_disciplines_documentation,
    create_timetable_documentation, create_users_documentation,
    create_n8n_ui_documentation, create_search_documentation,
    create_ttable_versions_documentation
)
from .constants import MODULE_NAMES


class ModuleDocumenter:
    """Creates documentation for different API modules."""
    
    def __init__(self):
        pass
    
    def group_endpoints_by_modules(self, endpoints: List[EndpointInfo]) -> Dict[str, List[EndpointInfo]]:
        """Group endpoints by their modules."""
        return group_endpoints_by_modules(endpoints)
    
    def categorize_endpoint(self, endpoint: EndpointInfo) -> str:
        """Categorize an endpoint into appropriate module."""
        return categorize_endpoint(endpoint)
    
    def analyze_module_relationships(self, module: str, all_endpoints: List[EndpointInfo]) -> List[str]:
        """Analyze relationships between modules based on dependencies."""
        return analyze_module_relationships(module, all_endpoints)
    
    def get_module_description(self, module_name: str) -> str:
        """Get description for a module."""
        return get_module_description(module_name)
    
    def create_module_documentation(self, module_name: str, endpoints: List[EndpointInfo], 
                                  all_endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Create documentation for a specific module."""
        return create_base_module_documentation(module_name, endpoints, all_endpoints)
    
    def document_specialties_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the specialties module."""
        return create_specialties_documentation(endpoints)
    
    def document_groups_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the groups module."""
        return create_groups_documentation(endpoints)
    
    def document_teachers_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the teachers module."""
        return create_teachers_documentation(endpoints)
    
    def document_disciplines_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the disciplines module."""
        return create_disciplines_documentation(endpoints)
    
    def document_timetable_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the timetable module."""
        return create_timetable_documentation(endpoints)
    
    def document_users_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the users module."""
        return create_users_documentation(endpoints)
    
    def document_n8n_ui_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the N8N UI module."""
        return create_n8n_ui_documentation(endpoints)
    
    def document_search_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the search module."""
        return create_search_documentation(endpoints)
    
    def document_ttable_versions_module(self, endpoints: List[EndpointInfo]) -> ModuleDocumentation:
        """Document the timetable versions module."""
        return create_ttable_versions_documentation(endpoints)