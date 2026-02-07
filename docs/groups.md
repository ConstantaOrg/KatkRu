## Groups

Модуль управления учебными группами. Предоставляет функциональность для создания, обновления и просмотра учебных групп. Включает управление статусами групп (активные/устаревшие) и привязку к зданиям. Требует аутентификации и роли методиста для модификации данных.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/private/groups/get` | get_groups | ✓ |  |
| PUT | `/api/v1/private/groups/update` | update_groups | ✓ |  |
| POST | `/api/v1/private/groups/add` | add_group | ✓ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/private/groups/get` - 

**Данные на вход:**

```python
# GroupPagenSchema
offset: int | None
limit: int | None
```

**Параметры:**
- `bid` (int, обязательный)

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.groups.get_all`
    - Function call: db.groups.get_all

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `Query`
    - Function call: Query

6. **function** - `log_event`
    - Function call: log_event

7. **function** - `dict`
    - Function call: dict

8. **function** - `router.post`
    - Function call: router.post

9. **fastapi_dependency** - `GroupPagenSchema`
    - FastAPI dependency: GroupPagenSchema

10. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

11. **function** - `hasattr`
    - Function call: hasattr

12. **function** - `log_event`
    - Function call: log_event

13. **function** - `response.set_cookie`
    - Function call: response.set_cookie

14. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

15. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "groups": [
    {
      "id": 1,
      "is_active": true,
      "name": "ИС-21-1"
    },
    {
      "id": 2,
      "is_active": true,
      "name": "ИС-21-2"
    }
  ]
}
```

**Ошибка авторизации (401):**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

---


### PUT `/api/v1/private/groups/update` - 

**Данные на вход:**

```python
# GroupUpdateSchema
set_as_active: Any | None
set_as_deprecated: Any | None
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.groups.switch_status`
    - Function call: db.groups.switch_status

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `body.model_dump`
    - Function call: body.model_dump

7. **function** - `router.put`
    - Function call: router.put

8. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

9. **function** - `hasattr`
    - Function call: hasattr

10. **function** - `log_event`
    - Function call: log_event

11. **function** - `response.set_cookie`
    - Function call: response.set_cookie

12. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

13. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Группы сменили статусы",
  "active_upd_count": 2,
  "depr_upd_count": 1
}
```

**Ошибка авторизации (401):**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

---


### POST `/api/v1/private/groups/add` - 

**Данные на вход:**

```python
# GroupAddSchema
group_name: str
building_id: int
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.groups.add`
    - Function call: db.groups.add

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `create_groups_add_response`
    - Function call: create_groups_add_response

7. **function** - `create_response_json`
    - Function call: create_response_json

8. **function** - `log_event`
    - Function call: log_event

9. **function** - `create_groups_add_response`
    - Function call: create_groups_add_response

10. **function** - `create_response_json`
    - Function call: create_response_json

11. **function** - `router.post`
    - Function call: router.post

12. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

13. **function** - `hasattr`
    - Function call: hasattr

14. **function** - `log_event`
    - Function call: log_event

15. **function** - `response.set_cookie`
    - Function call: response.set_cookie

16. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

17. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Ошибка авторизации (401):**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

---


### Database Tables

- `buildings`
- `groups`
- `specialties`

### Data Schemas

- `GroupAddSchema`
- `GroupPagenSchema`
- `GroupUpdateSchema`
- `GroupsGetResponse`
- `GroupsUpdateResponse`
