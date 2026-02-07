## N8N_Ui

Модуль интеграции с N8N для автоматизации рабочих процессов. Предоставляет специализированные API endpoints для интеграции с внешними системами автоматизации. Включает адаптированные схемы данных и форматы ответов для совместимости с N8N workflows. Обеспечивает мост между системой управления расписанием и внешними инструментами автоматизации.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/private/n8n_ui/ttable/create` | create_ttable | ✓ |  |
| POST | `/api/v1/private/n8n_ui/std_ttable/get_all` | get_std_ttable2cards | ✓ |  |
| POST | `/api/v1/private/n8n_ui/std_ttable/check_exists` | check_actuality_of_layout | ✓ |  |
| POST | `/api/v1/private/n8n_ui/current_ttable/get_all` | get_std_ttable2cards | ✓ |  |
| POST | `/api/v1/private/n8n_ui/cards/get_by_id` | create_ttable | ✓ |  |
| POST | `/api/v1/private/n8n_ui/cards/save` | save_card | ✓ |  |
| GET | `/api/v1/private/n8n_ui/cards/history` | get_cards_history | ✓ |  |
| GET | `/api/v1/private/n8n_ui/cards/content` | get_card_content | ✓ |  |
| PUT | `/api/v1/private/n8n_ui/cards/accept` | switch_card_status | ✓ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/private/n8n_ui/ttable/create` - 

    🏗️ Создает новую версию расписания в статусе 'pending'.
    💡 После создания версии используйте другие эндпоинты для добавления карточек.

**Данные на вход:**

```python
# CreateTtableSchema
building_id: int
date: Any
type: str
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.ttable.create`
    - Function call: db.ttable.create

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `router.post`
    - Function call: router.post

7. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

8. **function** - `hasattr`
    - Function call: hasattr

9. **function** - `log_event`
    - Function call: log_event

10. **function** - `response.set_cookie`
    - Function call: response.set_cookie

11. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

12. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Версия расписания создана",
  "ttable_id": 42
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


### POST `/api/v1/private/n8n_ui/std_ttable/get_all` - 

**Данные на вход:**

