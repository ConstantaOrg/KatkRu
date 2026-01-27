"""
Unit tests for IntegrationDocumenter class.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from core.docs_generator.integration_documenter import (
    IntegrationDocumenter,
    ExternalService,
    DatabaseTable,
    IntegrationDocumentation
)


class TestIntegrationDocumenter:
    """Test cases for IntegrationDocumenter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.documenter = IntegrationDocumenter()
    
    def test_init_with_default_project_root(self):
        """Test initialization with default project root."""
        documenter = IntegrationDocumenter()
        assert documenter.project_root == Path.cwd()
        assert len(documenter.config_files) == 5
        assert 'core/config.py' in documenter.config_files
    
    def test_init_with_custom_project_root(self):
        """Test initialization with custom project root."""
        custom_root = "/custom/path"
        documenter = IntegrationDocumenter(custom_root)
        assert documenter.project_root == Path(custom_root)
    
    def test_document_elasticsearch_integration(self):
        """Test Elasticsearch integration documentation."""
        service = self.documenter.document_elasticsearch_integration()
        
        assert isinstance(service, ExternalService)
        assert service.name == "Elasticsearch"
        assert service.type == "elasticsearch"
        assert "полнотекстового поиска" in service.description
        assert "search_index" in service.configuration["index_name"]
        assert "elastic_host" in service.connection_details["host"]
        assert len(service.usage_patterns) >= 3
        assert len(service.dependencies) >= 3
    
    def test_document_redis_integration(self):
        """Test Redis integration documentation."""
        service = self.documenter.document_redis_integration()
        
        assert isinstance(service, ExternalService)
        assert service.name == "Redis"
        assert service.type == "redis"
        assert "кэширования данных" in service.description
        assert "decode_responses" in service.configuration
        assert "redis_host" in service.connection_details["host"]
        assert len(service.usage_patterns) >= 3
        assert len(service.dependencies) >= 3
    
    def test_document_postgresql_integration(self):
        """Test PostgreSQL integration documentation."""
        service = self.documenter.document_postgresql_integration()
        
        assert isinstance(service, ExternalService)
        assert service.name == "PostgreSQL"
        assert service.type == "postgresql"
        assert "Основная база данных" in service.description
        assert "connection_pool" in service.configuration
        assert "pg_host" in service.connection_details["host"]
        assert len(service.usage_patterns) >= 4
        assert len(service.dependencies) >= 4
    
    def test_analyze_database_tables(self):
        """Test database tables analysis."""
        tables = self.documenter.analyze_database_tables()
        
        assert isinstance(tables, list)
        assert len(tables) > 0
        
        # Check that all expected tables are present
        table_names = [table.name for table in tables]
        expected_tables = ['specialties', 'groups', 'teachers', 'disciplines', 'timetable', 'users']
        for expected_table in expected_tables:
            assert expected_table in table_names
        
        # Check table structure
        specialties_table = next(table for table in tables if table.name == 'specialties')
        assert isinstance(specialties_table, DatabaseTable)
        assert "специальност" in specialties_table.description
        assert 'id' in specialties_table.columns
        assert 'spec_code' in specialties_table.columns
        assert len(specialties_table.relationships) > 0
        assert len(specialties_table.used_by_modules) > 0
    
    def test_document_database_schema(self):
        """Test database schema documentation."""
        schema = self.documenter.document_database_schema()
        
        assert isinstance(schema, dict)
        assert "overview" in schema
        assert "core_entities" in schema
        assert "timetable_system" in schema
        assert "relationships_map" in schema
        assert "indexes_and_constraints" in schema
        
        # Check core entities
        core_entities = schema["core_entities"]
        assert "specialties" in core_entities
        assert "groups" in core_entities
        assert "teachers" in core_entities
        assert "disciplines" in core_entities
        
        # Check timetable system
        timetable_system = schema["timetable_system"]
        assert "overview" in timetable_system
        assert "main_tables" in timetable_system
        assert "workflow" in timetable_system
        assert len(timetable_system["workflow"]) >= 4
        
        # Check relationships
        relationships = schema["relationships_map"]
        assert "one_to_many" in relationships
        assert "many_to_many" in relationships
        assert "many_to_one" in relationships
    
    def test_document_timetable_versioning_logic(self):
        """Test timetable versioning logic documentation."""
        versioning = self.documenter.document_timetable_versioning_logic()
        
        assert isinstance(versioning, dict)
        assert "overview" in versioning
        assert "version_statuses" in versioning
        assert "version_types" in versioning
        assert "workflow" in versioning
        assert "constraints" in versioning
        assert "tables_involved" in versioning
        
        # Check specific content
        assert "pending" in versioning["version_statuses"]
        assert "accepted" in versioning["version_statuses"]
        assert "standard" in versioning["version_types"]
        assert "daily" in versioning["version_types"]
        assert isinstance(versioning["tables_involved"], list)
        assert len(versioning["tables_involved"]) >= 3
    
    def test_extract_environment_variables(self):
        """Test environment variables extraction."""
        env_vars = self.documenter.extract_environment_variables()
        
        assert isinstance(env_vars, list)
        assert len(env_vars) > 10
        
        # Check for required variables
        env_var_text = " ".join(env_vars)
        assert "pg_user" in env_var_text
        assert "pg_password" in env_var_text
        assert "redis_host" in env_var_text
        assert "elastic_host" in env_var_text
        assert "APP_MODE" in env_var_text
        assert "search_index" in env_var_text
    
    def test_document_connection_setup(self):
        """Test connection setup documentation."""
        setup = self.documenter.document_connection_setup()
        
        assert isinstance(setup, dict)
        assert "postgresql_setup" in setup
        assert "redis_setup" in setup
        assert "elasticsearch_setup" in setup
        assert "environment_modes" in setup
        
        # Check setup instructions
        pg_setup = setup["postgresql_setup"]
        assert "переменные окружения" in pg_setup
        assert "asyncpg.create_pool" in pg_setup
        assert "dependency injection" in pg_setup
        
        redis_setup = setup["redis_setup"]
        assert "Redis клиент" in redis_setup
        assert "decode_responses=True" in redis_setup
        
        es_setup = setup["elasticsearch_setup"]
        assert "AsyncElasticsearch" in es_setup
        assert "индексы" in es_setup
        
        # Check environment modes
        env_modes = setup["environment_modes"]
        assert "local" in env_modes
        assert "docker" in env_modes
        assert "prod" in env_modes
    
    def test_generate_integration_documentation(self):
        """Test complete integration documentation generation."""
        doc = self.documenter.generate_integration_documentation()
        
        assert isinstance(doc, IntegrationDocumentation)
        assert len(doc.external_services) == 3
        assert len(doc.database_tables) > 5
        assert isinstance(doc.connection_setup, dict)
        assert isinstance(doc.environment_variables, list)
        
        # Check external services
        service_names = [service.name for service in doc.external_services]
        assert "PostgreSQL" in service_names
        assert "Redis" in service_names
        assert "Elasticsearch" in service_names
        
        # Check database tables
        table_names = [table.name for table in doc.database_tables]
        assert "specialties" in table_names
        assert "timetable" in table_names
        assert "users" in table_names
    
    def test_format_integration_markdown(self):
        """Test Markdown formatting of integration documentation."""
        doc = self.documenter.generate_integration_documentation()
        markdown = self.documenter.format_integration_markdown(doc)
        
        assert isinstance(markdown, str)
        assert len(markdown) > 1000  # Should be substantial content
        
        # Check for main sections
        assert "# Интеграции и База Данных" in markdown
        assert "## Внешние Сервисы" in markdown
        assert "## Структура Базы Данных" in markdown
        assert "## Настройка Подключений" in markdown
        assert "## Переменные Окружения" in markdown
        
        # Check for service documentation
        assert "### PostgreSQL" in markdown
        assert "### Redis" in markdown
        assert "### Elasticsearch" in markdown
        
        # Check for database documentation
        assert "### Обзор Схемы" in markdown
        assert "### Основные Сущности" in markdown
        assert "### Система Расписания" in markdown
        assert "### Связи Между Таблицами" in markdown
        
        # Check for specific content
        assert "asyncpg" in markdown
        assert "полнотекстового поиска" in markdown
        assert "версионирование" in markdown
    
    def test_database_table_relationships(self):
        """Test that database table relationships are properly documented."""
        tables = self.documenter.analyze_database_tables()
        
        # Find specific tables and check their relationships
        specialties_table = next(table for table in tables if table.name == 'specialties')
        groups_table = next(table for table in tables if table.name == 'groups')
        timetable_table = next(table for table in tables if table.name == 'timetable')
        
        # Check specialties relationships
        assert any("groups" in rel for rel in specialties_table.relationships)
        assert any("disciplines" in rel for rel in specialties_table.relationships)
        
        # Check groups relationships
        assert any("specialties" in rel for rel in groups_table.relationships)
        assert any("timetable" in rel for rel in groups_table.relationships)
        
        # Check timetable relationships
        assert any("groups" in rel for rel in timetable_table.relationships)
        assert any("teachers" in rel for rel in timetable_table.relationships)
        assert any("disciplines" in rel for rel in timetable_table.relationships)
    
    def test_module_usage_tracking(self):
        """Test that module usage is properly tracked for database tables."""
        tables = self.documenter.analyze_database_tables()
        
        # Check that tables are associated with correct modules
        specialties_table = next(table for table in tables if table.name == 'specialties')
        assert 'specialties' in specialties_table.used_by_modules
        assert 'elastic_search' in specialties_table.used_by_modules
        assert 'n8n_ui' in specialties_table.used_by_modules
        
        timetable_table = next(table for table in tables if table.name == 'timetable')
        assert 'timetable' in timetable_table.used_by_modules
        assert 'ttable_versions' in timetable_table.used_by_modules
        
        users_table = next(table for table in tables if table.name == 'users')
        assert 'users' in users_table.used_by_modules
        assert 'ttable_versions' in users_table.used_by_modules
    
    def test_service_configuration_completeness(self):
        """Test that service configurations include all necessary details."""
        # Test PostgreSQL configuration
        pg_service = self.documenter.document_postgresql_integration()
        assert "connection_pool" in pg_service.configuration
        assert "command_timeout" in pg_service.configuration
        assert "async_driver" in pg_service.configuration
        
        # Test Redis configuration
        redis_service = self.documenter.document_redis_integration()
        assert "decode_responses" in redis_service.configuration
        assert "connection_pool" in redis_service.configuration
        
        # Test Elasticsearch configuration
        es_service = self.documenter.document_elasticsearch_integration()
        assert "index_name" in es_service.configuration
        assert "mappings" in es_service.configuration
        assert "batch_size" in es_service.configuration
    
    def test_usage_patterns_coverage(self):
        """Test that usage patterns cover main functionality."""
        services = [
            self.documenter.document_postgresql_integration(),
            self.documenter.document_redis_integration(),
            self.documenter.document_elasticsearch_integration()
        ]
        
        for service in services:
            assert len(service.usage_patterns) >= 3
            
            # Each service should have specific usage patterns
            if service.name == "PostgreSQL":
                patterns_text = " ".join(service.usage_patterns)
                assert "CRUD" in patterns_text
                assert "Транзакц" in patterns_text
                assert "Версионирование" in patterns_text
            
            elif service.name == "Redis":
                patterns_text = " ".join(service.usage_patterns)
                assert "Кэш" in patterns_text
                assert "сессий" in patterns_text
            
            elif service.name == "Elasticsearch":
                patterns_text = " ".join(service.usage_patterns)
                assert "поиск" in patterns_text
                assert "индекс" in patterns_text
                assert "Автодополнение" in patterns_text


