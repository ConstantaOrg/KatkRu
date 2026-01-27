## Users {users}

Модуль управления пользователями системы. Предоставляет функциональность для аутентификации, авторизации и управления пользователями. Включает систему ролей (методист, администратор, только чтение) и JWT токены. Обеспечивает безопасность доступа к функциям системы.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| POST | `/api/v1/server/users/sign_up` | registration_user | ✓ | Регистрация |
| POST | `/api/v1/public/users/login` | log_in | ✗ | Вход в аккаунт |
| PUT | `/api/v1/private/users/logout` | log_out | ✓ |  |
| POST | `/api/v1/private/users/seances` | show_seances | ✓ | Все Устройства аккаунта |
| PUT | `/api/v1/server/users/passw/set_new_passw` | reset_password | ✓ |  |
| PUT | `/api/v1/private/users/any` | any_users | ✓ |  |

### Database Tables
- `roles`
- `user_sessions`
- `users`

### Data Schemas
- `UpdatePasswSchema`
- `UserRegSchema`
- `UserLogInSchema`

### Usage Examples

#### Successful POST request to /api/v1/server/users/sign_up
Example of a successful post request to the registration_user endpoint.

**Request:**
```bash
curl -X POST -v -H "Authorization: Bearer YOUR_JWT_TOKEN" -H "Content-Type: application/json" -d '{"passw":"example_string","email":"user@example.com","name":"Example Name"}' "https://api.example.com/api/v1/server/users/sign_up"
```

**Response:**
```json
{
  "id": 123,
  "message": "Resource created successfully",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Authentication Error - POST /api/v1/server/users/sign_up
Example of an authentication error when no valid JWT token is provided.

**Request:**
```bash
curl -X POST -v -H "Content-Type: application/json" -d '{"passw":"example_string","email":"user@example.com","name":"Example Name"}' "https://api.example.com/api/v1/server/users/sign_up"
```

**Response:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

#### Validation Error - POST /api/v1/server/users/sign_up
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X POST -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/server/users/sign_up"
```

**Response:**
```json
{
  "error": "Validation Error",
  "message": "Required parameters missing",
  "details": [
    {
      "field": "required_field",
      "message": "This field is required"
    }
  ]
}
```

---
