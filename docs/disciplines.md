## Disciplines

Модуль управления дисциплинами (предметами). Предоставляет функциональность для создания, обновления и просмотра учебных дисциплин. Связывает дисциплины с преподавателями и специальностями. Используется для формирования учебных планов и расписания занятий.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/private/disciplines/get` | get_disciplines | ✓ |  |
| PUT | `/api/v1/private/disciplines/update` | update_disciplines | ✓ |  |
| POST | `/api/v1/private/disciplines/add` | add_discipline | ✓ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/private/disciplines/get` - 

**Данные на вход:**

```python
# TeachersPagenSchema
offset: int | None
limit: int | None
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.disciplines.get_all`
    - Function call: db.disciplines.get_all

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

8. **fastapi_dependency** - `TeachersPagenSchema`
    - FastAPI dependency: TeachersPagenSchema

9. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

10. **function** - `hasattr`
    - Function call: hasattr

11. **function** - `log_event`
    - Function call: log_event

12. **function** - `response.set_cookie`
    - Function call: response.set_cookie

13. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

14. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "disciplines": [
    {
      "id": 1,
      "is_active": true,
      "title": "Математика"
    },
    {
      "id": 2,
      "is_active": true,
      "title": "Физика"
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


### PUT `/api/v1/private/disciplines/update` - 

**Данные на вход:**

```python
# DisciplineUpdateSchema
set_as_active: Any | None
set_as_deprecated: Any | None
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.disciplines.switch_status`
    - Function call: db.disciplines.switch_status

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
  "message": "Дисциплины сменили статусы",
  "active_upd_count": 3,
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


### POST `/api/v1/private/disciplines/add` - 

**Данные на вход:**

```python
# DisciplineAddSchema
title: str
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.disciplines.add`
    - Function call: db.disciplines.add

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `create_disciplines_add_response`
    - Function call: create_disciplines_add_response

7. **function** - `create_response_json`
    - Function call: create_response_json

8. **function** - `log_event`
    - Function call: log_event

9. **function** - `create_disciplines_add_response`
    - Function call: create_disciplines_add_response

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
- `specialties`
- `teachers`
- `timetable`

### Data Schemas

- `DisciplineAddSchema`
- `DisciplineUpdateSchema`
- `DisciplinesGetResponse`
- `DisciplinesUpdateResponse`
- `TeachersPagenSchema`
