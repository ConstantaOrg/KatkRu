## N8N Ui {n8n-ui}

Модуль интеграции с N8N для автоматизации рабочих процессов. Предоставляет специализированные API endpoints для интеграции с внешними системами автоматизации. Включает адаптированные схемы данных и форматы ответов для совместимости с N8N workflows. Обеспечивает мост между системой управления расписанием и внешними инструментами автоматизации.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| POST | `/api/v1/private/n8n_ui/ttable/create` | create_ttable | ✓ |  |
| POST | `/api/v1/private/n8n_ui/std_ttable/get_all` | get_std_ttable2cards | ✓ |  |
| POST | `/api/v1/private/n8n_ui/std_ttable/check_exists` | check_actuality_of_layout | ✓ |  |
| POST | `/api/v1/private/n8n_ui/current_ttable/get_all` | get_std_ttable2cards | ✓ |  |
| POST | `/api/v1/private/n8n_ui/cards/get_by_id` | create_ttable | ✓ |  |
| POST | `/api/v1/private/n8n_ui/cards/save` | save_card | ✓ |  |
| GET | `/api/v1/private/n8n_ui/cards/history` | get_cards_history | ✓ |  |
| GET | `/api/v1/private/n8n_ui/cards/content` | get_card_content | ✓ |  |
| PUT | `/api/v1/private/n8n_ui/cards/accept` | switch_card_status | ✓ |  |

### Database Tables

- `disciplines`
- `groups`
- `specialties`
- `teachers`

### Data Schemas

- `StdTtableSchema`
- `StdTtableCheckExistsResponse`
- `CreateTtableSchema`
- `SaveCardSchema`
- `CardsContentResponse`
- `CardsGetByIdResponse`
- `ExtCardStateSchema`
- `CardsHistoryResponse`
- `CardsAcceptResponse`
- `SnapshotTtableSchema`
- `StdTtableLoadSchema`
- `CurrentTtableGetAllResponse`
- `StdTtableGetAllResponse`
- `TtableCreateResponse`

### Usage Examples

#### Successful POST request to /api/v1/private/n8n_ui/ttable/create
Example of a successful post request to the create_ttable endpoint.

**Request:**
```bash
curl -X POST -v -H "Authorization: Bearer YOUR_JWT_TOKEN" -H "Content-Type: application/json" -d '{"building_id":123,"date":"example_string","type":"example_string"}' "https://api.example.com/api/v1/private/n8n_ui/ttable/create"
```

**Response:**
```json
{
  "success": true,
  "message": "Версия расписания создана",
  "ttable_id": 42
}
```

#### Authentication Error - POST /api/v1/private/n8n_ui/ttable/create
Example of an authentication error when no valid JWT token is provided.

**Request:**
```bash
curl -X POST -v -H "Content-Type: application/json" -d '{"building_id":123,"date":"example_string","type":"example_string"}' "https://api.example.com/api/v1/private/n8n_ui/ttable/create"
```

**Response:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

#### Validation Error - POST /api/v1/private/n8n_ui/ttable/create
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X POST -v -H "Authorization: Bearer YOUR_JWT_TOKEN" "https://api.example.com/api/v1/private/n8n_ui/ttable/create"
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
