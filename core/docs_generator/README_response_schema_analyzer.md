# Response Schema Analyzer

Анализатор API endpoints для создания response схем. Помогает понять структуру ответов и предлагает схемы для документации.

## Архитектура

Модуль рефакторен в соответствии с паттерном docs_generator и разделен на компоненты:

```
response_schema_analyzer/
├── __init__.py          # Экспорты модуля
├── analyzer.py          # Основной класс анализатора
├── constants.py         # Константы конфигурации
├── handlers.py          # Вспомогательные функции
├── models.py           # Модели данных
└── README.md           # Документация модуля
```

## Использование

### Базовое использование

```python
from core.docs_generator.response_schema_analyzer import ResponseSchemaAnalyzer

# Создаем анализатор
analyzer = ResponseSchemaAnalyzer()

# Анализируем все API файлы
report = analyzer.analyze_all_files()
print(f"Найдено файлов: {report.total_files}")
print(f"Найдено endpoints: {report.total_endpoints}")

# Генерируем отчет
markdown_report = analyzer.generate_report()

# Сохраняем отчет
analyzer.save_report("response_schemas_analysis.md")

# Получаем статистику
stats = analyzer.get_statistics()
print(f"Статистика: {stats}")
```

### Анализ конкретного файла

```python
from pathlib import Path
from core.docs_generator.response_schema_analyzer import ResponseSchemaAnalyzer

analyzer = ResponseSchemaAnalyzer()

# Анализируем конкретный файл
file_path = Path("core/api/groups_tab.py")
result = analyzer.analyze_file(file_path)

if result.analysis_success:
    for endpoint in result.endpoints:
        print(f"{endpoint.method} {endpoint.path} - {endpoint.function_name}")
        print(f"Return statements: {len(endpoint.return_statements)}")
```

### Генерация схем

```python
# Получаем предложения схем для файла
schemas = analyzer.get_endpoint_schemas("groups_tab.py")

for schema in schemas:
    print(f"Схема: {schema.class_name}")
    print(f"Уверенность: {schema.confidence_score:.2f}")
    print(f"Базовые классы: {schema.suggested_base_classes}")

# Генерируем код Python для схем
code = analyzer.generate_schema_code_for_file("groups_tab.py")
print(code)
```

### Запуск из командной строки

```bash
python core/docs_generator/response_schema_analyzer.py
```

Это создаст файл `response_schemas_analysis.md` с полным анализом всех API endpoints.

## Компоненты

### Модели данных

- `EndpointAnalysis`: Результат анализа одного endpoint
- `SchemaAnalysis`: Информация о предлагаемой схеме
- `ReturnStatement`: Данные о return statement
- `FileAnalysisResult`: Результат анализа файла
- `AnalysisReport`: Полный отчет анализа

### Константы

- `ROUTER_METHODS`: Поддерживаемые HTTP методы
- `SCHEMA_PATTERNS`: Правила обнаружения паттернов
- `FILE_PATTERNS`: Конфигурация анализа файлов
- `SCHEMA_NAME_PATTERNS`: Соглашения именования схем

### Обработчики

- `analyze_file_content()`: Анализ одного API файла
- `suggest_response_schema()`: Генерация предложений схем
- `generate_schema_code()`: Создание кода Python схем
- `extract_return_statements()`: Извлечение return statements

## Что анализируется

Анализатор находит:

- **HTTP методы**: GET, POST, PUT, DELETE, PATCH
- **Пути endpoints**: `/get`, `/add`, `/update` и т.д.
- **Имена функций**: `get_groups`, `add_group` и т.д.
- **Return statements**: примеры возвращаемых данных с номерами строк
- **Предлагаемые схемы**: автоматические предложения с оценкой уверенности

## Генерируемые схемы

Анализатор предлагает базовые классы на основе содержимого return statements:

- `SuccessResponse` - для ответов с `success` и `message`
- `GroupsResponse` - для ответов с `groups`
- `UsersResponse` - для ответов с `users`
- `SuccessWithIdResponse` - для POST запросов с `id`
- `ErrorResponse` - для ответов с ошибками

Каждая схема включает:
- Оценку уверенности (0.0-1.0)
- Предлагаемые базовые классы
- Анализ паттернов return statements
- Сгенерированный код Python

## Конфигурация

Настройка поведения анализа через константы:

```python
from core.docs_generator.response_schema_analyzer.constants import ANALYSIS_CONFIG

# Изменение параметров анализа
ANALYSIS_CONFIG.MAX_RETURN_STATEMENTS = 5
ANALYSIS_CONFIG.MAX_LINE_LENGTH = 150
```

## Интеграция

Модуль интегрирован в систему docs_generator и следует тем же архитектурным паттернам, что и другие модули анализаторов. Обратная совместимость обеспечена через основной файл `response_schema_analyzer.py`.