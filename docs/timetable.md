## Timetable {timetable}

Модуль управления расписанием занятий. Центральный модуль системы, объединяющий группы, преподавателей и дисциплины в единое расписание. Предоставляет функциональность для создания, обновления и просмотра расписания. Поддерживает версионирование расписания и различные форматы вывода.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| POST | `/api/v1/private/timetable/standard/import` | upload_ttable_file | ✓ | Будет полноценный файл-лоадер. Пока для алгоритма ... |
| POST | `/api/v1/public/timetable/get` | get_ttable_doc | ✗ |  |
| PUT | `/api/v1/private/ttable/versions/pre-commit` | accept_ttable_version | ✓ |  |
| PUT | `/api/v1/private/ttable/versions/commit` | accept_ttable_version | ✓ |  |

### Database Tables
- `disciplines`
- `groups`
- `teachers`
- `timetable`
- `ttable_versions`

### Data Schemas
- `TimetableGetResponse`
- `TtableVersionsCommitResponse`
- `TtableVersionsPreCommitResponse`
- `PreAcceptTimetableSchema`
- `ScheduleFilterSchema`
- `TimetableImportResponse`
- `CommitTtableVersionSchema`

### Usage Examples

#### Successful POST request to /api/v1/private/timetable/standard/import
Example of a successful post request to the upload_ttable_file endpoint.

**Request:**
```bash
curl -X POST -v -H "Authorization: Bearer YOUR_JWT_TOKEN" -H "Content-Type: application/json" -d '{"file_obj":"example_value"}' "https://api.example.com/api/v1/private/timetable/standard/import?smtr=example_value&bid=123"
```

**Response:**
```json
{
  "success": true,
  "message": "Расписание сохранено",
  "ttable_ver_id": 123,
  "status": "В Ожидании"
}
```

#### Authentication Error - POST /api/v1/private/timetable/standard/import
Example of an authentication error when no valid JWT token is provided.

**Request:**
```bash
curl -X POST -v -H "Content-Type: application/json" -d '{"file_obj":"example_value"}' "https://api.example.com/api/v1/private/timetable/standard/import?smtr=example_value&bid=123"
```

**Response:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

#### Validation Error - POST /api/v1/private/timetable/standard/import
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X POST -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/private/timetable/standard/import"
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
