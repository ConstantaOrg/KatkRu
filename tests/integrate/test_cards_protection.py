"""
Тесты для защиты от изменения утвержденных версий расписания
и дублирования утвержденных карточек.
"""
import pytest


@pytest.mark.asyncio
async def test_save_card_blocked_on_committed_version(client, seed_info, pg_pool):
    """Проверка, что нельзя сохранить карточку в утвержденной версии расписания"""
    async with pg_pool.acquire() as conn:
        # Создаем новое здание для этого теста
        b_id = await conn.fetchval("INSERT INTO buildings (address) VALUES ('Building_Save_Test') RETURNING id")
        g_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR_SAVE_TEST', $1, true) RETURNING id",
            b_id
        )
        
        # Создаем утвержденную версию расписания
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', true) RETURNING id",
            seed_info["ttable_statuses"]["accepted"],
            b_id,
            seed_info["user_id"]
        )
        
        # Создаем карточку
        hist_id = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            ttv_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["edited"],
            g_id
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
            "VALUES ($1, $2, 1, '101', $3, $4, false), ($1, $2, 2, '102', $3, $4, false)",
            hist_id,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
            ttv_id
        )
    
    # Пытаемся сохранить изменения
    resp = await client.post(
        "/api/v1/private/n8n_ui/cards/save",
        json={
            "card_hist_id": hist_id,
            "ttable_id": ttv_id,
            "week_day": None,
            "lessons": [
                {
                    "position": 1,
                    "discipline_id": seed_info["discipline_id"],
                    "teacher_id": seed_info["teacher_id"],
                    "aud": "201",
                    "week_day": None,
                    "is_force": False
                }
            ]
        }
    )
    
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "утверждена" in data["description"].lower()


@pytest.mark.asyncio
async def test_accept_card_blocked_on_committed_version(client, seed_info, pg_pool):
    """Проверка, что нельзя утвердить карточку в утвержденной версии расписания"""
    async with pg_pool.acquire() as conn:
        # Создаем новое здание
        b_id = await conn.fetchval("INSERT INTO buildings (address) VALUES ('Building_Accept_Test') RETURNING id")
        g_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR_ACCEPT_TEST', $1, true) RETURNING id",
            b_id
        )
        
        # Утвержденная версия
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', true) RETURNING id",
            seed_info["ttable_statuses"]["accepted"],
            b_id,
            seed_info["user_id"]
        )
        
        hist_id = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            ttv_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["edited"],
            g_id
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
            "VALUES ($1, $2, 1, '101', $3, $4, false), ($1, $2, 2, '102', $3, $4, false)",
            hist_id,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
            ttv_id
        )
    
    resp = await client.put(
        "/api/v1/private/n8n_ui/cards/accept",
        json={"card_hist_id": hist_id}
    )
    
    assert resp.status_code == 403
    assert "утверждена" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_card_duplicate_rejected(client, seed_info, pg_pool):
    """Проверка, что нельзя утвердить две карточки для одной группы в одной версии"""
    async with pg_pool.acquire() as conn:
        # НЕ утвержденная версия (pending)
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', false) RETURNING id",
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Первая карточка
        hist_id1 = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            ttv_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["draft"],
            seed_info["group_id"]
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
            "VALUES ($1, $2, 1, '101', $3, $4, false), ($1, $2, 2, '102', $3, $4, false)",
            hist_id1,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
            ttv_id
        )
        
        # Вторая карточка для той же группы
        hist_id2 = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, false, $4) RETURNING id",
            ttv_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["draft"],
            seed_info["group_id"]
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
            "VALUES ($1, $2, 3, '201', $3, $4, false), ($1, $2, 4, '202', $3, $4, false)",
            hist_id2,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
            ttv_id
        )
    
    # Утверждаем первую карточку - должно пройти
    resp1 = await client.put(
        "/api/v1/private/n8n_ui/cards/accept",
        json={"card_hist_id": hist_id1}
    )
    assert resp1.status_code == 200
    
    # Проверяем, что статус изменился на accepted
    async with pg_pool.acquire() as conn:
        status1 = await conn.fetchval(
            "SELECT status_id FROM cards_states_history WHERE id = $1",
            hist_id1
        )
    assert status1 == seed_info["cards_statuses"]["accepted"]
    
    # Пытаемся утвердить вторую карточку - должно быть отклонено
    resp2 = await client.put(
        "/api/v1/private/n8n_ui/cards/accept",
        json={"card_hist_id": hist_id2}
    )
    assert resp2.status_code == 409
    assert "уже существует утвержденная карточка" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_add_cards_empty_lessons(client, seed_info, pg_pool):
    """Проверка bulk_add с пустым списком уроков (создание пустых карточек)"""
    async with pg_pool.acquire() as conn:
        # Создаем новую группу для этого теста
        g_name = f"GR_BULK_EMPTY_{seed_info['group_id']}"
        await conn.execute(
            "INSERT INTO groups (name, building_id, is_active) VALUES ($1, $2, true)",
            g_name,
            seed_info["building_id"]
        )
        
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', false) RETURNING id",
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
    
    resp = await client.post(
        "/api/v1/private/n8n_ui/cards/bulk_add",
        json={
            "ttable_id": ttv_id,
            "week_day": None,
            "group_names": [g_name],
            "lessons": []
        }
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["cards_ids"]) == 1
    
    # Проверяем, что карточка создана без уроков
    async with pg_pool.acquire() as conn:
        details_count = await conn.fetchval(
            "SELECT COUNT(*) FROM cards_states_details WHERE card_hist_id = $1",
            data["cards_ids"][0]
        )
    assert details_count == 0


