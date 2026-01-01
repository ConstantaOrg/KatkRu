import os
import importlib
from datetime import date

import asyncpg
import httpx
import pytest
from fastapi import FastAPI

os.environ.setdefault("ENV_FILE", ".env.test")
from core.config_dir import config  # noqa

importlib.reload(config)
env = config.env

from core.api import main_router
from core.data.postgre import get_custom_pgsql, PgSql
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.utils.anything import Roles
from core.utils.logger import log_event


TEST_DB_NAME = "test_katk_db"


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    dbname = env.pg_db
    assert isinstance(dbname, str), "env.pg_db is not set"
    assert dbname.startswith("test_"), f"Refusing to run tests against non-test database: {dbname}"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def log_test_run(request):
    log_event(f"Запуск теста: {request.node.nodeid}")
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep is None:
        status = "нет статуса"
    elif rep.failed:
        status = "провален"
    elif rep.skipped:
        status = "пропущен"
    else:
        status = "пройден"
    log_event(f"Завершение теста: {request.node.nodeid} | статус: {status}")


async def _truncate_and_seed(conn: asyncpg.Connection):
    tables_to_truncate = [
        "cards_states_details",
        "cards_states_history",
        "std_ttable",
        "ttable_versions",
        "schedule_days",
        "lessons",
        "teachers_weekend",
        "teachers_buildings",
        "teachers",
        "groups",
        "specialties",
        "disciplines",
        "sessions_users",
        "users",
        "cards_statuses",
        "ttable_statuses",
        "buildings",
    ]
    await conn.execute("TRUNCATE TABLE " + ",".join(tables_to_truncate) + " RESTART IDENTITY CASCADE")

    cards_statuses = await conn.fetch("INSERT INTO cards_statuses (title) VALUES ('accepted'), ('edited'), ('draft') RETURNING id, title")
    ttable_statuses = await conn.fetch("INSERT INTO ttable_statuses (title) VALUES ('accepted'), ('pending') RETURNING id, title")
    building_id = (await conn.fetchrow("INSERT INTO buildings (address) VALUES ('Test address') RETURNING id"))["id"]
    user_id = (await conn.fetchrow(
        "INSERT INTO users (name, email, passw, role) VALUES ('Test User', 'test@example.com', 'pass', 'methodist') RETURNING id"
    ))["id"]
    group_id = (await conn.fetchrow(
        "INSERT INTO groups (name, building_id, is_active) VALUES ('GR1', $1, true) RETURNING id",
        building_id,
    ))["id"]
    discipline_id = (await conn.fetchrow(
        "INSERT INTO disciplines (title) VALUES ('Math') RETURNING id"
    ))["id"]
    teacher_id = (await conn.fetchrow(
        "INSERT INTO teachers (fio) VALUES ('Иванов И.И.') RETURNING id"
    ))["id"]
    std_sched_id = (await conn.fetchrow(
        "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
        "VALUES ($1, $2, $3, $4, 'standard', true) RETURNING id",
        date.today(),
        ttable_statuses[0]["id"],
        building_id,
        user_id,
    ))["id"]

    await conn.execute(
        "INSERT INTO std_ttable (sched_ver_id, group_id, discipline_id, position, aud, teacher_id, week_day) "
        "VALUES ($1, $2, $3, 1, '201', $4, 1)",
        std_sched_id,
        group_id,
        discipline_id,
        teacher_id,
    )

    ttable_id = (await conn.fetchrow(
        "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
        "VALUES ($1, $2, $3, $4, 'standard', false) RETURNING id",
        date.today(),
        ttable_statuses[0]["id"],
        building_id,
        user_id,
    ))["id"]

    hist_id = (await conn.fetchrow(
        "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
        "VALUES ($1, $2, $3, true, $4) RETURNING id",
        ttable_id,
        user_id,
        cards_statuses[1]["id"],  # edited
        group_id,
    ))["id"]

    await conn.execute(
        "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
        "VALUES ($1, $2, 1, '101', $3, $4, false)",
        hist_id,
        discipline_id,
        teacher_id,
        ttable_id,
    )

    return {
        "user_id": user_id,
        "group_id": group_id,
        "discipline_id": discipline_id,
        "teacher_id": teacher_id,
        "ttable_id": ttable_id,
        "hist_id": hist_id,
        "std_sched_id": std_sched_id,
    }


@pytest.fixture
async def db_seed():
    pool = await asyncpg.create_pool(
        user="postgres",
        password="pgdata",
        database=TEST_DB_NAME,
        host=env.pg_host,
        port=env.pg_port,
        max_size=10,
    )
    async with pool.acquire() as conn:
        seed_info = await _truncate_and_seed(conn)
    try:
        yield pool, seed_info
    finally:
        await pool.close()


@pytest.fixture
async def client(db_seed):
    pg_pool, seed_info = db_seed
    app = FastAPI()
    app.include_router(main_router)
    app.state.pg_pool = pg_pool
    app.state.seed_info = seed_info

    @app.middleware("http")
    async def add_state(request, call_next):
        request.state.role = Roles.methodist
        request.state.client_ip = "127.0.0.1"
        request.state.user_id = 1
        request.state.session_id = "test-session"
        return await call_next(request)

    async def override_pgsql():
        async with pg_pool.acquire() as conn:
            yield PgSql(conn)

    app.dependency_overrides[get_custom_pgsql] = override_pgsql
    app.dependency_overrides[JWTCookieDep] = lambda: None

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def seed_info(db_seed):
    return db_seed[1]


@pytest.fixture
def pg_pool(db_seed):
    return db_seed[0]
