import pytest
from uuid import uuid4
from core.data.sql_queries.users_sql import UsersQueries


def _new_creds():
    email = f"test_{uuid4().hex}@example.com"
    return {"email": email, "passw": "Pa$$w0rd"}

@pytest.fixture(autouse=True)
def patch_users_select(monkeypatch):
    async def select_with_role(self, email):
        row = await self.conn.fetchrow("SELECT id, passw, role, building_id FROM users WHERE email=$1", email)
        if row is None:
            return None
        data = dict(row)
        data.setdefault("role", "methodist")
        return data

    monkeypatch.setattr(UsersQueries, "select_user", select_with_role)


@pytest.mark.asyncio
async def test_sign_up_then_login_and_logout(client, seed_info):
    creds = _new_creds()
    import core.data.sql_queries.users_sql as u_sql
    assert u_sql.encryption.hash("probe") == "hashed::probe"
    reg = await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    assert reg.status_code == 200

    login = await client.post("/api/v1/public/users/login", json=creds)
    assert login.status_code == 200
    assert "access_token" in login.cookies and "refresh_token" in login.cookies

    logout = await client.put("/api/v1/private/users/logout", cookies=login.cookies)
    assert logout.status_code == 200
    assert "access_token" not in logout.cookies


@pytest.mark.asyncio
async def test_sign_up_duplicate_email(client, seed_info):
    creds = _new_creds()
    reg1 = await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    assert reg1.status_code == 200
    reg2 = await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    assert reg2.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client, seed_info):
    creds = _new_creds()
    await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    bad = {**creds, "passw": "wrongpass"}
    resp = await client.post("/api/v1/public/users/login", json=bad)
    assert resp.status_code == 401
