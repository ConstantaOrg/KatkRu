## Users

Модуль управления пользователями системы. Предоставляет функциональность для аутентификации, авторизации и управления пользователями. Включает систему ролей (методист, администратор, только чтение) и JWT токены. Обеспечивает безопасность доступа к функциям системы.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/server/users/sign_up` | registration_user | ✓ | Регистрация |
| POST | `/api/v1/public/users/login` | log_in | ✗ | Вход в аккаунт |
| PUT | `/api/v1/private/users/logout` | log_out | ✓ |  |
| POST | `/api/v1/private/users/seances` | show_seances | ✓ | Все Устройства аккаунта |
| PUT | `/api/v1/server/users/passw/set_new_passw` | reset_password | ✓ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/server/users/sign_up` - Регистрация

**Данные на вход:**

```python
# UserRegSchema
passw: str
email: str
name: str
```

**Процесс выполнения:**

1. **Работа с БД** - `db.users.reg_user`
    - Function call: db.users.reg_user

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `log_event`
    - Function call: log_event

5. **function** - `hide_log_param`
    - Function call: hide_log_param

6. **function** - `create_user_registration_response`
    - Function call: create_user_registration_response

7. **function** - `create_response_json`
    - Function call: create_response_json

8. **function** - `log_event`
    - Function call: log_event

9. **function** - `hide_log_param`
    - Function call: hide_log_param

10. **function** - `create_user_registration_response`
    - Function call: create_user_registration_response

11. **function** - `create_response_json`
    - Function call: create_response_json

12. **function** - `router.post`
    - Function call: router.post

**Возможные ответы:**

**Ошибка авторизации (401):**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

---


### POST `/api/v1/public/users/login` - Вход в аккаунт

**Данные на вход:**

```python
# UserLogInSchema
email: str
passw: str
```

**Процесс выполнения:**

1. **Работа с БД** - `db.users.select_user`
    - Function call: db.users.select_user

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `encryption.verify`
    - Function call: encryption.verify

5. **function** - `TokenPayloadSchema`
    - Function call: TokenPayloadSchema

6. **function** - `request.headers.get`
    - Function call: request.headers.get

7. **function** - `issue_aT_rT`
    - Function call: issue_aT_rT

8. **function** - `log_event`
    - Function call: log_event

9. **function** - `create_user_login_response`
    - Function call: create_user_login_response

10. **function** - `create_response_json`
    - Function call: create_response_json

11. **function** - `json_response.set_cookie`
    - Function call: json_response.set_cookie

12. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

13. **function** - `AccToken`
    - Function call: AccToken

14. **function** - `json_response.set_cookie`
    - Function call: json_response.set_cookie

15. **function** - `unknown.model_dump`
    - Function call: unknown.model_dump

16. **function** - `RtToken`
    - Function call: RtToken

17. **function** - `log_event`
    - Function call: log_event

18. **function** - `hide_log_param`
    - Function call: hide_log_param

19. **function** - `create_user_login_response`
    - Function call: create_user_login_response

20. **function** - `create_response_json`
    - Function call: create_response_json

21. **function** - `router.post`
    - Function call: router.post

22. **function** - `rate_limit`
    - Function call: rate_limit

**Возможные ответы:**

---


### PUT `/api/v1/private/users/logout` - 

**Процесс выполнения:**

1. **Проверка авторизации** - `db.auth.session_termination`
    - Function call: db.auth.session_termination

2. **Работа с БД** - `db.auth.session_termination`
    - Function call: db.auth.session_termination

3. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

4. **Работа с БД** - `PgSql`
    - Function call: PgSql

5. **database** - `response.delete_cookie`
    - Function call: response.delete_cookie

6. **database** - `response.delete_cookie`
    - Function call: response.delete_cookie

7. **function** - `log_event`
    - Function call: log_event

8. **function** - `router.put`
    - Function call: router.put

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

**Ошибка авторизации (401):**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

---


### POST `/api/v1/private/users/seances` - Все Устройства аккаунта

**Процесс выполнения:**

1. **Проверка авторизации** - `db.auth.all_seances_user`
    - Function call: db.auth.all_seances_user

2. **Работа с БД** - `db.auth.all_seances_user`
    - Function call: db.auth.all_seances_user

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

**Ошибка авторизации (401):**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

---


### PUT `/api/v1/server/users/passw/set_new_passw` - 

**Данные на вход:**

```python
# UpdatePasswSchema
passw: str
reset_token: str
```

**Процесс выполнения:**

1. **Работа с БД** - `db.users.set_new_passw`
    - Function call: db.users.set_new_passw

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `encryption.hash`
    - Function call: encryption.hash

5. **function** - `log_event`
    - Function call: log_event

6. **function** - `router.put`
    - Function call: router.put

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

- `roles`
- `user_sessions`
- `users`

### Data Schemas

- `UpdatePasswSchema`
- `UserLogInSchema`
- `UserRegSchema`
