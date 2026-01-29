## Specialties {specialties}

Модуль управления специальностями учебного заведения. Предоставляет функциональность для просмотра списка специальностей и получения детальной информации о конкретной специальности. Используется для организации учебного процесса и группировки студентов по направлениям обучения.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| POST | `/api/v1/public/specialties/all` | specialties_all | ✗ |  |
| GET | `/api/v1/public/specialties/{spec_id}` | specialties_get | ✗ |  |

### Database Tables

- `groups`
- `specialties`

### Data Schemas

- `SpecialtiesAllResponse`
- `SpecsPaginSchema`
- `SpecialtyGetResponse`

### Usage Examples

#### Successful POST request to /api/v1/public/specialties/all
Example of a successful post request to the specialties_all endpoint.

**Request:**
```bash
curl -X POST -v -H "Content-Type: application/json" -d '{"offset":42,"limit":42}' "https://api.example.com/api/v1/public/specialties/all"
```

**Response:**
```json
{
  "total": "example_string",
  "specialties": [
    {
      "code": "09.02.07",
      "description": "Описание специальности",
      "id": 1,
      "name": "Информационные системы и программирование"
    }
  ]
}
```

#### Validation Error - POST /api/v1/public/specialties/all
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X POST -v "https://api.example.com/api/v1/public/specialties/all"
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

#### Successful GET request to /api/v1/public/specialties/{spec_id}
Example of a successful get request to the specialties_get endpoint.

**Request:**
```bash
curl -X GET -v "https://api.example.com/api/v1/public/specialties/123"
```

**Response:**
```json
{
  "speciality": {
    "code": "09.02.07",
    "description": "Подготовка специалистов в области разработки ПО",
    "duration_years": 3,
    "id": 1,
    "name": "Информационные системы и программирование",
    "qualification": "Программист"
  }
}
```

---
