## Elastic_Search

Модуль поиска на базе Elasticsearch. Предоставляет мощные возможности полнотекстового поиска по всем данным системы. Включает поиск по специальностям, группам, преподавателям и дисциплинам. Поддерживает сложные запросы, фильтрацию и ранжирование результатов. Обеспечивает быстрый доступ к информации для пользователей системы.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/public/elastic/autocomplete_spec` | fast_search | ✗ | код специальности и название склеить на фронте(воз... |
| POST | `/api/v1/public/elastic/ext_spec` | deep_search | ✗ | код специальности и название склеить на фронте(воз... |
| POST | `/api/v1/public/elastic/search_group` | fast_search | ✗ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/public/elastic/autocomplete_spec` - код специальности и название склеить на фронте(возможно)

**Данные на вход:**

```python
# AutocompleteSearchSchema
search_term: str
search_mode: str
```

**Процесс выполнения:**

1. **external_service** - `SpecIndex.search_ptn`
    - Function call: SpecIndex.search_ptn

2. **external_service** - `aioes.search`
    - Function call: aioes.search

3. **function** - `log_event`
    - Function call: log_event

4. **function** - `len`
    - Function call: len

5. **function** - `tuple`
    - Function call: tuple

6. **function** - `router.post`
    - Function call: router.post

7. **fastapi_dependency** - `get_elastic_client`
    - FastAPI dependency: get_elastic_client

**Возможные ответы:**

**Успешный ответ (200):**
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

---


### POST `/api/v1/public/elastic/ext_spec` - код специальности и название склеить на фронте(возможно)

**Данные на вход:**

```python
# DeepSearchSchema
search_term: str
search_mode: str
```

**Процесс выполнения:**

1. **external_service** - `SpecIndex.search_ptn`
    - Function call: SpecIndex.search_ptn

2. **external_service** - `aioes.search`
    - Function call: aioes.search

3. **function** - `log_event`
    - Function call: log_event

4. **function** - `len`
    - Function call: len

5. **function** - `tuple`
    - Function call: tuple

6. **function** - `router.post`
    - Function call: router.post

7. **fastapi_dependency** - `PagenSchema`
    - FastAPI dependency: PagenSchema

8. **fastapi_dependency** - `get_elastic_client`
    - FastAPI dependency: get_elastic_client

**Возможные ответы:**

**Успешный ответ (200):**
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


### POST `/api/v1/public/elastic/search_group` - 

**Данные на вход:**

```python
# BaseSpecSearchSchema
search_term: str
```

**Процесс выполнения:**

1. **fastapi_dependency** - `get_elastic_client`
    - FastAPI dependency: get_elastic_client

**Возможные ответы:**

**Успешный ответ (200):**
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

---


### Database Tables

- `elasticsearch_indexes`
- `search_cache`

### Data Schemas

- `AutocompleteSearchResponse`
- `AutocompleteSearchSchema`
- `BaseSpecSearchSchema`
- `DeepSearchResponse`
- `DeepSearchSchema`
