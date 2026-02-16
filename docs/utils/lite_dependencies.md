# 🔐 Lite Dependencies

## Описание
Модуль с легковесными FastAPI dependencies для проверки прав доступа. Содержит функцию `role_require()` для контроля доступа к эндпоинтам на основе ролей пользователей и whitelist IP адресов.

## Функции

### 🛡️ `role_require()`
Фабрика dependency для проверки ролей пользователя.

**Сигнатура:**
```python
def role_require(*roles: str)
```

**Параметры:**
- `*roles` (str) - одна или несколько допустимых ролей

**Возвращает:**
- `async function` - dependency функция для FastAPI

**Использование:**
```python
from core.utils.lite_dependencies import role_require
from core.utils.anything import Roles

@router.post("/private/admin/users")
async def admin_endpoint(
    _: Annotated[None, Depends(role_require(Roles.methodist))]
):
    # Доступ только для methodist
    return {"message": "Admin action"}

@router.get("/private/data")
async def data_endpoint(
    _: Annotated[None, Depends(role_require(Roles.methodist, Roles.read_all))]
):
    # Доступ для methodist ИЛИ read_all
    return {"data": [...]}
```

## Бизнес-логика

### Проверка доступа

Функция выполняет две проверки:

1. **Whitelist IP адресов:**
   - Если IP в списке `env.allowed_ips`, доступ разрешён
   - Обходит проверку ролей
   - Используется для внутренних сервисов

2. **Проверка роли:**
   - Извлекается роль из `request.state.role`
   - Проверяется наличие в списке допустимых ролей
   - Если роль не подходит, возвращается 403 Forbidden

**Логика:**
```python
if ip not in env.allowed_ips and cur_role not in set(roles):
    raise HTTPException(status_code=403, detail="Недостаточно прав")
```

**Условие доступа:**
- IP в whitelist ИЛИ роль в списке допустимых

### Извлечение данных из request.state

Dependency ожидает, что в `request.state` установлены:
- `role` (str) - роль пользователя
- `client_ip` (str) - IP адрес клиента

Эти данные устанавливаются:
- JWT middleware (`JWTCookieDep`) - извлекает роль из токена
- Logging middleware (`ASGILoggingMiddleware`) - извлекает IP

### Роли в системе

Определены в `core.utils.anything.Roles`:
```python
@dataclass
class Roles:
    methodist: str = 'methodist'  # Методист (полный доступ)
    read_all: str = 'read_all'    # Только чтение
```

**Иерархия:**
- `methodist` - может читать и изменять данные
- `read_all` - может только читать данные

## Зависимости

### Внутренние модули
- `core.config_dir.config.env` - конфигурация с `allowed_ips`

### Внешние библиотеки
- `fastapi.HTTPException` - исключение для HTTP ошибок
- `starlette.requests.Request` - объект запроса

### Требования к request.state
- `request.state.role` - установлен JWT middleware
- `request.state.client_ip` - установлен logging middleware

## Примеры использования

### Одна роль
```python
from core.utils.lite_dependencies import role_require
from core.utils.anything import Roles

@router.post("/private/edit")
async def edit_data(
    _: Annotated[None, Depends(role_require(Roles.methodist))]
):
    # Только methodist может редактировать
    return {"success": True}
```

### Несколько ролей
```python
@router.get("/private/view")
async def view_data(
    _: Annotated[None, Depends(role_require(Roles.methodist, Roles.read_all))]
):
    # methodist ИЛИ read_all могут просматривать
    return {"data": [...]}
```

### Использование в роутере
```python
# Применить ко всем эндпоинтам роутера
router = APIRouter(
    prefix='/private/admin',
    dependencies=[Depends(role_require(Roles.methodist))]
)

@router.get("/users")
async def get_users():
    # Автоматически требует роль methodist
    return {"users": [...]}

@router.post("/users")
async def create_user():
    # Также требует роль methodist
    return {"success": True}
```

### Whitelist IP
```python
# В config.py
env.allowed_ips = ['127.0.0.1', '10.0.0.5']

# Запрос с IP 127.0.0.1
# Доступ разрешён независимо от роли
@router.post("/internal/sync")
async def internal_sync(
    _: Annotated[None, Depends(role_require(Roles.methodist))]
):
    # Доступ для whitelist IP без проверки роли
    return {"synced": True}
```

## Интеграция с другими модулями

### Связь с JWT middleware
Требует `request.state.role`:
```python
# В JWTCookieDep
payload = decode_jwt(token)
request.state.role = payload['role']
request.state.user_id = payload['user_id']
```

