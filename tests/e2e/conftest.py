import asyncpg
import httpx
import pytest
from redis.asyncio import Redis

from core.config_dir.config import pool_settings, redis_settings
from core.main import app
from tests.conftest import _truncate_and_seed


@pytest.fixture(scope="session")
async def e2e_db_pool():
    pool = await asyncpg.create_pool(**pool_settings, max_size=10)
    async with pool.acquire() as conn:
        await _truncate_and_seed(conn)
    try:
        yield pool
    finally:
        await pool.close()


@pytest.fixture(autouse=True)
async def flush_redis():
    redis = Redis(**redis_settings, decode_responses=True)
    await redis.flushdb()
    try:
        yield
    finally:
        await redis.close()


@pytest.fixture
async def client(e2e_db_pool):
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def pg_pool(e2e_db_pool):
    return e2e_db_pool


@pytest.fixture(autouse=True)
def patch_encryption(monkeypatch):
    from core.config_dir import config as cfg
    import core.data.sql_queries.users_sql as u_sql
    import core.api.users.users_api as users_api
    import core.utils.jwt_factory as jwt_factory
    from core.utils.anything import default_avatar

    class FakeEnc:
        def hash(self, pw):
            return f"hashed::{pw}"

        def verify(self, plain, hashed):
            return hashed == self.hash(plain)

    fake = FakeEnc()
    monkeypatch.setattr(cfg, "encryption", fake, raising=False)
    monkeypatch.setattr(u_sql, "encryption", fake, raising=False)
    monkeypatch.setattr(users_api, "encryption", fake, raising=False)
    monkeypatch.setattr(jwt_factory, "encryption", fake, raising=False)
    assert users_api.encryption.hash("probe") == "hashed::probe"

    async def fake_reg_user(self, email, passw: str, name: str, building_id: int, avatar: str = None):
        query = '''
        INSERT INTO users (email, passw, name, building_id, image_path)
        VALUES($1, $2, $3, $4, $5)
        ON CONFLICT (email) DO NOTHING 
        RETURNING id
        '''
        return await self.conn.fetchrow(query, email, fake.hash(passw), name, building_id, avatar or default_avatar)

    monkeypatch.setattr(u_sql.UsersQueries, "reg_user", fake_reg_user, raising=False)

    async def fake_make_session(self, *args, **kwargs):
        return None

    monkeypatch.setattr(u_sql.AuthQueries, "make_session", fake_make_session, raising=False)
