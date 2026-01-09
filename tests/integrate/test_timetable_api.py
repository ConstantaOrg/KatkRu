import pytest

from core.utils.anything import TimetableVerStatuses


@pytest.mark.asyncio
async def test_public_timetable_get(client, pg_pool, seed_info):
    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE cards_states_details
            SET aud = '201'
            WHERE card_hist_id = $1
            """,
            seed_info["hist_id"],
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
