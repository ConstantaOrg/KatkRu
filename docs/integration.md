# Интеграции и База Данных

Документация по внешним сервисам и структуре базы данных системы управления расписанием.

## Внешние Сервисы

### PostgreSQL

**Тип:** postgresql

**Описание:** Основная база данных системы, хранящая все данные о специальностях, группах, преподавателях, дисциплинах и расписании. Использует asyncpg для асинхронного взаимодействия с базой данных и поддерживает транзакции для обеспечения целостности данных.

**Конфигурация:**
- **connection_pool**: Используется пул соединений для оптимизации производительности
- **command_timeout**: 60 секунд для выполнения команд
- **isolation_level**: READ COMMITTED / REPEATABLE READ для транзакций
- **async_driver**: asyncpg для асинхронных операций

**Параметры подключения:**
- **host**: pg_host / pg_host_docker
- **port**: pg_port / pg_port_docker
- **database**: pg_db
- **user**: pg_user
- **password**: pg_password

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

---

### Redis

**Тип:** redis

**Описание:** Используется для кэширования данных и хранения сессий пользователей. Обеспечивает быстрый доступ к часто запрашиваемым данным и управление состоянием сессий. Поддерживает различные конфигурации для локальной разработки и продакшена.

**Конфигурация:**
- **decode_responses**: True - автоматическое декодирование ответов в строки
- **connection_pool**: Используется пул соединений для оптимизации производительности
- **password**: Требуется пароль для продакшен окружения
- **timeout**: Настраивается таймаут соединения

**Параметры подключения:**
- **host**: redis_host / redis_host_docker
- **port**: redis_port / redis_port_docker
- **password**: redis_password (только для продакшена)
- **database**: По умолчанию используется база данных 0

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

---

### Elasticsearch

**Тип:** elasticsearch

**Описание:** Используется для полнотекстового поиска по специальностям. Обеспечивает быстрый поиск по коду и названию специальностей с поддержкой автодополнения. Индексирует данные из таблицы specialties для оптимизации поисковых запросов.

**Конфигурация:**
- **index_name**: search_index (из переменной окружения)
- **mappings**: Настроены для поиска по полям code_prefix, spec_title_prefix, spec_title_search
- **aliases**: Используются алиасы для гибкого управления индексами
- **batch_size**: 2000 документов за раз при индексации

**Параметры подключения:**
- **host**: elastic_host / elastic_host_docker
- **port**: elastic_port
- **authentication**: elastic_user / elastic_password (закомментировано)
- **ssl**: ca_certs / verify_certs (закомментировано)
- **scheme**: http/https в зависимости от режима приложения

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

---

## Структура Базы Данных

### Обзор Схемы

База данных системы управления расписанием построена на PostgreSQL и включает основные сущности для управления учебным процессом: специальности, группы, преподаватели, дисциплины и расписание. Система поддерживает версионирование расписания и управление пользователями с ролевой моделью доступа.

### Основные Сущности

#### Specialties

**Назначение:** Центральная сущность для группировки студентов по направлениям обучения
**Ключевые поля:** `spec_code`, `title`, `learn_years`
**Бизнес-логика:** Каждая специальность имеет уникальный код и может иметь несколько форм обучения

#### Groups

**Назначение:** Учебные группы студентов, привязанные к специальностям и зданиям
**Ключевые поля:** `name`, `building_id`, `is_active`
**Бизнес-логика:** Группы могут быть активными или устаревшими, привязаны к конкретному зданию

#### Teachers

**Назначение:** Преподавательский состав учебного заведения
**Ключевые поля:** `fio`, `is_active`
**Бизнес-логика:** Преподаватели могут быть активными или неактивными, связаны с дисциплинами

#### Disciplines

**Назначение:** Учебные предметы, которые преподаются в учебном заведении
**Ключевые поля:** `title`, `description`
**Бизнес-логика:** Дисциплины связаны с преподавателями и используются в расписании

### Система Расписания

Система расписания построена на принципе версионирования, где каждая версия расписания проходит через статусы от создания до активации. Поддерживается как стандартное (шаблонное) расписание, так и ежедневные изменения.

**Основные таблицы:**
- **ttable_versions**: Основная таблица версий расписания с метаданными
- **std_ttable**: Стандартное расписание (шаблон) для регулярных занятий
- **cards_states_history**: История состояний карточек расписания по группам
- **cards_states_details**: Детальная информация о занятиях в карточках

