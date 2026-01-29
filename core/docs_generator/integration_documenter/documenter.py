"""
Main integration documenter class.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path

from .models import DatabaseTable, ExternalService, IntegrationDocumentation
from .handlers import (
    document_elasticsearch_integration, document_redis_integration,
    document_postgresql_integration, analyze_database_tables,
    document_database_schema, document_timetable_versioning_logic,
    extract_environment_variables, document_connection_setup,
    generate_integration_documentation, format_integration_markdown
)
from .constants import CONFIG_FILES


class IntegrationDocumenter:
    """Documents external service integrations and database structure."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_files = CONFIG_FILES.FILES.copy()
    
    def document_elasticsearch_integration(self) -> ExternalService:
        """Document Elasticsearch integration."""
        return document_elasticsearch_integration()
    
    def document_redis_integration(self) -> ExternalService:
        """Document Redis integration."""
        return document_redis_integration()
    
    def document_postgresql_integration(self) -> ExternalService:
        """Document PostgreSQL integration."""
        return document_postgresql_integration()
    
    def analyze_database_tables(self) -> List[DatabaseTable]:
        """Analyze and document database tables."""
        return analyze_database_tables()
    
    def document_database_schema(self) -> Dict[str, Any]:
        """Document complete database schema with relationships."""
        return document_database_schema()
    
    def document_timetable_versioning_logic(self) -> Dict[str, str]:
        """Document the timetable versioning system logic."""
        return document_timetable_versioning_logic()
    
    def extract_environment_variables(self) -> List[str]:
        """Extract required environment variables from configuration files."""
        return extract_environment_variables()
    
    def document_connection_setup(self) -> Dict[str, str]:
        """Document connection setup procedures."""
        return document_connection_setup()
    
    def generate_integration_documentation(self) -> IntegrationDocumentation:
        """Generate complete integration documentation."""
        return generate_integration_documentation(self.project_root)
    
    def format_integration_markdown(self, integration_doc: IntegrationDocumentation) -> str:
        """Format integration documentation as Markdown."""
        return format_integration_markdown(integration_doc)