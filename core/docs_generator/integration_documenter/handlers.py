"""
Handler functions for integration documentation operations.
"""

from typing import Dict, List, Any
from pathlib import Path

from .models import DatabaseTable, ExternalService, IntegrationDocumentation
from .constants import (
    CONFIG_FILES, DATABASE_TABLES_INFO, SERVICE_TYPES, 
    ENVIRONMENT_VARIABLES, CONNECTION_SETUP_TEMPLATES
)


def document_elasticsearch_integration() -> ExternalService:
    """Document Elasticsearch integration."""
    return ExternalService(
        name="Elasticsearch",
        type=SERVICE_TYPES.ELASTICSEARCH,
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


def document_redis_integration() -> ExternalService:
    """Document Redis integration."""
    return ExternalService(
        name="Redis",
        type=SERVICE_TYPES.REDIS,
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


def document_postgresql_integration() -> ExternalService:
    """Document PostgreSQL integration."""
    return ExternalService(
        name="PostgreSQL",
        type=SERVICE_TYPES.POSTGRESQL,
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


def analyze_database_tables() -> List[DatabaseTable]:
    """Analyze and document database tables."""
    tables = []
    
    for table_name, info in DATABASE_TABLES_INFO.TABLES.items():
        table = DatabaseTable(
            name=table_name,
            description=info.description,
            columns=info.columns,
            relationships=info.relationships,
            used_by_modules=info.used_by_modules
        )
        tables.append(table)
    
    return tables


def document_database_schema() -> Dict[str, Any]:
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
                "cards_states_details": "Детальная информация о каждом занятии в карточке"
            },
            "workflow": {
                "creation": "Создание новой версии расписания (статус: черновик)",
                "editing": "Редактирование карточек расписания по группам",
                "validation": "Проверка корректности и отсутствия конфликтов",
                "activation": "Активация версии и деактивация предыдущей"
            }
        },
        "user_management": {
            "overview": "Система управления пользователями с ролевой моделью доступа",
            "roles": {
                "methodist": "Полный доступ к редактированию расписания и данных",
                "admin": "Административные функции и управление пользователями",
                "read_only": "Только просмотр данных без возможности изменения"
            },
            "authentication": {
                "method": "JWT токены с refresh механизмом",
                "storage": "Сессии хранятся в Redis для быстрого доступа",
                "security": "IP whitelist и middleware для проверки доступа"
            }
        },
        "data_integrity": {
            "constraints": "Внешние ключи обеспечивают целостность связей между таблицами",
            "transactions": "Критические операции выполняются в транзакциях",
            "versioning": "Система версионирования предотвращает потерю данных",
            "audit": "История изменений сохраняется для аудита и отката"
        }
    }


def document_timetable_versioning_logic() -> Dict[str, str]:
    """Document the timetable versioning system logic."""
    return {
        "overview": (
            "Система версионирования расписания обеспечивает контролируемое управление изменениями "
            "расписания с возможностью отката и аудита. Каждая версия проходит через определенные "
            "статусы и может быть активирована только после валидации."
        ),
        "version_lifecycle": (
            "1. Создание версии (статус: черновик)\n"
            "2. Редактирование карточек по группам\n"
            "3. Валидация на конфликты и ошибки\n"
            "4. Активация версии (статус: активная)\n"
            "5. Деактивация предыдущей версии"
        ),
        "cards_system": (
            "Карточки расписания (cards_states_history) представляют состояние расписания "
            "для конкретной группы в определенной версии. Каждая карточка содержит детали "
            "занятий (cards_states_details) с информацией о дисциплине, преподавателе и аудитории."
        ),
        "conflict_resolution": (
            "Система автоматически проверяет конфликты:\n"
            "- Занятость аудиторий в одно время\n"
            "- Занятость преподавателей\n"
            "- Превышение лимитов занятий\n"
            "- Корректность временных слотов"
        ),
        "rollback_mechanism": (
            "В случае проблем с активной версией можно:\n"
            "- Откатиться к предыдущей стабильной версии\n"
            "- Создать новую версию на основе любой предыдущей\n"
            "- Сравнить изменения между версиями\n"
            "- Восстановить данные из архива"
        ),
        "performance_optimization": (
            "Для оптимизации производительности:\n"
            "- Индексы на часто используемые поля\n"
            "- Кэширование активной версии в Redis\n"
            "- Batch операции для массовых изменений\n"
            "- Асинхронная обработка больших операций"
        )
    }


