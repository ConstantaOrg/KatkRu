"""
Тесты для эндпоинтов дисциплин (core/api/disciplines_tab.py)
"""
import pytest


@pytest.mark.asyncio
async def test_get_disciplines_with_is_active_none(client, seed_info):
    """
    Тест /get - получение всех дисциплин (is_active = None)
    Должны вернуться все дисциплины независимо от статуса
    """
    response = await client.post(
        "/api/v1/private/disciplines/get",
        json={
            "body": {"is_active": None, "group_name": None},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "disciplines" in data
    assert len(data["disciplines"]) > 0


@pytest.mark.asyncio
async def test_get_disciplines_with_is_active_true(client, seed_info):
    """
    Тест /get - получение только активных дисциплин (is_active = True)
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём активную и неактивную дисциплину
    async with pg_pool.acquire() as conn:
        active_disc_id = await conn.fetchval(
            "INSERT INTO disciplines (title, is_active) VALUES ('Активная Дисциплина', true) RETURNING id"
        )
        inactive_disc_id = await conn.fetchval(
            "INSERT INTO disciplines (title, is_active) VALUES ('Неактивная Дисциплина', false) RETURNING id"
        )
    
    response = await client.post(
        "/api/v1/private/disciplines/get",
        json={
            "body": {"is_active": True, "group_name": None},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "disciplines" in data
    
    # Проверяем, что все возвращённые дисциплины активны
    for discipline in data["disciplines"]:
        assert discipline["is_active"] is True
    
    # Проверяем, что активная дисциплина есть в списке
    discipline_ids = [d["id"] for d in data["disciplines"]]
    assert active_disc_id in discipline_ids
    assert inactive_disc_id not in discipline_ids


@pytest.mark.asyncio
async def test_get_disciplines_with_is_active_false(client, seed_info):
    """
    Тест /get - получение только неактивных дисциплин (is_active = False)
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём неактивную дисциплину
    async with pg_pool.acquire() as conn:
        inactive_disc_id = await conn.fetchval(
            "INSERT INTO disciplines (title, is_active) VALUES ('Деактивированная Дисциплина', false) RETURNING id"
        )
    
    response = await client.post(
        "/api/v1/private/disciplines/get",
        json={
            "body": {"is_active": False, "group_name": None},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "disciplines" in data
    
    # Проверяем, что все возвращённые дисциплины неактивны
    for discipline in data["disciplines"]:
        assert discipline["is_active"] is False
    
    # Проверяем, что наша неактивная дисциплина есть в списке
    discipline_ids = [d["id"] for d in data["disciplines"]]
    assert inactive_disc_id in discipline_ids


@pytest.mark.asyncio
async def test_get_disciplines_filtered_by_group(client, seed_info):
    """
    Тест /get - фильтрация дисциплин по группе
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём группу и привязываем к ней дисциплины
    async with pg_pool.acquire() as conn:
        test_group_name = "TestGroup123"
        test_group_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id) VALUES ($1, $2) RETURNING id",
            test_group_name,
            seed_info["building_id"]
        )
        
        # Создаём дисциплины
        disc1_id = await conn.fetchval(
            "INSERT INTO disciplines (title) VALUES ('Дисциплина для группы 1') RETURNING id"
        )
        disc2_id = await conn.fetchval(
            "INSERT INTO disciplines (title) VALUES ('Дисциплина для группы 2') RETURNING id"
        )
        
        # Привязываем дисциплины к группе
        await conn.execute(
            "INSERT INTO groups_disciplines (group_id, discipline_id) VALUES ($1, $2), ($1, $3) ON CONFLICT DO NOTHING",
            test_group_id, disc1_id, disc2_id
        )
    
    response = await client.post(
        "/api/v1/private/disciplines/get",
        json={
            "body": {"is_active": None, "group_name": test_group_name},
            "pagen": {"limit": 100, "offset": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "disciplines" in data
    # Должны вернуться только дисциплины, привязанные к этой группе
    discipline_ids = [d["id"] for d in data["disciplines"]]
    assert disc1_id in discipline_ids
    assert disc2_id in discipline_ids


@pytest.mark.asyncio
async def test_add_discipline_success(client, seed_info):
    """
    Тест /add - успешное добавление дисциплины
    """
    pg_pool = client.app.state.pg_pool
    new_discipline_title = "Новая Тестовая Дисциплина"
    
    response = await client.post(
        "/api/v1/private/disciplines/add",
        json={"title": new_discipline_title}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "discipline_id" in data
    
    # Проверяем, что дисциплина добавлена в БД
    async with pg_pool.acquire() as conn:
        discipline = await conn.fetchrow(
            "SELECT * FROM disciplines WHERE id = $1",
            data["discipline_id"]
        )
        assert discipline is not None
        assert discipline["title"] == new_discipline_title
        assert discipline["is_active"] is True  # По умолчанию должна быть активной


@pytest.mark.asyncio
async def test_add_discipline_duplicate_conflict(client, seed_info):
    """
    Тест /add - попытка добавить дисциплину с существующим названием
    Проверка нарушения уникального индекса
    Ожидается: 409 Conflict
    """
    pg_pool = client.app.state.pg_pool
    duplicate_title = "Дубликат Дисциплины"
    
    # Добавляем дисциплину первый раз
    async with pg_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO disciplines (title) VALUES ($1)",
            duplicate_title
        )
    
    # Пытаемся добавить ту же дисциплину
    response = await client.post(
        "/api/v1/private/disciplines/add",
        json={"title": duplicate_title}
    )
    
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_update_disciplines_switch_status(client, seed_info):
    """
    Тест /update - изменение статусов дисциплин
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём дисциплины с разными статусами
    async with pg_pool.acquire() as conn:
        disc_to_activate = await conn.fetchval(
            "INSERT INTO disciplines (title, is_active) VALUES ('Для Активации', false) RETURNING id"
        )
        disc_to_deactivate = await conn.fetchval(
            "INSERT INTO disciplines (title, is_active) VALUES ('Для Деактивации', true) RETURNING id"
        )
    
    # Меняем статусы
    response = await client.put(
        "/api/v1/private/disciplines/update",
        json={
            "set_as_active": [disc_to_activate],
            "set_as_deprecated": [disc_to_deactivate]
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
            "SELECT is_active FROM disciplines WHERE id = $1",
            disc_to_activate
        )
        deactivated = await conn.fetchval(
            "SELECT is_active FROM disciplines WHERE id = $1",
            disc_to_deactivate
        )
        
        assert activated is True
        assert deactivated is False


@pytest.mark.asyncio
async def test_get_relations(client, seed_info):
    """
    Тест /get_relations - получение связей дисциплины с группами
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём дисциплину и связываем её с группами
    async with pg_pool.acquire() as conn:
        test_disc_id = await conn.fetchval(
            "INSERT INTO disciplines (title) VALUES ('Дисциплина для связей') RETURNING id"
        )
        
        # Привязываем к существующей группе
        await conn.execute(
            "INSERT INTO groups_disciplines (group_id, discipline_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            seed_info["group_id"],
            test_disc_id
        )
    
    response = await client.post(
        "/api/v1/private/disciplines/get_relations",
        json={"discipline_id": test_disc_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "group_relations" in data
    assert len(data["group_relations"]) > 0


@pytest.mark.asyncio
async def test_add_relation_success(client, seed_info):
    """
    Тест /add_relation - успешное добавление связи группа-дисциплина
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём новую дисциплину
    async with pg_pool.acquire() as conn:
        new_disc_id = await conn.fetchval(
            "INSERT INTO disciplines (title) VALUES ('Дисциплина для новой связи') RETURNING id"
        )
        
        # Получаем имя существующей группы
        group_name = await conn.fetchval(
            "SELECT name FROM groups WHERE id = $1",
            seed_info["group_id"]
        )
    
    response = await client.post(
        "/api/v1/private/disciplines/add_relation",
        json={
            "discipline_id": new_disc_id,
            "group_name": group_name
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Проверяем, что связь создана в БД
    async with pg_pool.acquire() as conn:
        relation_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM groups_disciplines WHERE group_id = $1 AND discipline_id = $2)",
            seed_info["group_id"],
            new_disc_id
        )
        assert relation_exists is True


@pytest.mark.asyncio
async def test_add_relation_nonexistent_group(client, seed_info):
    """
    Тест /add_relation - попытка добавить связь с несуществующей группой
    Ожидается: 400 Bad Request
    """
    response = await client.post(
        "/api/v1/private/disciplines/add_relation",
        json={
            "discipline_id": seed_info["discipline_id"],
            "group_name": "НесуществующаяГруппа999"
        }
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_add_relation_duplicate_conflict(client, seed_info):
    """
    Тест /add_relation - попытка добавить существующую связь
    Ожидается: 409 Conflict
    """
    pg_pool = client.app.state.pg_pool
    
    # Создаём связь
    async with pg_pool.acquire() as conn:
        group_name = await conn.fetchval(
            "SELECT name FROM groups WHERE id = $1",
            seed_info["group_id"]
        )
        
        # Добавляем связь
        await conn.execute(
            "INSERT INTO groups_disciplines (group_id, discipline_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            seed_info["group_id"],
            seed_info["discipline_id"]
        )
    
    # Пытаемся добавить ту же связь
    response = await client.post(
        "/api/v1/private/disciplines/add_relation",
        json={
            "discipline_id": seed_info["discipline_id"],
            "group_name": group_name
        }
    )
    
    assert response.status_code == 409
