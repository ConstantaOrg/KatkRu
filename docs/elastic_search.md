## Elastic Search {elastic-search}

Модуль поиска на базе Elasticsearch. Предоставляет мощные возможности полнотекстового поиска по всем данным системы. Включает поиск по специальностям, группам, преподавателям и дисциплинам. Поддерживает сложные запросы, фильтрацию и ранжирование результатов. Обеспечивает быстрый доступ к информации для пользователей системы.

### Endpoints

| Method | Path | Function | Auth Required | Description |
|--------|------|----------|---------------|-------------|
| POST | `/api/v1/public/elastic/autocomplete_spec` | fast_search | ✗ | код специальности и название склеить на фронте(воз... |
| POST | `/api/v1/public/elastic/ext_spec` | deep_search | ✗ | код специальности и название склеить на фронте(воз... |

### Database Tables
- `elasticsearch_indexes`
- `search_cache`

### Data Schemas
- `AutocompleteSearchSchema`
- `DeepSearchResponse`
- `AutocompleteSearchResponse`
- `DeepSearchSchema`

### Usage Examples

#### Successful POST request to /api/v1/public/elastic/autocomplete_spec
Example of a successful post request to the fast_search endpoint.

**Request:**
```bash
curl -X POST -v -H "Content-Type: application/json" -d '{"search_term":"example_string","search_mode":"example_string"}' "https://api.example.com/api/v1/public/elastic/autocomplete_spec"
```

**Response:**
```json
{
  "search_res": [
    {
      "id": "1",
      "spec_code": "09.02.07",
      "title": "Информационные системы и программирование"
    },
    {
      "id": "2",
      "spec_code": "09.02.03",
      "title": "Программирование в компьютерных системах"
    }
  ]
}
```

#### Validation Error - POST /api/v1/public/elastic/autocomplete_spec
Example of a validation error when required parameters are missing.

**Request:**
```bash
curl -X POST -v "https://api.example.com/api/v1/public/elastic/autocomplete_spec"
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

#### Successful POST request to /api/v1/public/elastic/ext_spec
Example of a successful post request to the deep_search endpoint.

**Request:**
```bash
curl -X POST -v -H "Content-Type: application/json" -d '{"search_term":"example_string","search_mode":"example_string"}' "https://api.example.com/api/v1/public/elastic/ext_spec"
```

**Response:**
```json
{
  "search_res": [
    {
      "id": "1",
      "spec_code": "09.02.07",
      "title": "Информационные системы и программирование"
    },
    {
      "id": "2",
      "spec_code": "09.02.03",
      "title": "Программирование в компьютерных системах"
    },
    {
      "id": "3",
      "spec_code": "10.02.05",
      "title": "Обеспечение информационной безопасности"
    }
  ]
}
```

---