def extract_environment_variables() -> List[str]:
    """Extract required environment variables from configuration files."""
    return ENVIRONMENT_VARIABLES.VARIABLES.copy()


def document_connection_setup() -> Dict[str, str]:
    """Document connection setup procedures."""
    return CONNECTION_SETUP_TEMPLATES.TEMPLATES.copy()


def generate_integration_documentation(project_root: Path) -> IntegrationDocumentation:
    """Generate complete integration documentation."""
    external_services = [
        document_elasticsearch_integration(),
        document_redis_integration(),
        document_postgresql_integration()
    ]
    
    database_tables = analyze_database_tables()
    connection_setup = document_connection_setup()
    environment_variables = extract_environment_variables()
    
    return IntegrationDocumentation(
        external_services=external_services,
        database_tables=database_tables,
        connection_setup=connection_setup,
        environment_variables=environment_variables
    )


def format_integration_markdown(integration_doc: IntegrationDocumentation) -> str:
    """Format integration documentation as Markdown."""
    content = []
    
    # Header
    content.append("# Интеграции и внешние сервисы")
    content.append("")
    content.append("Документация по интеграциям с внешними сервисами и настройке подключений.")
    content.append("")
    
    # External Services
    content.append("## Внешние сервисы")
    content.append("")
    
    for service in integration_doc.external_services:
        content.append(f"### {service.name}")
        content.append("")
        content.append(f"**Тип:** {service.type}")
        content.append("")
        content.append(f"**Описание:** {service.description}")
        content.append("")
        
        # Configuration
        content.append("**Конфигурация:**")
        for key, value in service.configuration.items():
            content.append(f"- **{key}:** {value}")
        content.append("")
        
        # Connection Details
        content.append("**Детали подключения:**")
        for key, value in service.connection_details.items():
            content.append(f"- **{key}:** {value}")
        content.append("")
        
        # Usage Patterns
        content.append("**Паттерны использования:**")
        for pattern in service.usage_patterns:
            content.append(f"- {pattern}")
        content.append("")
        
        # Dependencies
        content.append("**Зависимости:**")
        for dependency in service.dependencies:
            content.append(f"- {dependency}")
        content.append("")
    
    # Database Tables
    content.append("## Таблицы базы данных")
    content.append("")
    
    for table in integration_doc.database_tables:
        content.append(f"### {table.name}")
        content.append("")
        content.append(f"**Описание:** {table.description}")
        content.append("")
        
        # Columns
        content.append("**Колонки:**")
        for column in table.columns:
            content.append(f"- {column}")
        content.append("")
        
        # Relationships
        content.append("**Связи:**")
        for relationship in table.relationships:
            content.append(f"- {relationship}")
        content.append("")
        
        # Used by modules
        content.append("**Используется модулями:**")
        for module in table.used_by_modules:
            content.append(f"- {module}")
        content.append("")
    
    # Connection Setup
    content.append("## Настройка подключений")
    content.append("")
    
    for service_name, setup_info in integration_doc.connection_setup.items():
        content.append(f"### {service_name.title()}")
        content.append("")
        content.append(setup_info)
        content.append("")
    
    # Environment Variables
    content.append("## Переменные окружения")
    content.append("")
    content.append("Следующие переменные окружения должны быть настроены:")
    content.append("")
    
    for var in integration_doc.environment_variables:
        content.append(f"- `{var}`")
    content.append("")
    
    return "\n".join(content)