**Рабочий процесс:**
1. Создание новой версии расписания в статусе 'pending'
1. Заполнение данными через std_ttable или cards_states_*
1. Проверка ограничений (все активные группы включены)
1. Активация версии и деактивация предыдущей
1. Возможность отката к предыдущим версиям

### Связи Между Таблицами

**One-To-Many:**
- specialties -> groups (одна специальность - много групп)
- buildings -> groups (одно здание - много групп)
- ttable_versions -> std_ttable (одна версия - много записей расписания)
- groups -> cards_states_history (одна группа - много состояний)
- users -> ttable_versions (один пользователь - много версий)

**Many-To-Many:**
- teachers <-> disciplines (преподаватели ведут несколько дисциплин)
- specialties <-> disciplines (специальности включают несколько дисциплин)
- users <-> groups (пользователи могут быть связаны с группами)

**Many-To-One:**
- groups -> specialties (много групп - одна специальность)
- std_ttable -> teachers (много занятий - один преподаватель)
- std_ttable -> disciplines (много занятий - одна дисциплина)
- users -> roles (много пользователей - одна роль)

### Индексы и Ограничения

**Первичные ключи:** Все таблицы имеют автоинкрементные первичные ключи id

**Уникальные ограничения:**
- groups.name - уникальные имена групп
- specialties.spec_code - уникальные коды специальностей
- users.username - уникальные имена пользователей

**Внешние ключи:**
- groups.building_id -> buildings.id
- groups.specialty_id -> specialties.id (предполагается)
- std_ttable.sched_ver_id -> ttable_versions.id
- users.role_id -> roles.id

**Индексы производительности:**
- Индексы на внешние ключи для оптимизации JOIN операций
- Индексы на поля поиска (specialties.title, teachers.fio)
- Составные индексы для сложных запросов расписания

### Детальная Информация о Таблицах

#### Основные сущности

**specialties**
Хранит информацию о специальностях учебного заведения
*Основные поля:* `id`, `spec_code`, `title`, `description`, `learn_years`, `full_time`
 и еще 3 полей
*Связи:* groups (one-to-many); disciplines (many-to-many)
*Используется модулями:* specialties, groups, n8n_ui, elastic_search

**groups**
Содержит информацию об учебных группах
*Основные поля:* `id`, `name`, `building_id`, `is_active`
*Связи:* specialties (many-to-one); timetable (one-to-many); users (many-to-many)
*Используется модулями:* groups, timetable, users, n8n_ui

**teachers**
Информация о преподавателях
*Основные поля:* `id`, `fio`, `is_active`
*Связи:* disciplines (many-to-many); timetable (one-to-many)
*Используется модулями:* teachers, timetable, disciplines

**disciplines**
Учебные дисциплины (предметы)
*Основные поля:* `id`, `title`, `description`
*Связи:* teachers (many-to-many); specialties (many-to-many); timetable (one-to-many)
*Используется модулями:* disciplines, teachers, timetable, specialties


#### Расписание и версионирование

**timetable**
Основная таблица расписания занятий
*Основные поля:* `id`, `group_id`, `teacher_id`, `discipline_id`, `position`, `aud`
 и еще 1 полей
*Связи:* groups (many-to-one); teachers (many-to-one); disciplines (many-to-one); ttable_versions (many-to-one)
*Используется модулями:* timetable, ttable_versions

**ttable_versions**
Версии расписания для отслеживания изменений
*Основные поля:* `id`, `building_id`, `schedule_date`, `type`, `status_id`, `user_id`
 и еще 2 полей
*Связи:* timetable (one-to-many); users (many-to-one); cards_states_history (one-to-many)
*Используется модулями:* ttable_versions, timetable

**cards_states_history**
История состояний карточек расписания
*Основные поля:* `id`, `sched_ver_id`, `group_id`, `is_current`, `status_id`
*Связи:* ttable_versions (many-to-one); groups (many-to-one); cards_states_details (one-to-many)
*Используется модулями:* timetable, ttable_versions

**cards_states_details**
Детали карточек расписания
*Основные поля:* `id`, `card_hist_id`, `discipline_id`, `teacher_id`, `position`, `aud`
*Связи:* cards_states_history (many-to-one); disciplines (many-to-one); teachers (many-to-one)
*Используется модулями:* timetable

**std_ttable**
Стандартное расписание (шаблон)
*Основные поля:* `id`, `sched_ver_id`, `group_id`, `discipline_id`, `position`, `aud`
 и еще 2 полей
*Связи:* ttable_versions (many-to-one); groups (many-to-one); disciplines (many-to-one); teachers (many-to-one)
*Используется модулями:* timetable


