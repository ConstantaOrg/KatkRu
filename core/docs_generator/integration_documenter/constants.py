"""
Constants and configurations for integration documentation.
"""

from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path


@dataclass
class ConfigFiles:
    """Configuration files to analyze."""
    FILES: List[str] = None
    
    def __post_init__(self):
        if self.FILES is None:
            self.FILES = [
                'core/config_dir/config.py',
                'core/data/postgre.py',
                'core/data/redis_storage.py',
                'core/api/elastic_search.py'
            ]


@dataclass
class DatabaseTableInfo:
    """Information about a database table."""
    description: str
    columns: List[str]
    relationships: List[str]
    used_by_modules: List[str]


@dataclass
class DatabaseTablesInfo:
    """Database tables information."""
    TABLES: Dict[str, DatabaseTableInfo] = None
    
    def __post_init__(self):
        if self.TABLES is None:
            self.TABLES = {
                'specialties': DatabaseTableInfo(
                    description='Хранит информацию о специальностях учебного заведения',
                    columns=['id', 'spec_code', 'title', 'description', 'learn_years', 'full_time', 'free_form', 'evening_form', 'cost_per_year'],
                    relationships=['groups (one-to-many)', 'disciplines (many-to-many)'],
                    used_by_modules=['specialties', 'groups', 'n8n_ui', 'elastic_search']
                ),
                'groups': DatabaseTableInfo(
                    description='Содержит информацию об учебных группах',
                    columns=['id', 'name', 'building_id', 'is_active'],
                    relationships=['specialties (many-to-one)', 'timetable (one-to-many)', 'users (many-to-many)'],
                    used_by_modules=['groups', 'timetable', 'users', 'n8n_ui']
                ),
                'teachers': DatabaseTableInfo(
                    description='Информация о преподавателях',
                    columns=['id', 'fio', 'is_active'],
                    relationships=['disciplines (many-to-many)', 'timetable (one-to-many)'],
                    used_by_modules=['teachers', 'timetable', 'disciplines']
                ),
                'disciplines': DatabaseTableInfo(
                    description='Учебные дисциплины (предметы)',
                    columns=['id', 'title', 'description'],
                    relationships=['teachers (many-to-many)', 'specialties (many-to-many)', 'timetable (one-to-many)'],
                    used_by_modules=['disciplines', 'teachers', 'timetable', 'specialties']
                ),
                'timetable': DatabaseTableInfo(
                    description='Основная таблица расписания занятий',
                    columns=['id', 'group_id', 'teacher_id', 'discipline_id', 'position', 'aud', 'week_day'],
                    relationships=['groups (many-to-one)', 'teachers (many-to-one)', 'disciplines (many-to-one)', 'ttable_versions (many-to-one)'],
                    used_by_modules=['timetable', 'ttable_versions']
                ),
                'ttable_versions': DatabaseTableInfo(
                    description='Версии расписания для отслеживания изменений',
                    columns=['id', 'building_id', 'schedule_date', 'type', 'status_id', 'user_id', 'is_commited', 'last_modified_at'],
                    relationships=['timetable (one-to-many)', 'users (many-to-one)', 'cards_states_history (one-to-many)'],
                    used_by_modules=['ttable_versions', 'timetable']
                ),
                'users': DatabaseTableInfo(
                    description='Пользователи системы с ролями и правами доступа',
                    columns=['id', 'username', 'email', 'password_hash', 'role_id', 'is_active'],
                    relationships=['roles (many-to-one)', 'ttable_versions (one-to-many)', 'user_sessions (one-to-many)'],
                    used_by_modules=['users', 'ttable_versions']
                ),
                'roles': DatabaseTableInfo(
                    description='Роли пользователей (методист, администратор, только чтение)',
                    columns=['id', 'name', 'permissions'],
                    relationships=['users (one-to-many)'],
                    used_by_modules=['users']
                ),
                'buildings': DatabaseTableInfo(
                    description='Здания учебного заведения',
                    columns=['id', 'name', 'address'],
                    relationships=['groups (one-to-many)'],
                    used_by_modules=['groups', 'timetable']
                ),
                'cards_states_history': DatabaseTableInfo(
                    description='История состояний карточек расписания',
                    columns=['id', 'sched_ver_id', 'group_id', 'is_current', 'status_id'],
                    relationships=['ttable_versions (many-to-one)', 'groups (many-to-one)', 'cards_states_details (one-to-many)'],
                    used_by_modules=['timetable', 'ttable_versions']
                ),
                'cards_states_details': DatabaseTableInfo(
                    description='Детали карточек расписания',
                    columns=['id', 'card_hist_id', 'discipline_id', 'teacher_id', 'position', 'aud'],
                    relationships=['cards_states_history (many-to-one)', 'disciplines (many-to-one)', 'teachers (many-to-one)'],
                    used_by_modules=['timetable']
                ),
                'std_ttable': DatabaseTableInfo(
                    description='Стандартное расписание (шаблон)',
                    columns=['id', 'sched_ver_id', 'group_id', 'discipline_id', 'position', 'aud', 'teacher_id', 'week_day'],
                    relationships=['ttable_versions (many-to-one)', 'groups (many-to-one)', 'disciplines (many-to-one)', 'teachers (many-to-one)'],
                    used_by_modules=['timetable']
                )
            }


