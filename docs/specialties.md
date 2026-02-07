## Specialties

Модуль управления специальностями учебного заведения. Предоставляет функциональность для просмотра списка специальностей и получения детальной информации о конкретной специальности. Используется для организации учебного процесса и группировки студентов по направлениям обучения.

### Endpoints

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| POST | `/api/v1/public/specialties/all` | specialties_all | ✗ |  |
| GET | `/api/v1/public/specialties/{spec_id}` | specialties_get | ✗ |  |

---

## Detailed Endpoint Documentation

### POST `/api/v1/public/specialties/all` - 

**Данные на вход:**

```python
# SpecsPaginSchema
offset: int | None
limit: int | None
```

**Процесс выполнения:**

1. **Работа с БД** - `db.specialties.get_specialties`
    - Function call: db.specialties.get_specialties

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `dict`
    - Function call: dict

5. **function** - `router.post`
    - Function call: router.post

**Возможные ответы:**

**Успешный ответ (200):**
```json
{
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

---


### GET `/api/v1/public/specialties/{spec_id}` - 

**Данные на вход:**

**Параметры:**
- `spec_id` (int, обязательный)

**Процесс выполнения:**

1. **Работа с БД** - `db.specialties.get_spec_by_id`
    - Function call: db.specialties.get_spec_by_id

2. **Работа с БД** - `get_custom_pgsql`
    - FastAPI dependency: get_custom_pgsql

3. **Работа с БД** - `PgSql`
    - Function call: PgSql

4. **function** - `dict`
    - Function call: dict

5. **function** - `router.get`
    - Function call: router.get

**Возможные ответы:**

**Успешный ответ (200):**
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


### Database Tables

- `groups`
- `specialties`

### Data Schemas

- `SpecialtiesAllResponse`
- `SpecialtyGetResponse`
- `SpecsPaginSchema`
