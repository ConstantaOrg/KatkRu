## Groups {groups}

Модуль управления учебными группами. Предоставляет функциональность для создания, обновления и просмотра учебных групп. Включает управление статусами групп (активные/устаревшие) и привязку к зданиям. Требует аутентификации и роли методиста для модификации данных.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| GET | `/api/v1/private/groups/get` | get_groups | ✓ |  |
| PUT | `/api/v1/private/groups/update` | update_groups | ✓ |  |
| POST | `/api/v1/private/groups/add` | add_group | ✓ |  |

### Database Tables

- `buildings`
- `groups`
- `specialties`

### Data Schemas

- `GroupsUpdateResponse`
- `GroupAddSchema`
- `GroupsGetResponse`
- `GroupUpdateSchema`
- `GroupPagenSchema`

### Usage Examples

#### Successful GET request to /api/v1/private/groups/get
Example of a successful get request to the get_groups endpoint.

**Request:**
```bash
curl -X GET -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/private/groups/get?bid=123"
```

**Response:**
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

#### Authentication Error - GET /api/v1/private/groups/get
Example of an authentication error when no valid JWT token is provided.

**Request:**
```bash
curl -X GET -v "https://api.example.com/api/v1/private/groups/get?bid=123"
```

**Response:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

#### Validation Error - GET /api/v1/private/groups/get
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X GET -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/private/groups/get"
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