@pytest.mark.asyncio
async def test_bulk_add_cards_with_lessons(client, seed_info, pg_pool):
    """Проверка bulk_add с уроками для нескольких групп"""
    async with pg_pool.acquire() as conn:
        # Создаем две новые группы
        g1_name = f"GR_BULK1_{seed_info['group_id']}"
        g2_name = f"GR_BULK2_{seed_info['group_id']}"
        
        # Создаем второго преподавателя для второй группы
        t2_id = await conn.fetchval("INSERT INTO teachers (fio) VALUES ('Teacher_Bulk') RETURNING id")
        
        await conn.execute(
            "INSERT INTO groups (name, building_id, is_active) VALUES ($1, $2, true), ($3, $2, true)",
            g1_name,
            seed_info["building_id"],
            g2_name
        )
        
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', false) RETURNING id",
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
    
    # Добавляем карточки для первой группы
    resp1 = await client.post(
        "/api/v1/private/n8n_ui/cards/bulk_add",
        json={
            "ttable_id": ttv_id,
            "week_day": None,
            "group_names": [g1_name],
            "lessons": [
                {
                    "position": 1,
                    "discipline_id": seed_info["discipline_id"],
                    "teacher_id": seed_info["teacher_id"],
                    "aud": "301",
                    "week_day": None,
                    "is_force": False
                },
                {
                    "position": 2,
                    "discipline_id": seed_info["discipline_id"],
                    "teacher_id": seed_info["teacher_id"],
                    "aud": "302",
                    "week_day": None,
                    "is_force": False
                }
            ]
        }
    )
    
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    assert len(data1["cards_ids"]) == 1
    
    # Добавляем карточки для второй группы с другим преподавателем
    resp2 = await client.post(
        "/api/v1/private/n8n_ui/cards/bulk_add",
        json={
            "ttable_id": ttv_id,
            "week_day": None,
            "group_names": [g2_name],
            "lessons": [
                {
                    "position": 1,
                    "discipline_id": seed_info["discipline_id"],
                    "teacher_id": t2_id,
                    "aud": "401",
                    "week_day": None,
                    "is_force": False
                },
                {
                    "position": 2,
                    "discipline_id": seed_info["discipline_id"],
                    "teacher_id": t2_id,
                    "aud": "402",
                    "week_day": None,
                    "is_force": False
                }
            ]
        }
    )
    
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
    assert len(data2["cards_ids"]) == 1
    
    # Проверяем, что у каждой карточки по 2 урока
    async with pg_pool.acquire() as conn:
        for card_id in data1["cards_ids"] + data2["cards_ids"]:
            details_count = await conn.fetchval(
                "SELECT COUNT(*) FROM cards_states_details WHERE card_hist_id = $1",
                card_id
            )
            assert details_count == 2


@pytest.mark.asyncio
async def test_bulk_add_cards_group_not_found(client, seed_info, pg_pool):
    """Проверка bulk_add с несуществующей группой"""
    async with pg_pool.acquire() as conn:
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', false) RETURNING id",
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
    
    resp = await client.post(
        "/api/v1/private/n8n_ui/cards/bulk_add",
        json={
            "ttable_id": ttv_id,
            "week_day": None,
            "group_names": ["NONEXISTENT_GROUP_XYZ"],
            "lessons": []
        }
    )
    
    assert resp.status_code == 404
    assert "не найдены" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_add_cards_blocked_on_committed_version(client, seed_info, pg_pool):
    """Проверка, что bulk_add блокируется на утвержденной версии"""
    async with pg_pool.acquire() as conn:
        # Создаем новое здание
        b_id = await conn.fetchval("INSERT INTO buildings (address) VALUES ('Building_Bulk_Blocked') RETURNING id")
        g_name = f"GR_BULK_BLOCKED_{seed_info['group_id']}"
        await conn.execute(
            "INSERT INTO groups (name, building_id, is_active) VALUES ($1, $2, true)",
            g_name,
            b_id
        )
        
        # Утвержденная версия
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $1, $2, $3, 'standard', true) RETURNING id",
            seed_info["ttable_statuses"]["accepted"],
            b_id,
            seed_info["user_id"]
        )
    
    resp = await client.post(
        "/api/v1/private/n8n_ui/cards/bulk_add",
        json={
            "ttable_id": ttv_id,
            "week_day": None,
            "group_names": [g_name],
            "lessons": []
        }
    )
    
    assert resp.status_code == 403
    assert "утверждена" in resp.json()["detail"].lower()