```python
# StdTtableLoadSchema
building_id: int
ttable_id: int
week_day: int
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.n8n_ui.load_std_lessons_as_current`
    - Function call: db.n8n_ui.load_std_lessons_as_current

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
  "lessons": [
    {
      "card_hist_id": 2,
      "id": 1,
      "is_force": false,
      "name": "ИС-21-1",
      "position": 1,
      "status_card": 3,
      "title": "Математика"
    },
    {
      "card_hist_id": 3,
      "id": 2,
      "is_force": false,
      "name": "ИС-21-1",
      "position": 2,
      "status_card": 3,
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


### POST `/api/v1/private/n8n_ui/std_ttable/check_exists` - 

    🔍 Этот эндпоинт выполняет сложную проверку актуальности данных. Время выполнения может достигать 5-10 секунд.
    📊 Результат содержит детальную информацию о различиях в группах, преподавателях и дисциплинах.

**Данные на вход:**

```python
# StdTtableSchema
building_id: int
ttable_id: int
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.n8n_ui.check_loaded_std_pairs`
    - Function call: db.n8n_ui.check_loaded_std_pairs

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `len`
    - Function call: len

7. **function** - `len`
    - Function call: len

8. **function** - `len`
    - Function call: len

9. **function** - `router.post`
    - Function call: router.post

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
  "diff_groups": [
    {
      "name": "ИС-21-1"
    },
    {
      "name": "ПР-21-1"
    }
  ],
  "diff_teachers": [
    {
      "fio": "Иванов И.И."
    },
    {
      "fio": "Петрова А.С."
    }
  ],
  "diff_disciplines": [
    {
      "title": "Математика"
    },
    {
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


### POST `/api/v1/private/n8n_ui/current_ttable/get_all` - 

**Данные на вход:**

```python
# SnapshotTtableSchema
ttable_id: int
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
  "lessons": [
    {
      "auditorium": "101",
      "discipline_id": 5,
      "discipline_name": "Математика",
      "group_id": 2,
      "group_name": "ИС-21-1",
      "id": 10,
      "is_force": true,
      "position": 1,
      "teacher_id": 3,
      "teacher_name": "Иванов И.И."
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


### POST `/api/v1/private/n8n_ui/cards/get_by_id` - 

**Данные на вход:**

```python
# ExtCardStateSchema
card_hist_id: int
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
  "ext_card": [
    {
      "aud": "101",
      "position": 1,
      "teacher_id": 1,
      "teacher_name": "Иванов И.И."
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


### POST `/api/v1/private/n8n_ui/cards/save` - 

    ⚠️ Этот эндпоинт может возвращать конфликты при сохранении. Обязательно обрабатывайте ответы с success: false.
    💡 При конфликтах рекомендуется показать пользователю альтернативные варианты времени или преподавателей.

**Данные на вход:**

```python
# SaveCardSchema
card_hist_id: int
ttable_id: int
lessons: list
```

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.n8n_ui.save_card`
    - Function call: db.n8n_ui.save_card

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `isinstance`
    - Function call: isinstance

6. **function** - `log_event`
    - Function call: log_event

7. **function** - `create_cards_save_response`
    - Function call: create_cards_save_response

8. **function** - `create_response_json`
    - Function call: create_response_json

9. **function** - `log_event`
    - Function call: log_event

10. **function** - `create_cards_save_response`
    - Function call: create_cards_save_response

11. **function** - `create_response_json`
    - Function call: create_response_json

12. **function** - `router.post`
    - Function call: router.post

13. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

14. **function** - `hasattr`
    - Function call: hasattr

15. **function** - `log_event`
    - Function call: log_event

16. **function** - `response.set_cookie`
    - Function call: response.set_cookie

17. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

18. **function** - `AccToken`
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


### GET `/api/v1/private/n8n_ui/cards/history` - 

**Данные на вход:**

**Параметры:**
- `sched_ver_id` (int, обязательный)
- `group_id` (int, обязательный)

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.n8n_ui.get_cards_history`
    - Function call: db.n8n_ui.get_cards_history

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `Query`
    - Function call: Query

6. **function** - `Query`
    - Function call: Query

7. **function** - `log_event`
    - Function call: log_event

8. **function** - `len`
    - Function call: len

9. **function** - `dict`
    - Function call: dict

10. **function** - `router.get`
    - Function call: router.get

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
  "history": [
    {
      "card_hist_id": 100,
      "created_at": "2024-01-15T10:30:00Z",
      "is_current": true,
      "status_id": 2,
      "user_id": 1,
      "user_name": "Иванов И.И."
    },
    {
      "card_hist_id": 99,
      "created_at": "2024-01-14T15:20:00Z",
      "is_current": false,
      "status_id": 1,
      "user_id": 2,
      "user_name": "Петрова А.С."
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


### GET `/api/v1/private/n8n_ui/cards/content` - 

**Данные на вход:**

**Параметры:**
- `card_hist_id` (int, обязательный)

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.n8n_ui.get_card_content`
    - Function call: db.n8n_ui.get_card_content

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `Query`
    - Function call: Query

6. **function** - `log_event`
    - Function call: log_event

7. **function** - `len`
    - Function call: len

8. **function** - `dict`
    - Function call: dict

9. **function** - `router.get`
    - Function call: router.get

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
  "card_content": [
    {
      "aud": "101",
      "discipline_id": 1,
      "discipline_title": "Математика",
      "position": 1,
      "teacher_id": 1,
      "teacher_name": "Иванов И.И."
    },
    {
      "aud": "205",
      "discipline_id": 2,
      "discipline_title": "Физика",
      "position": 2,
      "teacher_id": 2,
      "teacher_name": "Петрова А.С."
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


### PUT `/api/v1/private/n8n_ui/cards/accept` - 

**Данные на вход:**

**Процесс выполнения:**

1. **Проверка авторизации** - `role_require`
    - Function call: role_require

2. **Работа с БД** - `db.n8n_ui.accept_card`
    - Function call: db.n8n_ui.accept_card

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **function** - `Body`
    - Function call: Body

6. **function** - `router.put`
    - Function call: router.put

7. **fastapi_dependency** - `check_at_factor`
    - FastAPI dependency: check_at_factor

8. **function** - `hasattr`
    - Function call: hasattr

9. **function** - `log_event`
    - Function call: log_event

10. **function** - `response.set_cookie`
    - Function call: response.set_cookie

11. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

12. **function** - `AccToken`
    - Function call: AccToken

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Карточка утверждена!"
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
- `specialties`
- `teachers`

### Data Schemas

- `CardsAcceptResponse`
- `CardsContentResponse`
- `CardsGetByIdResponse`
- `CardsHistoryResponse`
- `CreateTtableSchema`
- `CurrentTtableGetAllResponse`
- `ExtCardStateSchema`
- `SaveCardSchema`
- `SnapshotTtableSchema`
- `StdTtableCheckExistsResponse`
- `StdTtableGetAllResponse`
- `StdTtableLoadSchema`
- `StdTtableSchema`
- `TtableCreateResponse`
