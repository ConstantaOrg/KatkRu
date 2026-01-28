"""
Integration documenter for external services and database documentation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import inspect
import ast
import os
from pathlib import Path


@dataclass
class DatabaseTable:
    """Information about a database table."""
    name: str
    description: str
    columns: List[str]
    relationships: List[str]
    used_by_modules: List[str]


@dataclass
class ExternalService:
    """Information about an external service integration."""
    name: str
    type: str  # elasticsearch, redis, postgresql
    description: str
    configuration: Dict[str, Any]
    connection_details: Dict[str, str]
    usage_patterns: List[str]
    dependencies: List[str]


@dataclass
class IntegrationDocumentation:
    """Complete integration documentation."""
    external_services: List[ExternalService]
    database_tables: List[DatabaseTable]
    connection_setup: Dict[str, str]
    environment_variables: List[str]


class IntegrationDocumenter:
    """Documents external service integrations and database structure."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_files = [
            'core/config_dir/config.py',
            'core/data/postgre.py',
            'core/data/redis_storage.py',
            'core/api/elastic_search.py'
        ]
        
        # Database table information extracted from SQL queries
        self.database_tables_info = {
            'specialties': {
                'description': 'Хранит информацию о специальностях учебного заведения',
                'columns': ['id', 'spec_code', 'title', 'description', 'learn_years', 'full_time', 'free_form', 'evening_form', 'cost_per_year'],
                'relationships': ['groups (one-to-many)', 'disciplines (many-to-many)'],
                'used_by_modules': ['specialties', 'groups', 'n8n_ui', 'elastic_search']
            },
            'groups': {
                'description': 'Содержит информацию об учебных группах',
                'columns': ['id', 'name', 'building_id', 'is_active'],
                'relationships': ['specialties (many-to-one)', 'timetable (one-to-many)', 'users (many-to-many)'],
                'used_by_modules': ['groups', 'timetable', 'users', 'n8n_ui']
            },
            'teachers': {
                'description': 'Информация о преподавателях',
                'columns': ['id', 'fio', 'is_active'],
                'relationships': ['disciplines (many-to-many)', 'timetable (one-to-many)'],
                'used_by_modules': ['teachers', 'timetable', 'disciplines']
            },
            'disciplines': {
                'description': 'Учебные дисциплины (предметы)',
                'columns': ['id', 'title', 'description'],
                'relationships': ['teachers (many-to-many)', 'specialties (many-to-many)', 'timetable (one-to-many)'],
                'used_by_modules': ['disciplines', 'teachers', 'timetable', 'specialties']
            },
            'timetable': {
                'description': 'Основная таблица расписания занятий',
                'columns': ['id', 'group_id', 'teacher_id', 'discipline_id', 'position', 'aud', 'week_day'],
                'relationships': ['groups (many-to-one)', 'teachers (many-to-one)', 'disciplines (many-to-one)', 'ttable_versions (many-to-one)'],
                'used_by_modules': ['timetable', 'ttable_versions']
            },
            'ttable_versions': {
                'description': 'Версии расписания для отслеживания изменений',
                'columns': ['id', 'building_id', 'schedule_date', 'type', 'status_id', 'user_id', 'is_commited', 'last_modified_at'],
                'relationships': ['timetable (one-to-many)', 'users (many-to-one)', 'cards_states_history (one-to-many)'],
                'used_by_modules': ['ttable_versions', 'timetable']
            },
            'users': {
                'description': 'Пользователи системы с ролями и правами доступа',
                'columns': ['id', 'username', 'email', 'password_hash', 'role_id', 'is_active'],
                'relationships': ['roles (many-to-one)', 'ttable_versions (one-to-many)', 'user_sessions (one-to-many)'],
                'used_by_modules': ['users', 'ttable_versions']
            },
            'roles': {
                'description': 'Роли пользователей (методист, администратор, только чтение)',
                'columns': ['id', 'name', 'permissions'],
                'relationships': ['users (one-to-many)'],
                'used_by_modules': ['users']
            },
            'buildings': {
                'description': 'Здания учебного заведения',
                'columns': ['id', 'name', 'address'],
                'relationships': ['groups (one-to-many)'],
                'used_by_modules': ['groups', 'timetable']
            },
            'cards_states_history': {
                'description': 'История состояний карточек расписания',
                'columns': ['id', 'sched_ver_id', 'group_id', 'is_current', 'status_id'],
                'relationships': ['ttable_versions (many-to-one)', 'groups (many-to-one)', 'cards_states_details (one-to-many)'],
                'used_by_modules': ['timetable', 'ttable_versions']
            },
            'cards_states_details': {
                'description': 'Детали карточек расписания',
                'columns': ['id', 'card_hist_id', 'discipline_id', 'teacher_id', 'position', 'aud'],
                'relationships': ['cards_states_history (many-to-one)', 'disciplines (many-to-one)', 'teachers (many-to-one)'],
                'used_by_modules': ['timetable']
            },
            'std_ttable': {
                'description': 'Стандартное расписание (шаблон)',
                'columns': ['id', 'sched_ver_id', 'group_id', 'discipline_id', 'position', 'aud', 'teacher_id', 'week_day'],
                'relationships': ['ttable_versions (many-to-one)', 'groups (many-to-one)', 'disciplines (many-to-one)', 'teachers (many-to-one)'],
                'used_by_modules': ['timetable']
            }
        }
    
    def document_elasticsearch_integration(self) -> ExternalService:
        """Document Elasticsearch integration."""
        return ExternalService(
            name="Elasticsearch",
            type="elasticsearch",
            description=(
                "Используется для полнотекстового поиска по специальностям. "
                "Обеспечивает быстрый поиск по коду и названию специальностей с поддержкой автодополнения. "
                "Индексирует данные из таблицы specialties для оптимизации поисковых запросов."
            ),
            configuration={
                "index_name": "search_index (из переменной окружения)",
                "mappings": "Настроены для поиска по полям code_prefix, spec_title_prefix, spec_title_search",
                "aliases": "Используются алиасы для гибкого управления индексами",
                "batch_size": "2000 документов за раз при индексации"
            },
            connection_details={
                "host": "elastic_host / elastic_host_docker",
                "port": "elastic_port",
                "authentication": "elastic_user / elastic_password (закомментировано)",
                "ssl": "ca_certs / verify_certs (закомментировано)",
                "scheme": "http/https в зависимости от режима приложения"
            },
            usage_patterns=[
                "Автодополнение поиска специальностей (/public/elastic/autocomplete_spec)",
                "Расширенный поиск специальностей (/public/elastic/ext_spec)",
                "Инициализация индекса при запуске приложения",
                "Батчевая индексация данных из PostgreSQL"
            ],
            dependencies=[
                "AsyncElasticsearch клиент",
                "Конфигурация из core.config_dir.config",
                "Настройки индекса из core.config_dir.index_settings",
                "Данные из PostgreSQL (таблица specialties)"
            ]
        )
    
    def document_redis_integration(self) -> ExternalService:
        """Document Redis integration."""
        return ExternalService(
            name="Redis",
            type="redis",
            description=(
                "Используется для кэширования данных и хранения сессий пользователей. "
                "Обеспечивает быстрый доступ к часто запрашиваемым данным и управление состоянием сессий. "
                "Поддерживает различные конфигурации для локальной разработки и продакшена."
            ),
            configuration={
                "decode_responses": "True - автоматическое декодирование ответов в строки",
                "connection_pool": "Используется пул соединений для оптимизации производительности",
                "password": "Требуется пароль для продакшен окружения",
                "timeout": "Настраивается таймаут соединения"
            },
            connection_details={
                "host": "redis_host / redis_host_docker",
                "port": "redis_port / redis_port_docker",
                "password": "redis_password (только для продакшена)",
                "database": "По умолчанию используется база данных 0"
            },
            usage_patterns=[
                "Кэширование результатов поисковых запросов",
                "Хранение JWT токенов и сессий пользователей",
                "Кэширование данных расписания для быстрого доступа",
                "Временное хранение состояния импорта данных"
            ],
            dependencies=[
                "Redis.asyncio клиент",
                "Конфигурация из core.config_dir.config",
                "Контекстный менеджер для управления соединениями",
                "FastAPI dependency injection система"
            ]
        )
    
    def document_postgresql_integration(self) -> ExternalService:
        """Document PostgreSQL integration."""
        return ExternalService(
            name="PostgreSQL",
            type="postgresql",
            description=(
                "Основная база данных системы, хранящая все данные о специальностях, группах, "
                "преподавателях, дисциплинах и расписании. Использует asyncpg для асинхронного "
                "взаимодействия с базой данных и поддерживает транзакции для обеспечения целостности данных."
            ),
            configuration={
                "connection_pool": "Используется пул соединений для оптимизации производительности",
                "command_timeout": "60 секунд для выполнения команд",
                "isolation_level": "READ COMMITTED / REPEATABLE READ для транзакций",
                "async_driver": "asyncpg для асинхронных операций"
            },
            connection_details={
                "host": "pg_host / pg_host_docker",
                "port": "pg_port / pg_port_docker",
                "database": "pg_db",
                "user": "pg_user",
                "password": "pg_password"
            },
            usage_patterns=[
                "CRUD операции для всех основных сущностей",
                "Сложные запросы с JOIN для получения связанных данных",
                "Транзакционные операции для импорта расписания",
                "Batch операции для массовой вставки данных",
                "Версионирование расписания с поддержкой отката"
            ],
            dependencies=[
                "asyncpg драйвер",
                "Пул соединений AsyncPG",
                "SQL запросы в модулях *_sql.py",
                "Конфигурация из core.config_dir.config",
                "FastAPI dependency injection система"
            ]
        )
    
    def analyze_database_tables(self) -> List[DatabaseTable]:
        """Analyze and document database tables."""
        tables = []
        
        for table_name, info in self.database_tables_info.items():
            table = DatabaseTable(
                name=table_name,
                description=info['description'],
                columns=info['columns'],
                relationships=info['relationships'],
                used_by_modules=info['used_by_modules']
            )
            tables.append(table)
        
        return tables
    
    def document_database_schema(self) -> Dict[str, Any]:
        """Document complete database schema with relationships."""
        return {
            "overview": (
                "База данных системы управления расписанием построена на PostgreSQL и включает "
                "основные сущности для управления учебным процессом: специальности, группы, "
                "преподаватели, дисциплины и расписание. Система поддерживает версионирование "
                "расписания и управление пользователями с ролевой моделью доступа."
            ),
            "core_entities": {
                "specialties": {
                    "purpose": "Центральная сущность для группировки студентов по направлениям обучения",
                    "key_fields": ["spec_code", "title", "learn_years"],
                    "business_logic": "Каждая специальность имеет уникальный код и может иметь несколько форм обучения"
                },
                "groups": {
                    "purpose": "Учебные группы студентов, привязанные к специальностям и зданиям",
                    "key_fields": ["name", "building_id", "is_active"],
                    "business_logic": "Группы могут быть активными или устаревшими, привязаны к конкретному зданию"
                },
                "teachers": {
                    "purpose": "Преподавательский состав учебного заведения",
                    "key_fields": ["fio", "is_active"],
                    "business_logic": "Преподаватели могут быть активными или неактивными, связаны с дисциплинами"
                },
                "disciplines": {
                    "purpose": "Учебные предметы, которые преподаются в учебном заведении",
                    "key_fields": ["title", "description"],
                    "business_logic": "Дисциплины связаны с преподавателями и используются в расписании"
                }
            },
            "timetable_system": {
                "overview": (
                    "Система расписания построена на принципе версионирования, где каждая версия "
                    "расписания проходит через статусы от создания до активации. Поддерживается "
                    "как стандартное (шаблонное) расписание, так и ежедневные изменения."
                ),
                "main_tables": {
                    "ttable_versions": "Основная таблица версий расписания с метаданными",
                    "std_ttable": "Стандартное расписание (шаблон) для регулярных занятий",
                    "cards_states_history": "История состояний карточек расписания по группам",
                    "cards_states_details": "Детальная информация о занятиях в карточках"
                },
                "workflow": [
                    "Создание новой версии расписания в статусе 'pending'",
                    "Заполнение данными через std_ttable или cards_states_*",
                    "Проверка ограничений (все активные группы включены)",
                    "Активация версии и деактивация предыдущей",
                    "Возможность отката к предыдущим версиям"
                ]
            },
            "relationships_map": {
                "one_to_many": [
                    "specialties -> groups (одна специальность - много групп)",
                    "buildings -> groups (одно здание - много групп)",
                    "ttable_versions -> std_ttable (одна версия - много записей расписания)",
                    "groups -> cards_states_history (одна группа - много состояний)",
                    "users -> ttable_versions (один пользователь - много версий)"
                ],
                "many_to_many": [
                    "teachers <-> disciplines (преподаватели ведут несколько дисциплин)",
                    "specialties <-> disciplines (специальности включают несколько дисциплин)",
                    "users <-> groups (пользователи могут быть связаны с группами)"
                ],
                "many_to_one": [
                    "groups -> specialties (много групп - одна специальность)",
                    "std_ttable -> teachers (много занятий - один преподаватель)",
                    "std_ttable -> disciplines (много занятий - одна дисциплина)",
                    "users -> roles (много пользователей - одна роль)"
                ]
            },
            "indexes_and_constraints": {
                "primary_keys": "Все таблицы имеют автоинкрементные первичные ключи id",
                "unique_constraints": [
                    "groups.name - уникальные имена групп",
                    "specialties.spec_code - уникальные коды специальностей",
                    "users.username - уникальные имена пользователей"
                ],
                "foreign_keys": [
                    "groups.building_id -> buildings.id",
                    "groups.specialty_id -> specialties.id (предполагается)",
                    "std_ttable.sched_ver_id -> ttable_versions.id",
                    "users.role_id -> roles.id"
                ],
                "performance_indexes": [
                    "Индексы на внешние ключи для оптимизации JOIN операций",
                    "Индексы на поля поиска (specialties.title, teachers.fio)",
                    "Составные индексы для сложных запросов расписания"
                ]
            }
        }
    
    def document_timetable_versioning_logic(self) -> Dict[str, str]:
        """Document the timetable versioning system logic."""
        return {
            "overview": (
                "Система версионирования расписания обеспечивает отслеживание изменений, "
                "создание резервных копий и возможность отката к предыдущим версиям. "
                "Каждая версия имеет статус и может быть активной или неактивной."
            ),
            "version_statuses": (
                "1 - pending (ожидает подтверждения), "
                "2 - accepted (принято и активно), "
                "3 - deprecated (устарело)"
            ),
            "version_types": (
                "standard - стандартное расписание (шаблон), "
                "daily - ежедневное расписание с изменениями"
            ),
            "workflow": (
                "1. Создание новой версии в статусе pending\n"
                "2. Заполнение данными расписания\n"
                "3. Проверка ограничений (все группы должны быть включены)\n"
                "4. Перевод в статус accepted и деактивация предыдущей версии\n"
                "5. Возможность отката через изменение статусов"
            ),
            "constraints": (
                "- Только одна активная версия каждого типа для здания\n"
                "- Все активные группы должны быть включены в расписание\n"
                "- Транзакционность операций для обеспечения целостности\n"
                "- Автоматическое управление флагом is_commited"
            ),
            "tables_involved": [
                "ttable_versions - основная таблица версий",
                "cards_states_history - история состояний карточек",
                "cards_states_details - детали карточек расписания",
                "std_ttable - стандартное расписание"
            ]
        }
    
    def extract_environment_variables(self) -> List[str]:
        """Extract required environment variables from configuration files."""
        env_vars = [
            # PostgreSQL
            "pg_user - Пользователь PostgreSQL",
            "pg_password - Пароль PostgreSQL",
            "pg_db - Имя базы данных PostgreSQL",
            "pg_host - Хост PostgreSQL (локальный)",
            "pg_port - Порт PostgreSQL (локальный)",
            "pg_host_docker - Хост PostgreSQL (Docker)",
            "pg_port_docker - Порт PostgreSQL (Docker)",
            
            # Redis
            "redis_password - Пароль Redis",
            "redis_host - Хост Redis (локальный)",
            "redis_port - Порт Redis (локальный)",
            "redis_host_docker - Хост Redis (Docker)",
            "redis_port_docker - Порт Redis (Docker)",
            
            # Elasticsearch
            "elastic_user - Пользователь Elasticsearch",
            "elastic_password - Пароль Elasticsearch",
            "elastic_host - Хост Elasticsearch (локальный)",
            "elastic_host_docker - Хост Elasticsearch (Docker)",
            "elastic_port - Порт Elasticsearch",
            "elastic_cert - Путь к сертификату Elasticsearch (локальный)",
            "elastic_cert_docker - Путь к сертификату Elasticsearch (Docker)",
            "search_index - Имя индекса для поиска",
            
            # Application
            "APP_MODE - Режим приложения (local/docker/prod)",
            "es_init - Инициализация Elasticsearch при запуске",
            "ENV_FILE - Путь к файлу окружения",
            "ENV_LOCAL_TEST_FILE - Путь к тестовому файлу окружения"
        ]
        
        return env_vars
    
    def document_connection_setup(self) -> Dict[str, str]:
        """Document connection setup procedures."""
        return {
            "postgresql_setup": (
                "1. Установить переменные окружения для PostgreSQL\n"
                "2. Создать пул соединений через asyncpg.create_pool()\n"
                "3. Настроить dependency injection в FastAPI\n"
                "4. Использовать контекстный менеджер для управления соединениями\n"
                "5. Настроить таймауты и параметры пула"
            ),
            "redis_setup": (
                "1. Установить переменные окружения для Redis\n"
                "2. Создать Redis клиент с decode_responses=True\n"
                "3. Настроить пароль для продакшен окружения\n"
                "4. Использовать контекстный менеджер для управления соединениями\n"
                "5. Настроить dependency injection в FastAPI"
            ),
            "elasticsearch_setup": (
                "1. Установить переменные окружения для Elasticsearch\n"
                "2. Создать AsyncElasticsearch клиент\n"
                "3. Настроить SSL сертификаты (опционально)\n"
                "4. Инициализировать индексы при запуске приложения\n"
                "5. Настроить маппинги и алиасы для поиска\n"
                "6. Выполнить первичную индексацию данных"
            ),
            "environment_modes": (
                "local - локальная разработка с локальными сервисами\n"
                "docker - разработка в Docker контейнерах\n"
                "prod - продакшен окружение с внешними сервисами"
            )
        }
    
    def generate_integration_documentation(self) -> IntegrationDocumentation:
        """Generate complete integration documentation."""
        external_services = [
            self.document_postgresql_integration(),
            self.document_redis_integration(),
            self.document_elasticsearch_integration()
        ]
        
        database_tables = self.analyze_database_tables()
        connection_setup = self.document_connection_setup()
        environment_variables = self.extract_environment_variables()
        
        return IntegrationDocumentation(
            external_services=external_services,
            database_tables=database_tables,
            connection_setup=connection_setup,
            environment_variables=environment_variables
        )
    
    def format_integration_markdown(self, integration_doc: IntegrationDocumentation) -> str:
        """Format integration documentation as Markdown."""
        content = []
        
        # Title
        content.append("# Интеграции и База Данных\n")
        content.append("Документация по внешним сервисам и структуре базы данных системы управления расписанием.\n")
        
        # External Services
        content.append("## Внешние Сервисы\n")
        
        for service in integration_doc.external_services:
            content.append(f"### {service.name}\n")
            content.append(f"**Тип:** {service.type}\n")
            content.append(f"**Описание:** {service.description}\n")
            
            # Configuration
            if service.configuration:
                content.append("**Конфигурация:**")
                for key, value in service.configuration.items():
                    content.append(f"- **{key}**: {value}")
                content.append("")
            
            # Connection Details
            if service.connection_details:
                content.append("**Параметры подключения:**")
                for key, value in service.connection_details.items():
                    content.append(f"- **{key}**: {value}")
                content.append("")
            
            # Usage Patterns
            if service.usage_patterns:
                content.append("**Паттерны использования:**")
                for pattern in service.usage_patterns:
                    content.append(f"- {pattern}")
                content.append("")
            
            # Dependencies
            if service.dependencies:
                content.append("**Зависимости:**")
                for dep in service.dependencies:
                    content.append(f"- {dep}")
                content.append("")
            
            content.append("---\n")
        
        # Database Tables
        content.append("## Структура Базы Данных\n")
        
        # Add database schema documentation
        db_schema = self.document_database_schema()
        content.append("### Обзор Схемы\n")
        content.append(f"{db_schema['overview']}\n")
        
        # Core entities
        content.append("### Основные Сущности\n")
        for entity_name, entity_info in db_schema['core_entities'].items():
            content.append(f"#### {entity_name.title()}\n")
            content.append(f"**Назначение:** {entity_info['purpose']}")
            content.append(f"**Ключевые поля:** {', '.join(f'`{field}`' for field in entity_info['key_fields'])}")
            content.append(f"**Бизнес-логика:** {entity_info['business_logic']}\n")
        
        # Timetable system
        timetable_system = db_schema['timetable_system']
        content.append("### Система Расписания\n")
        content.append(f"{timetable_system['overview']}\n")
        
        content.append("**Основные таблицы:**")
        for table_name, description in timetable_system['main_tables'].items():
            content.append(f"- **{table_name}**: {description}")
        content.append("")
        
        content.append("**Рабочий процесс:**")
        for step in timetable_system['workflow']:
            content.append(f"1. {step}")
        content.append("")
        
        # Relationships
        relationships = db_schema['relationships_map']
        content.append("### Связи Между Таблицами\n")
        
        for rel_type, relations in relationships.items():
            rel_title = rel_type.replace('_', '-').title()
            content.append(f"**{rel_title}:**")
            for relation in relations:
                content.append(f"- {relation}")
            content.append("")
        
        # Indexes and constraints
        indexes = db_schema['indexes_and_constraints']
        content.append("### Индексы и Ограничения\n")
        
        content.append(f"**Первичные ключи:** {indexes['primary_keys']}\n")
        
        content.append("**Уникальные ограничения:**")
        for constraint in indexes['unique_constraints']:
            content.append(f"- {constraint}")
        content.append("")
        
        content.append("**Внешние ключи:**")
        for fk in indexes['foreign_keys']:
            content.append(f"- {fk}")
        content.append("")
        
        content.append("**Индексы производительности:**")
        for index in indexes['performance_indexes']:
            content.append(f"- {index}")
        content.append("")
        
        content.append("### Детальная Информация о Таблицах\n")
        
        # Group tables by category
        core_tables = ['specialties', 'groups', 'teachers', 'disciplines']
        timetable_tables = ['timetable', 'ttable_versions', 'std_ttable', 'cards_states_history', 'cards_states_details']
        user_tables = ['users', 'roles']
        other_tables = ['buildings']
        
        table_categories = [
            ("Основные сущности", core_tables),
            ("Расписание и версионирование", timetable_tables),
            ("Пользователи и роли", user_tables),
            ("Вспомогательные таблицы", other_tables)
        ]
        
        for category_name, table_names in table_categories:
            content.append(f"#### {category_name}\n")
            
            for table in integration_doc.database_tables:
                if table.name in table_names:
                    content.append(f"**{table.name}**")
                    content.append(f"{table.description}")
                    
                    if table.columns:
                        content.append("*Основные поля:* " + ", ".join(f"`{col}`" for col in table.columns[:6]))
                        if len(table.columns) > 6:
                            content.append(f" и еще {len(table.columns) - 6} полей")
                    
                    if table.relationships:
                        content.append("*Связи:* " + "; ".join(table.relationships))
                    
                    if table.used_by_modules:
                        content.append("*Используется модулями:* " + ", ".join(table.used_by_modules))
                    
                    content.append("")
            
            content.append("")
        
        # Timetable Versioning Logic
        versioning_logic = self.document_timetable_versioning_logic()
        content.append("### Логика Версионирования Расписания\n")
        
        for key, value in versioning_logic.items():
            if key == "tables_involved":
                content.append("**Задействованные таблицы:**")
                for table in value:
                    content.append(f"- {table}")
            else:
                title = key.replace("_", " ").title()
                content.append(f"**{title}:**")
                content.append(f"{value}\n")
        
        content.append("")
        
        # Connection Setup
        content.append("## Настройка Подключений\n")
        
        for setup_type, instructions in integration_doc.connection_setup.items():
            title = setup_type.replace("_", " ").title()
            content.append(f"### {title}\n")
            content.append(f"{instructions}\n")
        
        # Environment Variables
        content.append("## Переменные Окружения\n")
        content.append("Список всех необходимых переменных окружения для настройки системы:\n")
        
        # Group environment variables by service
        pg_vars = [var for var in integration_doc.environment_variables if var.startswith("pg_")]
        redis_vars = [var for var in integration_doc.environment_variables if var.startswith("redis_")]
        elastic_vars = [var for var in integration_doc.environment_variables if var.startswith("elastic_") or var.startswith("search_")]
        app_vars = [var for var in integration_doc.environment_variables if not any(var.startswith(prefix) for prefix in ["pg_", "redis_", "elastic_", "search_"])]
        
        var_categories = [
            ("PostgreSQL", pg_vars),
            ("Redis", redis_vars),
            ("Elasticsearch", elastic_vars),
            ("Приложение", app_vars)
        ]
        
        for category_name, vars_list in var_categories:
            if vars_list:
                content.append(f"### {category_name}\n")
                for var in vars_list:
                    content.append(f"- `{var}`")
                content.append("")
        
        return "\n".join(content)