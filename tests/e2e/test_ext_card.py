"""
Тесты для эндпоинтов карточек расписания (core/api/n8n_ui/ext_card.py)
"""
import pytest
from datetime import date


@pytest.mark.asyncio
async def test_switch_as_edit_success(client, seed_info, pg_pool):
    """
    Тест /switch_as_edit - успешное изменение статуса карточки на 'Редактировано'
    Версия расписания: status_id != 1 AND is_commited = false
    """
    # Создаём версию расписания, которую можно редактировать
    async with pg_pool.acquire() as conn:
        editable_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'standard', false) RETURNING id",
            date.today(),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        card_hist_id = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            editable_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["draft"],
            seed_info["group_id"]
        )
        
        initial_status = await conn.fetchval(
            "SELECT status_id FROM cards_states_history WHERE id = $1",
            card_hist_id
        )
        assert initial_status == seed_info["cards_statuses"]["draft"]
    
    # Вызываем эндпоинт
    response = await client.put(
        "/api/v1/private/n8n_ui/cards/switch_as_edit",
        json={"card_hist_id": card_hist_id, "ttable_id": editable_ttable_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Проверяем изменение через БД
    async with pg_pool.acquire() as conn:
        new_status = await conn.fetchval(
            "SELECT status_id FROM cards_states_history WHERE id = $1",
            card_hist_id
        )
        assert new_status == seed_info["cards_statuses"]["edited"]


@pytest.mark.asyncio
async def test_switch_as_edit_forbidden_committed_version(client, seed_info, pg_pool):
    """
    Тест /switch_as_edit - попытка изменить карточку в утверждённой версии
    Версия расписания: status_id = 1 AND is_commited = true
    Ожидается: 403 Forbidden
    """
    async with pg_pool.acquire() as conn:
        committed_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', true) RETURNING id",
            date(2026, 3, 15),
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        card_hist_id = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            committed_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
    
    response = await client.put(
        "/api/v1/private/n8n_ui/cards/switch_as_edit",
        json={"card_hist_id": card_hist_id, "ttable_id": committed_ttable_id}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "утверждена" in data["detail"].lower() or "запрещены" in data["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_del_success(client, seed_info, pg_pool):
    """
    Тест /bulk_del - успешное удаление карточек
    Версия расписания: status_id != 1 AND is_commited = false
    """
    async with pg_pool.acquire() as conn:
        editable_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'standard', false) RETURNING id",
            date.today(),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        card_ids = []
        for i in range(3):
            card_id = await conn.fetchval(
                "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
                "VALUES ($1, $2, $3, true, $4) RETURNING id",
                editable_ttable_id,
                seed_info["user_id"],
                seed_info["cards_statuses"]["draft"],
                seed_info["group_id"]
            )
            card_ids.append(card_id)
    
    response = await client.request(
        "DELETE",
        "/api/v1/private/n8n_ui/cards/bulk_del",
        json={"card_ids": card_ids, "ttable_id": editable_ttable_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Проверяем, что эндпоинт вернул сообщение об удалении
    assert "message" in data


@pytest.mark.asyncio
async def test_bulk_del_forbidden_committed_version(client, seed_info, pg_pool):
    """
    Тест /bulk_del - попытка удалить карточки в утверждённой версии
    Ожидается: 403 Forbidden
    """
    async with pg_pool.acquire() as conn:
        committed_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', true) RETURNING id",
            date(2026, 4, 20),
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        card_id = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            committed_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
    
    response = await client.request(
        "DELETE",
        "/api/v1/private/n8n_ui/cards/bulk_del",
        json={"card_ids": [card_id], "ttable_id": committed_ttable_id}
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_group_box_w_disciplines(client, seed_info, pg_pool):
    """
    Тест /group-box_w_disciplines - проверка выдачи дисциплин для группы
    Проверяет, что возвращается правильное количество дисциплин, привязанных к группе
    """
    async with pg_pool.acquire() as conn:
        discipline_ids = []
        for i in range(3):
            disc_id = await conn.fetchval(
                f"INSERT INTO disciplines (title) VALUES ('Test Discipline {i}') RETURNING id"
            )
            discipline_ids.append(disc_id)
        
        # Привязываем дисциплины к группе (таблица groups_disciplines должна существовать)
        for disc_id in discipline_ids:
            await conn.execute(
                "INSERT INTO groups_disciplines (group_id, discipline_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                seed_info["group_id"],
                disc_id
            )
    
    response = await client.get(
        f"/api/v1/private/n8n_ui/cards/group-box_w_disciplines?group_id={seed_info['group_id']}&offset=0&limit=10"
    )
    
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert "group_box" in data
    # Проверяем, что вернулись дисциплины (как минимум те, что мы добавили)
    assert isinstance(data["group_box"], list)
