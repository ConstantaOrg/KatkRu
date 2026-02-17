"""
Тесты для эндпоинтов преподавателей (core/api/teachers_tab.py)
"""
import pytest


@pytest.mark.asyncio
async def test_get_teachers_with_is_active_none(client, seed_info):
    """
    Тест /get - получение всех преподавателей (is_active = None)
    Должны вернуться все преподаватели независимо от статуса
    """
    response = await client.post(
        "/api/v1/private/teachers/get",
        json={
            "body": {"is_active": None},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "teachers" in data
    assert len(data["teachers"]) > 0


@pytest.mark.asyncio
async def test_get_teachers_with_is_active_true(client, seed_info):
    """
    Тест /get - получение только активных преподавателей (is_active = True)
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём активного и неактивного преподавателя
    async with pg_pool.acquire() as conn:
        active_teacher_id = await conn.fetchval(
            "INSERT INTO teachers (fio, is_active) VALUES ('Активный Преподаватель', true) RETURNING id"
        )
        inactive_teacher_id = await conn.fetchval(
            "INSERT INTO teachers (fio, is_active) VALUES ('Неактивный Преподаватель', false) RETURNING id"
        )
    
    response = await client.post(
        "/api/v1/private/teachers/get",
        json={
            "body": {"is_active": True},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "teachers" in data
    
    # Проверяем, что все возвращённые преподаватели активны
    for teacher in data["teachers"]:
        assert teacher["is_active"] is True
    
    # Проверяем, что активный преподаватель есть в списке
    teacher_ids = [t["id"] for t in data["teachers"]]
    assert active_teacher_id in teacher_ids
    assert inactive_teacher_id not in teacher_ids


@pytest.mark.asyncio
async def test_get_teachers_with_is_active_false(client, seed_info):
    """
    Тест /get - получение только неактивных преподавателей (is_active = False)
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём неактивного преподавателя
    async with pg_pool.acquire() as conn:
        inactive_teacher_id = await conn.fetchval(
            "INSERT INTO teachers (fio, is_active) VALUES ('Деактивированный Преподаватель', false) RETURNING id"
        )
    
    response = await client.post(
        "/api/v1/private/teachers/get",
        json={
            "body": {"is_active": False},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "teachers" in data
    
    # Проверяем, что все возвращённые преподаватели неактивны
    for teacher in data["teachers"]:
        assert teacher["is_active"] is False
    
    # Проверяем, что наш неактивный преподаватель есть в списке
    teacher_ids = [t["id"] for t in data["teachers"]]
    assert inactive_teacher_id in teacher_ids


@pytest.mark.asyncio
async def test_add_teacher_success(client, seed_info):
    """
    Тест /add - успешное добавление преподавателя
    """
    pg_pool = client.app.state.pg_pool
    new_teacher_fio = "Новый Преподаватель Тестович"
    
    response = await client.post(
        "/api/v1/private/teachers/add",
        json={"fio": new_teacher_fio}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "teacher_id" in data
    
    # Проверяем, что преподаватель добавлен в БД
    async with pg_pool.acquire() as conn:
        teacher = await conn.fetchrow(
            "SELECT * FROM teachers WHERE id = $1",
            data["teacher_id"]
        )
        assert teacher is not None
        assert teacher["fio"] == new_teacher_fio
        assert teacher["is_active"] is True  # По умолчанию должен быть активным


@pytest.mark.asyncio
async def test_add_teacher_duplicate_conflict(client, seed_info):
    """
    Тест /add - попытка добавить преподавателя с существующим ФИО
    Проверка нарушения уникального индекса
    Ожидается: 409 Conflict
    """
    pg_pool = client.app.state.pg_pool
    duplicate_fio = "Дубликат Преподаватель"
    
    # Добавляем преподавателя первый раз
    async with pg_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO teachers (fio) VALUES ($1)",
            duplicate_fio
        )
    
    # Пытаемся добавить того же преподавателя
    response = await client.post(
        "/api/v1/private/teachers/add",
        json={"fio": duplicate_fio}
    )
    
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_update_teachers_switch_status(client, seed_info):
    """
    Тест /update - изменение статусов преподавателей
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём преподавателей с разными статусами
    async with pg_pool.acquire() as conn:
        teacher_to_activate = await conn.fetchval(
            "INSERT INTO teachers (fio, is_active) VALUES ('Для Активации', false) RETURNING id"
        )
        teacher_to_deactivate = await conn.fetchval(
            "INSERT INTO teachers (fio, is_active) VALUES ('Для Деактивации', true) RETURNING id"
        )
    
    # Меняем статусы
    response = await client.put(
        "/api/v1/private/teachers/update",
        json={
            "set_as_active": [teacher_to_activate],
            "set_as_deprecated": [teacher_to_deactivate]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["active_upd_count"] == 1
    assert data["depr_upd_count"] == 1
    
    # Проверяем изменения в БД
    async with pg_pool.acquire() as conn:
        activated = await conn.fetchval(
            "SELECT is_active FROM teachers WHERE id = $1",
            teacher_to_activate
        )
        deactivated = await conn.fetchval(
            "SELECT is_active FROM teachers WHERE id = $1",
            teacher_to_deactivate
        )
        
        assert activated is True
        assert deactivated is False


@pytest.mark.asyncio
async def test_update_teachers_empty_lists(client, seed_info):
    """
    Тест /update - вызов с пустыми списками
    """
    response = await client.put(
        "/api/v1/private/teachers/update",
        json={
            "set_as_active": [],
            "set_as_deprecated": []
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["active_upd_count"] == 0
    assert data["depr_upd_count"] == 0
