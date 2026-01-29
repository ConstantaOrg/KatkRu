# Интеграции и внешние сервисы

Документация по интеграциям с внешними сервисами и настройке подключений.

## Внешние сервисы

### Elasticsearch

**Тип:** elasticsearch

**Описание:** Используется для полнотекстового поиска по специальностям. Обеспечивает быстрый поиск по коду и названию специальностей с поддержкой автодополнения. Индексирует данные из таблицы specialties для оптимизации поисковых запросов.

**Конфигурация:**
- **index_name:** search_index (из переменной окружения)
- **mappings:** Настроены для поиска по полям code_prefix, spec_title_prefix, spec_title_search
- **aliases:** Используются алиасы для гибкого управления индексами
- **batch_size:** 2000 документов за раз при индексации

**Детали подключения:**
- **host:** elastic_host / elastic_host_docker
- **port:** elastic_port
- **authentication:** elastic_user / elastic_password (закомментировано)
- **ssl:** ca_certs / verify_certs (закомментировано)
- **scheme:** http/https в зависимости от режима приложения

**Паттерны использования:**
- Автодополнение поиска специальностей (/public/elastic/autocomplete_spec)
- Расширенный поиск специальностей (/public/elastic/ext_spec)
- Инициализация индекса при запуске приложения
- Батчевая индексация данных из PostgreSQL

**Зависимости:**
- AsyncElasticsearch клиент
- Конфигурация из core.config_dir.config
- Настройки индекса из core.config_dir.index_settings
- Данные из PostgreSQL (таблица specialties)

### Redis

**Тип:** redis

**Описание:** Используется для кэширования данных и хранения сессий пользователей. Обеспечивает быстрый доступ к часто запрашиваемым данным и управление состоянием сессий. Поддерживает различные конфигурации для локальной разработки и продакшена.

**Конфигурация:**
- **decode_responses:** True - автоматическое декодирование ответов в строки
- **connection_pool:** Используется пул соединений для оптимизации производительности
- **password:** Требуется пароль для продакшен окружения
- **timeout:** Настраивается таймаут соединения

**Детали подключения:**
- **host:** redis_host / redis_host_docker
- **port:** redis_port / redis_port_docker
- **password:** redis_password (только для продакшена)
- **database:** По умолчанию используется база данных 0

**Паттерны использования:**
- Кэширование результатов поисковых запросов
- Хранение JWT токенов и сессий пользователей
- Кэширование данных расписания для быстрого доступа
- Временное хранение состояния импорта данных

**Зависимости:**
- Redis.asyncio клиент
- Конфигурация из core.config_dir.config
- Контекстный менеджер для управления соединениями
- FastAPI dependency injection система

### PostgreSQL

**Тип:** postgresql

**Описание:** Основная база данных системы, хранящая все данные о специальностях, группах, преподавателях, дисциплинах и расписании. Использует asyncpg для асинхронного взаимодействия с базой данных и поддерживает транзакции для обеспечения целостности данных.

**Конфигурация:**
- **connection_pool:** Используется пул соединений для оптимизации производительности
- **command_timeout:** 60 секунд для выполнения команд
- **isolation_level:** READ COMMITTED / REPEATABLE READ для транзакций
- **async_driver:** asyncpg для асинхронных операций

**Детали подключения:**
- **host:** pg_host / pg_host_docker
- **port:** pg_port / pg_port_docker
- **database:** pg_db
- **user:** pg_user
- **password:** pg_password

**Паттерны использования:**
- CRUD операции для всех основных сущностей
- Сложные запросы с JOIN для получения связанных данных
- Транзакционные операции для импорта расписания
- Batch операции для массовой вставки данных
- Версионирование расписания с поддержкой отката

**Зависимости:**
- asyncpg драйвер
- Пул соединений AsyncPG
- SQL запросы в модулях *_sql.py
- Конфигурация из core.config_dir.config
- FastAPI dependency injection система

## Таблицы базы данных

### specialties

**Описание:** Хранит информацию о специальностях учебного заведения

**Колонки:**
- id
- spec_code
- title
- description
- learn_years
- full_time
- free_form
- evening_form
- cost_per_year

**Связи:**
- groups (one-to-many)
- disciplines (many-to-many)

**Используется модулями:**
- specialties
- groups
- n8n_ui
- elastic_search

### groups

**Описание:** Содержит информацию об учебных группах

