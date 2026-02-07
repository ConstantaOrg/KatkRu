## Timetable

Модуль управления расписанием занятий. Центральный модуль системы, объединяющий группы, преподавателей и дисциплины в единое расписание. Предоставляет функциональность для создания, обновления и просмотра расписания. Поддерживает версионирование расписания и различные форматы вывода.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/private/timetable/standard/import` | upload_ttable_file | ✓ | Будет полноценный файл-лоадер. Пока для алгоритма ... |
| POST | `/api/v1/public/timetable/get` | get_ttable_doc | ✗ |  |
| PUT | `/api/v1/private/ttable/versions/pre-commit` | accept_ttable_version | ✓ |  |
| PUT | `/api/v1/private/ttable/versions/commit` | accept_ttable_version | ✓ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/private/timetable/standard/import` - Будет полноценный файл-лоадер

**Данные на вход:**

**Параметры:**
- `smtr` (Literal, обязательный)
- `bid` (int, обязательный)

**Процесс выполнения:**

1. **Работа с БД** - `db.ttable.import_raw_std_ttable`
    - Function call: db.ttable.import_raw_std_ttable

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `Query`
    - Function call: Query

5. **function** - `Query`
    - Function call: Query

6. **function** - `log_event`
    - Function call: log_event

7. **function** - `std_ttable_doc_processer`
    - Function call: std_ttable_doc_processer

8. **function** - `int`
    - Function call: int

9. **function** - `log_event`
    - Function call: log_event

10. **function** - `router.post`
    - Function call: router.post

11. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

12. **function** - `hasattr`
    - Function call: hasattr

13. **function** - `log_event`
    - Function call: log_event

14. **function** - `response.set_cookie`
    - Function call: response.set_cookie

15. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

16. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Расписание сохранено",
  "ttable_ver_id": 123,
  "status": "В Ожидании"
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


### POST `/api/v1/public/timetable/get` - 

**Данные на вход:**

```python
# ScheduleFilterSchema
group: Any | None
date: str | None
```

**Процесс выполнения:**

1. **Работа с БД** - `db.ttable.get_ttable`
    - Function call: db.ttable.get_ttable

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `dict`
    - Function call: dict

5. **function** - `router.post`
    - Function call: router.post

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "schedule": [
    {
      "aud": "101",
      "fio": "Иванов И.И.",
      "position": 1,
      "title": "Математика"
    },
    {
      "aud": "205",
      "fio": "Петрова А.С.",
      "position": 2,
      "title": "Физика"
    }
  ]
}
```

---


### PUT `/api/v1/private/ttable/versions/pre-commit` - 

**Данные на вход:**

```python
# PreAcceptTimetableSchema
ttable_id: int
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.ttable.check_accept_constraints`
    - Function call: db.ttable.check_accept_constraints

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `create_ttable_precommit_response`
    - Function call: create_ttable_precommit_response

6. **function** - `create_response_json`
    - Function call: create_response_json

7. **function** - `create_ttable_precommit_response`
    - Function call: create_ttable_precommit_response

8. **function** - `error_data.get`
    - Function call: error_data.get

9. **function** - `error_data.get`
    - Function call: error_data.get

10. **function** - `error_data.get`
    - Function call: error_data.get

11. **function** - `error_data.get`
    - Function call: error_data.get

12. **function** - `error_data.get`
    - Function call: error_data.get

13. **function** - `create_response_json`
    - Function call: create_response_json

14. **function** - `router.put`
    - Function call: router.put

15. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

16. **function** - `hasattr`
    - Function call: hasattr

17. **function** - `log_event`
    - Function call: log_event

18. **function** - `response.set_cookie`
    - Function call: response.set_cookie

19. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

20. **function** - `AccToken`
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


### PUT `/api/v1/private/ttable/versions/commit` - 

**Данные на вход:**

```python
# CommitTtableVersionSchema
pending_ver_id: int
target_ver_id: int
```

**Процесс выполнения:**

1. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

2. **Работа с БД** - `PgSql`
    - Function call: PgSql

3. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

4. **function** - `hasattr`
    - Function call: hasattr

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `response.set_cookie`
    - Function call: response.set_cookie

7. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

8. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Версии переключены!"
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


### Database Tables

- `disciplines`
- `groups`
- `teachers`
- `timetable`
- `ttable_versions`

### Data Schemas

- `CommitTtableVersionSchema`
- `PreAcceptTimetableSchema`
- `ScheduleFilterSchema`
- `TimetableGetResponse`
- `TimetableImportResponse`
- `TtableVersionsCommitResponse`
