import pytest
from uuid import uuid4
from core.config_dir import config
from contextlib import asynccontextmanager
from core.data.sql_queries.users_sql import UsersQueries
from core.data.sql_queries.users_sql import AuthQueries


def _new_creds():
    email = f"test_{uuid4().hex}@example.com"
    return {"email": email, "passw": "Pa$$w0rd"}


@pytest.fixture(autouse=True)
def patch_encryption(monkeypatch):
    def fake_hash(pw):
        return f"hashed::{pw}"

    def fake_verify(plain, hashed):
        return hashed == fake_hash(plain)

    monkeypatch.setattr(config.encryption, "hash", fake_hash)
    monkeypatch.setattr(config.encryption, "verify", fake_verify)


class DummyRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def incr(self, key):
        self.store[key] = int(self.store.get(key, 0)) + 1
        return self.store[key]

    async def expire(self, key, ttl):
        # no-op for tests
        return True

    async def delete(self, key):
        self.store.pop(key, None)


@pytest.fixture(autouse=True)
def patch_rate_limit(monkeypatch):
    dummy = DummyRedis()

    @asynccontextmanager
    async def get_dummy():
        yield dummy

    import core.api.users.rate_limiter as rl
    monkeypatch.setattr(rl, "get_redis_connection", get_dummy)


@pytest.fixture(autouse=True)
def patch_users_select(monkeypatch):
    async def select_with_role(self, email):
        return await self.conn.fetchrow("SELECT id, passw, role FROM users WHERE email=$1", email)

    monkeypatch.setattr(UsersQueries, "select_user", select_with_role)


@pytest.fixture(autouse=True)
def patch_auth(monkeypatch):
    async def no_make_session(self, *args, **kwargs):
        return None

    async def no_check(self, *args, **kwargs):
        return None

    monkeypatch.setattr(AuthQueries, "make_session", no_make_session)
    monkeypatch.setattr(AuthQueries, "check_exist_session", no_check)


@pytest.mark.asyncio
async def test_sign_up_then_login_and_logout(client, pg_pool):
    creds = _new_creds()
    reg = await client.post("/api/v1/api/v1/server/users/sign_up", json={**creds, "name": "Tester"})
    assert reg.status_code == 200

    async with pg_pool.acquire() as conn:
        await conn.execute("UPDATE users SET role='methodist' WHERE email=$1", creds["email"])

    login = await client.post("/api/v1/api/v1/public/users/login", json=creds)
    assert login.status_code == 200
    assert "access_token" in login.cookies and "refresh_token" in login.cookies

    logout = await client.put("/api/v1/api/v1/private/users/logout", cookies=login.cookies)
    assert logout.status_code == 200
    assert "access_token" not in logout.cookies


@pytest.mark.asyncio
async def test_sign_up_duplicate_email(client, pg_pool):
    creds = _new_creds()
    reg1 = await client.post("/api/v1/api/v1/server/users/sign_up", json={**creds, "name": "Tester"})
    assert reg1.status_code == 200
    async with pg_pool.acquire() as conn:
        await conn.execute("UPDATE users SET role='methodist' WHERE email=$1", creds["email"])
    reg2 = await client.post("/api/v1/api/v1/server/users/sign_up", json={**creds, "name": "Tester"})
    assert reg2.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client, pg_pool):
    creds = _new_creds()
    await client.post("/api/v1/api/v1/server/users/sign_up", json={**creds, "name": "Tester"})
    async with pg_pool.acquire() as conn:
        await conn.execute("UPDATE users SET role='methodist' WHERE email=$1", creds["email"])
    bad = {**creds, "passw": "wrongpass"}
    resp = await client.post("/api/v1/api/v1/public/users/login", json=bad)
    assert resp.status_code == 401
