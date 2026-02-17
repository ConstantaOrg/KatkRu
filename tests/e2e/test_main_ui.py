"""
Тесты для эндпоинтов главного UI расписания (core/api/n8n_ui/main_ui.py)
"""
import pytest
from datetime import date


@pytest.mark.asyncio
async def test_create_standard_ttable(client, seed_info):
    """
    Тест /create - создание стандартного расписания
    Проверяет ограничения уникального индекса ttable_versions_building_id_type_idx
    """
    response = await client.post(
        "/api/v1/private/n8n_ui/ttable/create",
        json={
            "date": "2026-12-31",  # Будущая дата для прохождения валидации
            "type": "standard"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "ttable_id" in data
    
    # Проверяем, что расписание создано в БД
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        ttable = await conn.fetchrow(
            "SELECT * FROM ttable_versions WHERE id = $1",
            data["ttable_id"]
        )
        assert ttable is not None
        assert ttable["type"] == "standard"
        # Для standard расписания date может быть любой
        assert ttable["building_id"] == seed_info["building_id"]


@pytest.mark.asyncio
async def test_create_replacements_ttable(client, seed_info):
    """
    Тест /create - создание расписания замен
    Проверяет ограничения уникального индекса ttable_versions_building_date_replacements_idx
    """
    test_date = date(2026, 5, 15)
    
    response = await client.post(
        "/api/v1/private/n8n_ui/ttable/create",
        json={
            "date": test_date.isoformat(),
            "type": "replacements"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "ttable_id" in data
    
    # Проверяем в БД
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        ttable = await conn.fetchrow(
            "SELECT * FROM ttable_versions WHERE id = $1",
            data["ttable_id"]
        )
        assert ttable is not None
        assert ttable["type"] == "replacements"
        assert ttable["schedule_date"] == test_date


@pytest.mark.asyncio
async def test_std_check_exists_with_outdated_records(client, seed_info):
    """
    Тест /std/check_exists - проверка с устаревшими записями (is_active = false)
    """
    # Создаём устаревшие записи (is_active = false)
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        # Деактивируем существующую группу
        await conn.execute(
            "UPDATE groups SET is_active = false WHERE id = $1",
            seed_info["group_id"]
        )
        
        # Деактивируем преподавателя
        await conn.execute(
            "UPDATE teachers SET is_active = false WHERE id = $1",
            seed_info["teacher_id"]
        )
        
        # Деактивируем дисциплину
        await conn.execute(
            "UPDATE disciplines SET is_active = false WHERE id = $1",
            seed_info["discipline_id"]
        )
    
    response = await client.post(
        "/api/v1/private/n8n_ui/ttable/std/check_exists",
        json={"ttable_id": seed_info["std_sched_id"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Должны быть обнаружены различия
    assert "diff_groups" in data
    assert "diff_teachers" in data
    assert "diff_disciplines" in data
    
    # Восстанавливаем активность для других тестов
    async with pg_pool.acquire() as conn:
        await conn.execute(
            "UPDATE groups SET is_active = true WHERE id = $1",
            seed_info["group_id"]
        )
        await conn.execute(
            "UPDATE teachers SET is_active = true WHERE id = $1",
            seed_info["teacher_id"]
        )
        await conn.execute(
            "UPDATE disciplines SET is_active = true WHERE id = $1",
            seed_info["discipline_id"]
        )


@pytest.mark.asyncio
async def test_std_check_exists_without_outdated_records(client, seed_info):
    """
    Тест /std/check_exists - проверка без устаревших записей
    Все записи активны (is_active = true)
    """
    response = await client.post(
        "/api/v1/private/n8n_ui/ttable/std/check_exists",
        json={"ttable_id": seed_info["std_sched_id"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Не должно быть различий
    assert len(data.get("diff_groups", [])) == 0
    assert len(data.get("diff_teachers", [])) == 0
    assert len(data.get("diff_disciplines", [])) == 0


@pytest.mark.asyncio
async def test_versions_pre_commit_no_updating_needed(client, seed_info):
    """
    Тест /versions/pre-commit - случай, когда not_updating (просто меняется статус)
    Расписание меняет status_id = 1 AND is_commited = true
    """
    # Создаём версию, которая готова к коммиту без обновлений
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 6, 10),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Создаём карточки для всех групп (чтобы не было needed_groups)
        group_ids = await conn.fetch("SELECT id FROM groups WHERE building_id = $1", seed_info["building_id"])
        
        # Создаём дополнительных преподавателей для каждой группы
        for idx, group_row in enumerate(group_ids):
            # Создаём уникального преподавателя для каждой группы
            teacher_id = await conn.fetchval(
                f"INSERT INTO teachers (fio) VALUES ('Teacher for Pre-commit Test {idx}') RETURNING id"
            )
            
            card_hist_id = await conn.fetchval(
                "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
                "VALUES ($1, $2, $3, true, $4) RETURNING id",
                ttable_id,
                seed_info["user_id"],
                seed_info["cards_statuses"]["accepted"],
                group_row["id"]
            )
            
            # Добавляем минимум 2 урока для каждой карточки с уникальным преподавателем
            await conn.execute(
                "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
                "VALUES ($1, $2, 1, '101', $3, $4, false), ($1, $2, 2, '102', $3, $4, false)",
                card_hist_id,
                seed_info["discipline_id"],
                teacher_id,
                ttable_id
            )
    
    response = await client.put(
        "/api/v1/private/n8n_ui/ttable/versions/pre-commit",
        json={"ttable_id": ttable_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_versions_switch_as_pending_success(client, seed_info):
    """
    Тест /versions/switch_as_pending - успешное изменение статуса на 'Редактировано'
    Версия: is_commited = false
    """
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 7, 1),
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
    
    response = await client.put(
        "/api/v1/private/n8n_ui/ttable/versions/switch_as_pending",
        json={"ttable_id": ttable_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_versions_switch_as_pending_forbidden_committed(client, seed_info):
    """
    Тест /versions/switch_as_pending - попытка изменить утверждённую версию
    Версия: is_commited = true
    Ожидается: 403 Forbidden
    """
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', true) RETURNING id",
            date(2026, 7, 15),
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
    
    response = await client.put(
        "/api/v1/private/n8n_ui/ttable/versions/switch_as_pending",
        json={"ttable_id": ttable_id}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "утверждена" in data["detail"].lower()


@pytest.mark.asyncio
async def test_versions_switch_as_pending_different_status_ids(client, seed_info):
    """
    Тест /versions/switch_as_pending - проверка с разными status_id
    """
    # Тест с status_id = pending (2)
    pg_pool = client.app.state.pg_pool
    async with pg_pool.acquire() as conn:
        ttable_id_pending = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 8, 1),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
    
    response = await client.put(
        "/api/v1/private/n8n_ui/ttable/versions/switch_as_pending",
        json={"ttable_id": ttable_id_pending}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
