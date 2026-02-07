## Teachers

Модуль управления преподавателями. Предоставляет функциональность для добавления, обновления и просмотра информации о преподавателях. Включает управление статусами преподавателей и предотвращение дублирования записей. Требует аутентификации и роли методиста для модификации данных.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/private/teachers/get` | get_teachers | ✓ |  |
| PUT | `/api/v1/private/teachers/update` | update_teachers | ✓ |  |
| POST | `/api/v1/private/teachers/add` | add_teacher | ✓ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/private/teachers/get` - 

**Данные на вход:**

```python
# TeachersPagenSchema
offset: int | None
limit: int | None
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.teachers.get_all`
    - Function call: db.teachers.get_all

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `dict`
    - Function call: dict

7. **function** - `router.post`
    - Function call: router.post

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
  "teachers": [
    {
      "fio": "Иванов Иван Иванович",
      "id": 1,
      "is_active": true
    },
    {
      "fio": "Петрова Анна Сергеевна",
      "id": 2,
      "is_active": true
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


### PUT `/api/v1/private/teachers/update` - 

**Данные на вход:**

```python
# TeachersUpdateSchema
set_as_active: Any | None
set_as_deprecated: Any | None
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.teachers.switch_status`
    - Function call: db.teachers.switch_status

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
  "message": "Учителя сменили статусы",
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


### POST `/api/v1/private/teachers/add` - 

**Данные на вход:**

```python
# TeachersAddSchema
fio: str
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.teachers.add`
    - Function call: db.teachers.add

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `create_teachers_add_response`
    - Function call: create_teachers_add_response

7. **function** - `create_response_json`
    - Function call: create_response_json

8. **function** - `log_event`
    - Function call: log_event

9. **function** - `create_teachers_add_response`
    - Function call: create_teachers_add_response

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

- `disciplines`
- `teachers`

### Data Schemas

- `TeachersAddSchema`
- `TeachersGetResponse`
- `TeachersPagenSchema`
- `TeachersUpdateResponse`
- `TeachersUpdateSchema`
