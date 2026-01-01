import pytest


@pytest.mark.asyncio
async def test_groups_get(client, seed_info):
    resp = await client.get(
        "/api/v1/private/groups/get",
        params={"bid": 1, "limit": 10, "offset": 0},
    )
    assert resp.status_code == 200
    data = resp.json()["groups"]
    assert any(row["name"] == "GR1" for row in data)


@pytest.mark.asyncio
async def test_groups_add(client, pg_pool):
    resp = await client.put(
        "/api/v1/private/groups/add",
        json={"group_name": "GR2", "building_id": 1},
    )
    assert resp.status_code == 200
    new_id = resp.json()["group_id"]
    async with pg_pool.acquire() as conn:
        exists = await conn.fetchval("SELECT count(*) FROM groups WHERE id=$1 AND name='GR2'", new_id)
    assert exists == 1


@pytest.mark.asyncio
async def test_groups_update(client, pg_pool, seed_info):
    # ожидаем деактивации группы
    resp = await client.put(
        "/api/v1/private/groups/update",
        json={"set_as_active": [], "set_as_deprecated": [seed_info["group_id"]]},
    )
    assert resp.status_code == 200
    async with pg_pool.acquire() as conn:
        is_active = await conn.fetchval("SELECT is_active FROM groups WHERE id=$1", seed_info["group_id"])
    assert is_active is False