**Колонки:**
- id
- name
- building_id
- is_active

**Связи:**
- specialties (many-to-one)
- timetable (one-to-many)
- users (many-to-many)

**Используется модулями:**
- groups
- timetable
- users
- n8n_ui

### teachers

**Описание:** Информация о преподавателях

**Колонки:**
- id
- fio
- is_active

**Связи:**
- disciplines (many-to-many)
- timetable (one-to-many)

**Используется модулями:**
- teachers
- timetable
- disciplines

### disciplines

**Описание:** Учебные дисциплины (предметы)

**Колонки:**
- id
- title
- description

**Связи:**
- teachers (many-to-many)
- specialties (many-to-many)
- timetable (one-to-many)

**Используется модулями:**
- disciplines
- teachers
- timetable
- specialties

### timetable

**Описание:** Основная таблица расписания занятий

**Колонки:**
- id
- group_id
- teacher_id
- discipline_id
- position
- aud
- week_day

**Связи:**
- groups (many-to-one)
- teachers (many-to-one)
- disciplines (many-to-one)
- ttable_versions (many-to-one)

**Используется модулями:**
- timetable
- ttable_versions

### ttable_versions

**Описание:** Версии расписания для отслеживания изменений

**Колонки:**
- id
- building_id
- schedule_date
- type
- status_id
- user_id
- is_commited
- last_modified_at

**Связи:**
- timetable (one-to-many)
- users (many-to-one)
- cards_states_history (one-to-many)

**Используется модулями:**
- ttable_versions
- timetable

### users

**Описание:** Пользователи системы с ролями и правами доступа

**Колонки:**
- id
- username
- email
- password_hash
- role_id
- is_active

**Связи:**
- roles (many-to-one)
- ttable_versions (one-to-many)
- user_sessions (one-to-many)

**Используется модулями:**
- users
- ttable_versions

### roles

**Описание:** Роли пользователей (методист, администратор, только чтение)

**Колонки:**
- id
- name
- permissions

**Связи:**
- users (one-to-many)

**Используется модулями:**
- users

### buildings

**Описание:** Здания учебного заведения

**Колонки:**
- id
- name
- address

**Связи:**
- groups (one-to-many)

**Используется модулями:**
- groups
- timetable

### cards_states_history

**Описание:** История состояний карточек расписания

**Колонки:**
- id
- sched_ver_id
- group_id
- is_current
- status_id

**Связи:**
- ttable_versions (many-to-one)
- groups (many-to-one)
- cards_states_details (one-to-many)

**Используется модулями:**
- timetable
- ttable_versions

### cards_states_details

**Описание:** Детали карточек расписания

**Колонки:**
- id
- card_hist_id
- discipline_id
- teacher_id
- position
- aud

**Связи:**
- cards_states_history (many-to-one)
- disciplines (many-to-one)
- teachers (many-to-one)

**Используется модулями:**
- timetable

### std_ttable

**Описание:** Стандартное расписание (шаблон)

**Колонки:**
- id
- sched_ver_id
- group_id
- discipline_id
- position
- aud
- teacher_id
- week_day

**Связи:**
- ttable_versions (many-to-one)
- groups (many-to-one)
- disciplines (many-to-one)
- teachers (many-to-one)

**Используется модулями:**
- timetable

## Настройка подключений

### Postgresql

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

### Redis

Redis подключение настраивается через переменные окружения:
- REDIS_HOST: хост Redis сервера
- REDIS_PORT: порт (по умолчанию 6379)
- REDIS_PASSWORD: пароль (опционально)

Используется для кэширования и хранения сессий пользователей.
Настройки пула соединений в core/data/redis_storage.py.

### Elasticsearch

Elasticsearch подключение настраивается через переменные окружения:
- ELASTICSEARCH_HOST: хост Elasticsearch
- ELASTICSEARCH_PORT: порт (по умолчанию 9200)
- ELASTICSEARCH_INDEX_PREFIX: префикс для индексов

Используется для полнотекстового поиска по данным системы.
Конфигурация клиента в core/api/elastic_search.py.

## Переменные окружения

Следующие переменные окружения должны быть настроены:

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `ELASTICSEARCH_HOST`
- `ELASTICSEARCH_PORT`
- `ELASTICSEARCH_INDEX_PREFIX`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`
- `ALLOWED_IPS`
- `LOG_LEVEL`
- `DEBUG_MODE`