### Связь с logging middleware
Требует `request.state.client_ip`:
```python
# В ASGILoggingMiddleware
request.state.client_ip = get_client_ip(request)
```

### Связь с anything.py
Использует константы ролей:
```python
from core.utils.anything import Roles

role_require(Roles.methodist)
role_require(Roles.read_all)
```

### Использование в API модулях
Применяется во всех приватных эндпоинтах:
- `core/api/timetable_api.py`
- `core/api/groups_tab.py`
- `core/api/teachers_tab.py`
- `core/api/disciplines_tab.py`
- `core/api/ttable_versions/ttable_versions_tab.py`
- `core/api/elastic_search/api_elastic_search.py`
- И другие

## Типичные сценарии

1. **Методист редактирует расписание:**
   - JWT токен содержит `role: 'methodist'`
   - Middleware устанавливает `request.state.role = 'methodist'`
   - `role_require(Roles.methodist)` проверяет роль
   - Доступ разрешён

2. **Read-only пользователь просматривает данные:**
   - JWT токен содержит `role: 'read_all'`
   - Эндпоинт требует `role_require(Roles.methodist, Roles.read_all)`
   - Роль `read_all` в списке допустимых
   - Доступ разрешён

3. **Неавторизованный доступ:**
   - Пользователь без JWT токена
   - `request.state.role` не установлен
   - Dependency выбрасывает исключение
   - Возвращается 403 Forbidden

4. **Внутренний сервис:**
   - Запрос с IP `10.0.0.5` (в whitelist)
   - IP проверяется первым
   - Проверка роли пропускается
   - Доступ разрешён

## Безопасность

### Whitelist IP
**Преимущества:**
- Быстрый доступ для внутренних сервисов
- Упрощает интеграцию

**Риски:**
- IP spoofing (если не настроен правильно прокси)
- Необходимо доверять сети


### Проверка ролей
**Преимущества:**
- Гранулярный контроль доступа
- Разделение прав между пользователями
- Аудит через JWT токены

**Ограничения:**
- Только две роли (methodist, read_all)
- Нет иерархии ролей
- Нет permission-based контроля

## Обработка ошибок

### 403 Forbidden
**Причины:**
- Роль пользователя не в списке допустимых
- IP не в whitelist

**Ответ:**
```json
{
  "detail": "Недостаточно прав"
}
```

**Логирование:**
- Не логируется автоматически
- Можно добавить логирование в dependency

### Отсутствие request.state
**Признаки:**
- Если middleware не установил `role` или `client_ip`
- Dependency выбросит `AttributeError`

**Подсказка:**
- Убедиться, что middleware настроены правильно
- Добавить проверку наличия атрибутов


## Будущие улучшения

### 1. Расширение ролей
```python
@dataclass
class Roles:
    admin: str = 'admin'
    methodist: str = 'methodist'
    teacher: str = 'teacher'
    student: str = 'student'
    read_all: str = 'read_all'
```


### 2. Логирование отказов
```python
def role_require(*roles: str):
    async def checker(request: Request):
        cur_role = request.state.role
        ip = request.state.client_ip
        
        if ip not in env.allowed_ips and cur_role not in set(roles):
            log_event(
                f"Access denied: role={cur_role}, required={roles}",
                request=request,
                level='WARNING'
            )
            raise HTTPException(403, "Недостаточно прав")
    return checker
```

### 3. Иерархия ролей
```python
ROLE_HIERARCHY = {
    'admin': ['methodist', 'teacher', 'student', 'read_all'],
    'methodist': ['teacher', 'read_all'],
    'teacher': ['read_all'],
}

def has_role(user_role: str, required_roles: set) -> bool:
    if user_role in required_roles:
        return True
    # Проверка иерархии
    for role in ROLE_HIERARCHY.get(user_role, []):
        if role in required_roles:
            return True
    return False
```


## Связь с документацией

Модуль используется в:
- `docs/api/timetable_api.md` - проверка доступа к расписанию
- `docs/api/groups_tab.md` - проверка доступа к группам
- `docs/api/teachers_tab.md` - проверка доступа к преподавателям
- `docs/api/disciplines_tab.md` - проверка доступа к дисциплинам
- `docs/api/ttable_versions_ttable_versions_tab.md` - проверка доступа к версиям
- `docs/api/elastic_search_api_elastic_search.md` - проверка доступа к поиску
- `docs/utils/anything.md` - определение ролей
