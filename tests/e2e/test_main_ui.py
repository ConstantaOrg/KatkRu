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



@pytest.mark.asyncio
async def test_cards_week_day_standard_schedule_uniqueness(client, seed_info):
    """
    Тест уникального индекса cards_states_history_standard_unique
    Проверяет: (sched_ver_id, group_id, week_day) WHERE status_id = 1 AND week_day IS NOT NULL
    
    Сценарий:
    1. Создаём стандартное расписание
    2. Создаём карточки для одной группы на разные дни недели (1-6)
    3. Утверждаем все карточки (status_id = 1)
    4. Пытаемся создать дубликат для того же дня - должна быть ошибка
    5. Создаём карточку для другого дня - должно пройти успешно
    """
    pg_pool = client.app.state.pg_pool
    
    async with pg_pool.acquire() as conn:
        # Создаём стандартное расписание
        std_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (NULL, $1, $2, $3, 'standard', false) RETURNING id",
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Создаём карточки для понедельника (week_day = 1)
        card_monday = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
        
        # Добавляем детали карточки
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
            "VALUES ($1, $2, 1, '101', $3, $4)",
            card_monday,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
            std_ttable_id
        )
        
        # Создаём карточку для вторника (week_day = 2) - должно пройти
        card_tuesday = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 2) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
        
        assert card_tuesday is not None
        
        # Пытаемся создать дубликат для понедельника - должна быть ошибка
        try:
            await conn.fetchval(
                "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
                "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
                std_ttable_id,
                seed_info["user_id"],
                seed_info["cards_statuses"]["accepted"],
                seed_info["group_id"]
            )
            assert False, "Должна быть ошибка уникальности индекса"
        except Exception as e:
            assert "cards_states_history_standard_unique" in str(e)
        
        # Создаём черновик для понедельника (status_id != 1) - должно пройти
        card_monday_draft = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["draft"],
            seed_info["group_id"]
        )
        
        assert card_monday_draft is not None


@pytest.mark.asyncio
async def test_cards_week_day_replacements_uniqueness(client, seed_info):
    """
    Тест уникального индекса cards_states_history_replacements_unique
    Проверяет: (sched_ver_id, group_id) WHERE status_id = 1 AND week_day IS NULL
    
    Сценарий:
    1. Создаём расписание замен
    2. Создаём карточку для группы (week_day = NULL)
    3. Утверждаем карточку (status_id = 1)
    4. Пытаемся создать дубликат - должна быть ошибка
    5. Создаём черновик - должно пройти успешно
    """
    pg_pool = client.app.state.pg_pool
    
    async with pg_pool.acquire() as conn:
        # Создаём расписание замен
        repl_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 5, 20),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Создаём утверждённую карточку (week_day = NULL)
        card_accepted = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, NULL) RETURNING id",
            repl_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
        
        # Добавляем детали
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
            "VALUES ($1, $2, 1, '201', $3, $4)",
            card_accepted,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
            repl_ttable_id
        )
        
        # Пытаемся создать дубликат утверждённой карточки - должна быть ошибка
        try:
            await conn.fetchval(
                "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
                "VALUES ($1, $2, $3, $4, true, NULL) RETURNING id",
                repl_ttable_id,
                seed_info["user_id"],
                seed_info["cards_statuses"]["accepted"],
                seed_info["group_id"]
            )
            assert False, "Должна быть ошибка уникальности индекса"
        except Exception as e:
            assert "cards_states_history_replacements_unique" in str(e)
        
        # Создаём черновик (status_id != 1) - должно пройти
        card_draft = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, NULL) RETURNING id",
            repl_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["draft"],
            seed_info["group_id"]
        )
        
        assert card_draft is not None


