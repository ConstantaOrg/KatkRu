## Teachers {teachers}

Модуль управления преподавателями. Предоставляет функциональность для добавления, обновления и просмотра информации о преподавателях. Включает управление статусами преподавателей и предотвращение дублирования записей. Требует аутентификации и роли методиста для модификации данных.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| GET | `/api/v1/private/teachers/get` | get_teachers | ✓ |  |
| PUT | `/api/v1/private/teachers/update` | update_teachers | ✓ |  |
| POST | `/api/v1/private/teachers/add` | add_teacher | ✓ |  |

### Database Tables
- `disciplines`
- `teachers`

### Data Schemas
- `TeachersPagenSchema`
- `TeachersAddSchema`
- `TeachersAddResponse`
- `TeachersUpdateResponse`
- `TeachersUpdateSchema`
- `TeachersGetResponse`

### Usage Examples

#### Successful GET request to /api/v1/private/teachers/get
Example of a successful get request to the get_teachers endpoint.

**Request:**
```bash
curl -X GET -v -H "Authorization: Bearer YOUR_JWT_TOKEN" -d '{"pagen":1}' "https://api.example.com/api/v1/private/teachers/get"
```

**Response:**
```json
{
  "teachers": [
    {
      "created_at": "2024-01-01T00:00:00Z",
      "disciplines_count": 3,
      "fio": "Иванов Иван Иванович",
      "id": 1,
      "is_active": true
    },
    {
      "created_at": "2024-01-01T00:00:00Z",
      "disciplines_count": 2,
      "fio": "Петрова Анна Сергеевна",
      "id": 2,
      "is_active": true
    }
  ]
}
```

#### Authentication Error - GET /api/v1/private/teachers/get
Example of an authentication error when no valid JWT token is provided.

**Request:**
```bash
curl -X GET -v -d '{"pagen":1}' "https://api.example.com/api/v1/private/teachers/get"
```

**Response:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

#### Validation Error - GET /api/v1/private/teachers/get
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X GET -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/private/teachers/get"
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
