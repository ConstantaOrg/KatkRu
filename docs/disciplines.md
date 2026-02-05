## Disciplines {disciplines}

Модуль управления дисциплинами (предметами). Предоставляет функциональность для создания, обновления и просмотра учебных дисциплин. Связывает дисциплины с преподавателями и специальностями. Используется для формирования учебных планов и расписания занятий.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| GET | `/api/v1/private/disciplines/get` | get_disciplines | ✓ |  |
| PUT | `/api/v1/private/disciplines/update` | update_disciplines | ✓ |  |
| POST | `/api/v1/private/disciplines/add` | add_discipline | ✓ |  |

### Database Tables

- `disciplines`
- `specialties`
- `teachers`
- `timetable`

### Data Schemas

- `DisciplineAddSchema`
- `DisciplinesUpdateResponse`
- `TeachersPagenSchema`
- `DisciplineUpdateSchema`
- `DisciplinesGetResponse`

### Usage Examples

#### Successful GET request to /api/v1/private/disciplines/get
Example of a successful get request to the get_disciplines endpoint.

**Request:**
```bash
curl -X GET -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/private/disciplines/get"
```

**Response:**
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

#### Authentication Error - GET /api/v1/private/disciplines/get
Example of an authentication error when no valid JWT token is provided.

**Request:**
```bash
curl -X GET -v "https://api.example.com/api/v1/private/disciplines/get"
```

**Response:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

#### Successful PUT request to /api/v1/private/disciplines/update
Example of a successful put request to the update_disciplines endpoint.

**Request:**
```bash
curl -X PUT -v -H "Authorization: Bearer YOUR_JWT_TOKEN" -H "Content-Type: application/json" -d '{"set_as_active":"example_string","set_as_deprecated":"example_string"}' "https://api.example.com/api/v1/private/disciplines/update"
```

**Response:**
```json
{
  "success": true,
  "message": "Дисциплины сменили статусы",
  "active_upd_count": 3,
  "depr_upd_count": 1
}
```

---