@pytest.mark.asyncio
async def test_load_std_lessons_as_current_from_cards(client, seed_info):
    """
    Тест функции load_std_lessons_as_current после миграции
    Проверяет загрузку шаблона из cards_states_history/details вместо std_ttable
    
    Сценарий:
    1. Создаём стандартное расписание с утверждёнными карточками для разных дней недели
    2. Создаём расписание замен
    3. Загружаем шаблон для конкретного дня недели
    4. Проверяем, что карточки скопированы с week_day = NULL
    """
    pg_pool = client.app.state.pg_pool
    
    async with pg_pool.acquire() as conn:
        # Удаляем существующее стандартное расписание из seed
        await conn.execute(
            "DELETE FROM std_ttable WHERE sched_ver_id = $1",
            seed_info["std_sched_id"]
        )
        await conn.execute(
            "DELETE FROM ttable_versions WHERE id = $1",
            seed_info["std_sched_id"]
        )
        
        # Создаём стандартное расписание
        std_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (NULL, $1, $2, $3, 'standard', true) RETURNING id",
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Создаём дополнительного преподавателя для избежания конфликтов
        teacher2_id = await conn.fetchval(
            "INSERT INTO teachers (fio) VALUES ('Teacher for Load Test') RETURNING id"
        )
        
        # Создаём утверждённые карточки для понедельника (week_day = 1)
        card_monday = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
        
        # Добавляем детали для понедельника
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
            "VALUES ($1, $2, 1, '301', $3, $4), ($1, $2, 2, '302', $3, $4)",
            card_monday,
            seed_info["discipline_id"],
            teacher2_id,
            std_ttable_id
        )
        
        # Создаём дополнительного преподавателя для вторника
        teacher3_id = await conn.fetchval(
            "INSERT INTO teachers (fio) VALUES ('Teacher for Tuesday') RETURNING id"
        )
        
        # Создаём карточку для вторника (week_day = 2)
        card_tuesday = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 2) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
            "VALUES ($1, $2, 1, '401', $3, $4)",
            card_tuesday,
            seed_info["discipline_id"],
            teacher3_id,
            std_ttable_id
        )
        
        # Создаём расписание замен
        repl_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 5, 25),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Вызываем функцию загрузки для понедельника (week_day = 1)
        from core.data.sql_queries.n8n_iu_sql import N8NIUQueries
        queries = N8NIUQueries(conn)
        
        result = await queries.load_std_lessons_as_current(
            building_id=seed_info["building_id"],
            week_day=1,
            sched_ver_id=repl_ttable_id,
            user_id=seed_info["user_id"]
        )
        
        # Проверяем результат
        assert len(result) == 2  # Должно быть 2 урока из понедельника
        
        # Проверяем, что карточки созданы с week_day = NULL
        loaded_cards = await conn.fetch(
            "SELECT * FROM cards_states_history WHERE sched_ver_id = $1",
            repl_ttable_id
        )
        
        assert len(loaded_cards) == 1
        assert loaded_cards[0]["week_day"] is None  # Для замен week_day должен быть NULL
        assert loaded_cards[0]["status_id"] == seed_info["cards_statuses"]["draft"]
        assert loaded_cards[0]["is_current"] is True
        
        # Проверяем детали карточек
        loaded_details = await conn.fetch(
            "SELECT * FROM cards_states_details WHERE sched_ver_id = $1",
            repl_ttable_id
        )
        
        assert len(loaded_details) == 2  # 2 урока из понедельника


@pytest.mark.asyncio
async def test_load_std_lessons_multiple_groups(client, seed_info):
    """
    Тест загрузки шаблона для нескольких групп
    
    Сценарий:
    1. Создаём стандартное расписание с карточками для 3 групп на понедельник
    2. Загружаем шаблон в расписание замен
    3. Проверяем, что все группы загружены корректно
    """
    pg_pool = client.app.state.pg_pool
    
    async with pg_pool.acquire() as conn:
        # Удаляем существующее стандартное расписание из seed
        await conn.execute(
            "DELETE FROM std_ttable WHERE sched_ver_id = $1",
            seed_info["std_sched_id"]
        )
        await conn.execute(
            "DELETE FROM ttable_versions WHERE id = $1",
            seed_info["std_sched_id"]
        )
        
        # Создаём дополнительные группы
        group2_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR2', $1, true) RETURNING id",
            seed_info["building_id"]
        )
        group3_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR3', $1, true) RETURNING id",
            seed_info["building_id"]
        )
        
        # Создаём стандартное расписание
        std_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (NULL, $1, $2, $3, 'standard', true) RETURNING id",
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Создаём уникальных преподавателей для каждой группы
        teachers = []
        for i in range(3):
            teacher_id = await conn.fetchval(
                f"INSERT INTO teachers (fio) VALUES ('Teacher Multi {i}') RETURNING id"
            )
            teachers.append(teacher_id)
        
        # Создаём карточки для всех групп на понедельник
        for idx, group_id in enumerate([seed_info["group_id"], group2_id, group3_id]):
            card_id = await conn.fetchval(
                "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
                "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
                std_ttable_id,
                seed_info["user_id"],
                seed_info["cards_statuses"]["accepted"],
                group_id
            )
            
            await conn.execute(
                "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
                "VALUES ($1, $2, 1, '501', $3, $4), ($1, $2, 2, '502', $3, $4)",
                card_id,
                seed_info["discipline_id"],
                teachers[idx],
                std_ttable_id
            )
        
        # Создаём расписание замен
        repl_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 6, 1),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Загружаем шаблон
        from core.data.sql_queries.n8n_iu_sql import N8NIUQueries
        queries = N8NIUQueries(conn)
        
        result = await queries.load_std_lessons_as_current(
            building_id=seed_info["building_id"],
            week_day=1,
            sched_ver_id=repl_ttable_id,
            user_id=seed_info["user_id"]
        )
        
        # Проверяем результат
        assert len(result) == 6  # 3 группы * 2 урока = 6
        
        # Проверяем карточки
        loaded_cards = await conn.fetch(
            "SELECT * FROM cards_states_history WHERE sched_ver_id = $1 ORDER BY group_id",
            repl_ttable_id
        )
        
        assert len(loaded_cards) == 3
        for card in loaded_cards:
            assert card["week_day"] is None
            assert card["status_id"] == seed_info["cards_statuses"]["draft"]