@dataclass
class ServiceTypes:
    """Types of external services."""
    ELASTICSEARCH: str = 'elasticsearch'
    REDIS: str = 'redis'
    POSTGRESQL: str = 'postgresql'


@dataclass
class EnvironmentVariables:
    """Required environment variables."""
    VARIABLES: List[str] = None
    
    def __post_init__(self):
        if self.VARIABLES is None:
            self.VARIABLES = [
                'POSTGRES_HOST',
                'POSTGRES_PORT', 
                'POSTGRES_DB',
                'POSTGRES_USER',
                'POSTGRES_PASSWORD',
                'REDIS_HOST',
                'REDIS_PORT',
                'REDIS_PASSWORD',
                'ELASTICSEARCH_HOST',
                'ELASTICSEARCH_PORT',
                'ELASTICSEARCH_INDEX_PREFIX',
                'JWT_SECRET_KEY',
                'JWT_ALGORITHM',
                'JWT_ACCESS_TOKEN_EXPIRE_MINUTES',
                'JWT_REFRESH_TOKEN_EXPIRE_DAYS',
                'ALLOWED_IPS',
                'LOG_LEVEL',
                'DEBUG_MODE'
            ]


@dataclass
class ConnectionSetupTemplates:
    """Templates for connection setup documentation."""
    TEMPLATES: Dict[str, str] = None
    
    def __post_init__(self):
        if self.TEMPLATES is None:
            self.TEMPLATES = {
                'postgresql': """
PostgreSQL подключение настраивается через переменные окружения:
- POSTGRES_HOST: хост базы данных
- POSTGRES_PORT: порт (по умолчанию 5432)
- POSTGRES_DB: имя базы данных
- POSTGRES_USER: пользователь
- POSTGRES_PASSWORD: пароль

Пул соединений настраивается в core/data/postgre.py с параметрами:
- min_size: минимальное количество соединений
- max_size: максимальное количество соединений
- command_timeout: таймаут команд
                """.strip(),
                
                'redis': """
Redis подключение настраивается через переменные окружения:
- REDIS_HOST: хост Redis сервера
- REDIS_PORT: порт (по умолчанию 6379)
- REDIS_PASSWORD: пароль (опционально)

Используется для кэширования и хранения сессий пользователей.
Настройки пула соединений в core/data/redis_storage.py.
                """.strip(),
                
                'elasticsearch': """
Elasticsearch подключение настраивается через переменные окружения:
- ELASTICSEARCH_HOST: хост Elasticsearch
- ELASTICSEARCH_PORT: порт (по умолчанию 9200)
- ELASTICSEARCH_INDEX_PREFIX: префикс для индексов

Используется для полнотекстового поиска по данным системы.
Конфигурация клиента в core/api/elastic_search.py.
                """.strip()
            }


# Create instances for easy access
CONFIG_FILES = ConfigFiles()
DATABASE_TABLES_INFO = DatabaseTablesInfo()
SERVICE_TYPES = ServiceTypes()
ENVIRONMENT_VARIABLES = EnvironmentVariables()
CONNECTION_SETUP_TEMPLATES = ConnectionSetupTemplates()