#### Пользователи и роли

**users**
Пользователи системы с ролями и правами доступа
*Основные поля:* `id`, `username`, `email`, `password_hash`, `role_id`, `is_active`
*Связи:* roles (many-to-one); ttable_versions (one-to-many); user_sessions (one-to-many)
*Используется модулями:* users, ttable_versions

**roles**
Роли пользователей (методист, администратор, только чтение)
*Основные поля:* `id`, `name`, `permissions`
*Связи:* users (one-to-many)
*Используется модулями:* users


#### Вспомогательные таблицы

**buildings**
Здания учебного заведения
*Основные поля:* `id`, `name`, `address`
*Связи:* groups (one-to-many)
*Используется модулями:* groups, timetable


### Логика Версионирования Расписания

**Overview:**
Система версионирования расписания обеспечивает отслеживание изменений, создание резервных копий и возможность отката к предыдущим версиям. Каждая версия имеет статус и может быть активной или неактивной.

**Version Statuses:**
1 - pending (ожидает подтверждения), 2 - accepted (принято и активно), 3 - deprecated (устарело)

**Version Types:**
standard - стандартное расписание (шаблон), daily - ежедневное расписание с изменениями

**Workflow:**
1. Создание новой версии в статусе pending
2. Заполнение данными расписания
3. Проверка ограничений (все группы должны быть включены)
4. Перевод в статус accepted и деактивация предыдущей версии
5. Возможность отката через изменение статусов

**Constraints:**
- Только одна активная версия каждого типа для здания
- Все активные группы должны быть включены в расписание
- Транзакционность операций для обеспечения целостности
- Автоматическое управление флагом is_commited

**Задействованные таблицы:**
- ttable_versions - основная таблица версий
- cards_states_history - история состояний карточек
- cards_states_details - детали карточек расписания
- std_ttable - стандартное расписание

## Настройка Подключений

### Postgresql Setup

1. Установить переменные окружения для PostgreSQL
2. Создать пул соединений через asyncpg.create_pool()
3. Настроить dependency injection в FastAPI
4. Использовать контекстный менеджер для управления соединениями
5. Настроить таймауты и параметры пула

### Redis Setup

1. Установить переменные окружения для Redis
2. Создать Redis клиент с decode_responses=True
3. Настроить пароль для продакшен окружения
4. Использовать контекстный менеджер для управления соединениями
5. Настроить dependency injection в FastAPI

### Elasticsearch Setup

1. Установить переменные окружения для Elasticsearch
2. Создать AsyncElasticsearch клиент
3. Настроить SSL сертификаты (опционально)
4. Инициализировать индексы при запуске приложения
5. Настроить маппинги и алиасы для поиска
6. Выполнить первичную индексацию данных

### Environment Modes

local - локальная разработка с локальными сервисами
docker - разработка в Docker контейнерах
prod - продакшен окружение с внешними сервисами

## Переменные Окружения

Список всех необходимых переменных окружения для настройки системы:

### PostgreSQL

- `pg_user - Пользователь PostgreSQL`
- `pg_password - Пароль PostgreSQL`
- `pg_db - Имя базы данных PostgreSQL`
- `pg_host - Хост PostgreSQL (локальный)`
- `pg_port - Порт PostgreSQL (локальный)`
- `pg_host_docker - Хост PostgreSQL (Docker)`
- `pg_port_docker - Порт PostgreSQL (Docker)`

### Redis

- `redis_password - Пароль Redis`
- `redis_host - Хост Redis (локальный)`
- `redis_port - Порт Redis (локальный)`
- `redis_host_docker - Хост Redis (Docker)`
- `redis_port_docker - Порт Redis (Docker)`

### Elasticsearch

- `elastic_user - Пользователь Elasticsearch`
- `elastic_password - Пароль Elasticsearch`
- `elastic_host - Хост Elasticsearch (локальный)`
- `elastic_host_docker - Хост Elasticsearch (Docker)`
- `elastic_port - Порт Elasticsearch`
- `elastic_cert - Путь к сертификату Elasticsearch (локальный)`
- `elastic_cert_docker - Путь к сертификату Elasticsearch (Docker)`
- `search_index - Имя индекса для поиска`

### Приложение

- `APP_MODE - Режим приложения (local/docker/prod)`
- `es_init - Инициализация Elasticsearch при запуске`
- `ENV_FILE - Путь к файлу окружения`
- `ENV_LOCAL_TEST_FILE - Путь к тестовому файлу окружения`