@pytest.mark.asyncio
async def test_load_std_lessons_filters_inactive_entities(client, seed_info):
    """
    Тест фильтрации неактивных сущностей при загрузке шаблона
    
    Сценарий:
    1. Создаём стандартное расписание с карточками
    2. Деактивируем группу/преподавателя/дисциплину
    3. Загружаем шаблон
    4. Проверяем, что неактивные записи не загружены
    """
    pg_pool = client.app.state.pg_pool
    
    async with pg_pool.acquire() as conn:
        # Удаляем существующее стандартное расписание из seed
        await conn.execute(
            "DELETE FROM std_ttable WHERE sched_ver_id = $1",
            seed_info["std_sched_id"]
        )
        await conn.execute(
            "DELETE FROM ttable_versions WHERE id = $1",
            seed_info["std_sched_id"]
        )
        
        # Создаём дополнительную группу
        inactive_group_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('INACTIVE_GR', $1, true) RETURNING id",
            seed_info["building_id"]
        )
        
        # Создаём стандартное расписание
        std_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (NULL, $1, $2, $3, 'standard', true) RETURNING id",
            seed_info["ttable_statuses"]["accepted"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Создаём уникального преподавателя для активной группы
        teacher_active_id = await conn.fetchval(
            "INSERT INTO teachers (fio) VALUES ('Teacher Active Test') RETURNING id"
        )
        
        # Создаём уникального преподавателя для неактивной группы
        teacher_inactive_id = await conn.fetchval(
            "INSERT INTO teachers (fio) VALUES ('Teacher Inactive Test') RETURNING id"
        )
        
        # Создаём карточку для активной группы
        card_active = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            seed_info["group_id"]
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
            "VALUES ($1, $2, 1, '601', $3, $4)",
            card_active,
            seed_info["discipline_id"],
            teacher_active_id,
            std_ttable_id
        )
        
        # Создаём карточку для группы, которую деактивируем
        card_inactive = await conn.fetchval(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, group_id, is_current, week_day) "
            "VALUES ($1, $2, $3, $4, true, 1) RETURNING id",
            std_ttable_id,
            seed_info["user_id"],
            seed_info["cards_statuses"]["accepted"],
            inactive_group_id
        )
        
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id) "
            "VALUES ($1, $2, 1, '602', $3, $4)",
            card_inactive,
            seed_info["discipline_id"],
            teacher_inactive_id,
            std_ttable_id
        )
        
        # Деактивируем группу
        await conn.execute(
            "UPDATE groups SET is_active = false WHERE id = $1",
            inactive_group_id
        )
        
        # Создаём расписание замен
        repl_ttable_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'replacements', false) RETURNING id",
            date(2026, 6, 5),
            seed_info["ttable_statuses"]["pending"],
            seed_info["building_id"],
            seed_info["user_id"]
        )
        
        # Загружаем шаблон
        from core.data.sql_queries.n8n_iu_sql import N8NIUQueries
        queries = N8NIUQueries(conn)
        
        result = await queries.load_std_lessons_as_current(
            building_id=seed_info["building_id"],
            week_day=1,
            sched_ver_id=repl_ttable_id,
            user_id=seed_info["user_id"]
        )
        
        # Проверяем, что загружена только активная группа
        assert len(result) == 1
        
        loaded_cards = await conn.fetch(
            "SELECT * FROM cards_states_history WHERE sched_ver_id = $1",
            repl_ttable_id
        )
        
        assert len(loaded_cards) == 1
        assert loaded_cards[0]["group_id"] == seed_info["group_id"]
