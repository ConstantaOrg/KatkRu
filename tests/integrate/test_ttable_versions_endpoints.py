import pytest

from core.utils.anything import TimetableVerStatuses, CardsStatesStatuses


@pytest.mark.asyncio
async def test_pre_commit_ok(client, pg_pool):
    async with pg_pool.acquire() as conn:
        b_id = await conn.fetchval("INSERT INTO buildings (address) VALUES ('addr10') RETURNING id")
        u_id = await conn.fetchval(
            "INSERT INTO users (name, email, passw, role) VALUES ('U', 'u@u', 'p', 'methodist') RETURNING id"
        )
        g_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR10', $1, true) RETURNING id",
            b_id,
        )
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $3, $1, $2, 'standard', false) RETURNING id",
            b_id,
            u_id,
            TimetableVerStatuses.pending,
        )
        await conn.execute(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) VALUES ($1, $2, $4, true, $3)",
            ttv_id,
            u_id,
            g_id,
            CardsStatesStatuses.draft,
        )
        hist_id = await conn.fetchval("SELECT currval('cards_states_history_id_seq')")
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
            "VALUES ($1, 1, 1, '101', 1, $2, false)",
            hist_id,
            ttv_id,
        )

    resp = await client.put(
        "/api/v1/private/ttable/versions/pre-commit",
        json={"ttable_id": ttv_id},
    )
    assert resp.status_code in (200, 202)
    payload = resp.json()
    if resp.status_code == 200:
        assert payload.get("success") is True
    else:
        # Has active version elsewhere, should return info about current active
        assert "cur_active_ver" in payload


@pytest.mark.asyncio
async def test_pre_commit_missing_groups(client, pg_pool):
    # Building 11 has two active groups, but version covers only one -> expect 409
    async with pg_pool.acquire() as conn:
        b_id = await conn.fetchval("INSERT INTO buildings (address) VALUES ('addr11') RETURNING id")
        u_id = await conn.fetchval(
            "INSERT INTO users (name, email, passw, role) VALUES ('U2', 'u2@u', 'p', 'methodist') RETURNING id"
        )
        g1_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR11', $1, true) RETURNING id",
            b_id,
        )
        g2_id = await conn.fetchval(
            "INSERT INTO groups (name, building_id, is_active) VALUES ('GR12', $1, true) RETURNING id",
            b_id,
        )
        ttv_id = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $3, $1, $2, 'standard', false) RETURNING id",
            b_id,
            u_id,
            TimetableVerStatuses.pending,
        )
        await conn.execute(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) VALUES ($1, $2, $4, true, $3)",
            ttv_id,
            u_id,
            g1_id,
            CardsStatesStatuses.draft,
        )
        hist_id = await conn.fetchval("SELECT currval('cards_states_history_id_seq')")
        await conn.execute(
            "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
            "VALUES ($1, 1, 1, '101', 1, $2, false)",
            hist_id,
            ttv_id,
        )

    resp = await client.put(
        "/api/v1/private/ttable/versions/pre-commit",
        json={"ttable_id": ttv_id},
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "needed_groups" in data
    assert isinstance(data["needed_groups"], list)
    assert len(data["needed_groups"]) == 1
    assert g2_id in data["needed_groups"]  # g2 is missing from the version
    assert data["success"] is False
    assert data["ttable_id"] == ttv_id


@pytest.mark.asyncio
async def test_commit_version(client, pg_pool):
    # Make two versions in distinct building to avoid unique conflicts
    async with pg_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE ttable_versions CASCADE")
        b_id = await conn.fetchval("INSERT INTO buildings (address) VALUES ('addr12') RETURNING id")
        u_id = await conn.fetchval(
            "INSERT INTO users (name, email, passw, role) VALUES ('U3', 'u3@u', 'p', 'methodist') RETURNING id"
        )
        pending = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $3, $1, $2, 'standard', false) RETURNING id",
            b_id,
            u_id,
            TimetableVerStatuses.pending,
        )
        target = await conn.fetchval(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES (current_date, $3, $1, $2, 'standard', true) RETURNING id",
            b_id,
            u_id,
            TimetableVerStatuses.accepted,
        )

    resp = await client.put(
        "/api/v1/private/ttable/versions/commit",
        json={"pending_ver_id": pending, "target_ver_id": target},
    )
    assert resp.status_code == 200
    async with pg_pool.acquire() as conn:
        target_committed = await conn.fetchval("SELECT is_commited FROM ttable_versions WHERE id=$1", target)
        pending_committed = await conn.fetchval("SELECT is_commited FROM ttable_versions WHERE id=$1", pending)
    assert target_committed is True
    assert pending_committed is False