class TestDatabaseTableModel:
    """Test DatabaseTable data model."""
    
    def test_database_table_creation(self):
        """Test DatabaseTable creation."""
        table = DatabaseTable(
            name="test_table",
            description="Test table description",
            columns=["id", "name", "created_at"],
            relationships=["other_table (one-to-many)"],
            used_by_modules=["test_module"]
        )
        
        assert table.name == "test_table"
        assert table.description == "Test table description"
        assert len(table.columns) == 3
        assert len(table.relationships) == 1
        assert len(table.used_by_modules) == 1


class TestExternalServiceModel:
    """Test ExternalService data model."""
    
    def test_external_service_creation(self):
        """Test ExternalService creation."""
        service = ExternalService(
            name="TestService",
            type="database",
            description="Test service description",
            configuration={"key": "value"},
            connection_details={"host": "localhost"},
            usage_patterns=["pattern1", "pattern2"],
            dependencies=["dep1", "dep2"]
        )
        
        assert service.name == "TestService"
        assert service.type == "database"
        assert service.description == "Test service description"
        assert service.configuration["key"] == "value"
        assert service.connection_details["host"] == "localhost"
        assert len(service.usage_patterns) == 2
        assert len(service.dependencies) == 2


class TestIntegrationDocumentationModel:
    """Test IntegrationDocumentation data model."""
    
    def test_integration_documentation_creation(self):
        """Test IntegrationDocumentation creation."""
        service = ExternalService(
            name="TestService",
            type="database",
            description="Test",
            configuration={},
            connection_details={},
            usage_patterns=[],
            dependencies=[]
        )
        
        table = DatabaseTable(
            name="test_table",
            description="Test",
            columns=[],
            relationships=[],
            used_by_modules=[]
        )
        
        doc = IntegrationDocumentation(
            external_services=[service],
            database_tables=[table],
            connection_setup={"setup": "instructions"},
            environment_variables=["VAR1", "VAR2"]
        )
        
        assert len(doc.external_services) == 1
        assert len(doc.database_tables) == 1
        assert doc.connection_setup["setup"] == "instructions"
        assert len(doc.environment_variables) == 2