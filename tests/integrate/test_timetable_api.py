import pytest

from core.utils.anything import TimetableVerStatuses


@pytest.mark.asyncio
async def test_public_timetable_get(client, pg_pool, seed_info):
    async with pg_pool.acquire() as conn:
        sched_day_id = await conn.fetchval(
            "INSERT INTO schedule_days (group_id, sched_ver_id) VALUES ($1, $2) RETURNING id",
            seed_info["group_id"],
            seed_info["ttable_id"],
        )
        await conn.execute(
            """
            INSERT INTO lessons (sched_id, discipline_id, position, aud, teacher_id)
            VALUES ($1, $2, 1, '201', $3)
            """,
            sched_day_id,
            seed_info["discipline_id"],
            seed_info["teacher_id"],
        )

    body = {"building_id": seed_info["building_id"], "group": "GR1"}
    resp = await client.post("/api/v1/public/timetable/get", json=body)

    assert resp.status_code == 200
    payload = resp.json()
    assert "schedule" in payload
    schedule = payload["schedule"]
    assert len(schedule) == 1
    row = schedule[0]
    assert row["position"] == 1
    assert row["aud"] == "201"
