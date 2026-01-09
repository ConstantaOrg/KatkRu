import pytest


@pytest.mark.asyncio
async def test_specialties_all(client):
    resp = await client.post("/api/v1/public/specialties/all", json={"limit": 10, "offset": 0})
    assert resp.status_code == 200
    assert "specialties" in resp.json()


@pytest.mark.asyncio
async def test_specialties_get(client, pg_pool):
    # ensure at least one specialty exists
    async with pg_pool.acquire() as conn:
        spec_id = await conn.fetchval(
            "INSERT INTO specialties (spec_code, title, learn_years, description, full_time, free_form, evening_form, cost_per_year) "
            "VALUES ('99.99', 'SpecTest', 4, 'desc', true, false, false, 10000) RETURNING id"
        )
    resp = await client.get(f"/api/v1/public/specialties/{spec_id}")
    assert resp.status_code == 200
    data = resp.json()["speciality"]
    assert data["spec_code"] == "99.99"
    assert data["description"] == "desc"
