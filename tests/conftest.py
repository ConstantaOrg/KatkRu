from datetime import date
import importlib
import os

import asyncpg
from asyncpg import InsufficientPrivilegeError
import httpx
import pytest
from fastapi import FastAPI

from core.config_dir import config as cfg
env = cfg.env
pool_settings = cfg.pool_settings

from core.api import main_router
from core.data.postgre import PgSql, get_custom_pgsql
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.utils.anything import Roles
from core.utils.logger import log_event


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    assert isinstance(env.pg_db, str), "env.pg_db is not set"
    assert env.pg_db.startswith("test_"), f"Refusing to run tests against non-test database: {env.pg_db}"



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
        status = "не выполнен"
    elif rep.failed:
        status = "упал"
    elif rep.skipped:
        status = "пропущен"
    else:
        status = "успешно"
    log_event(f"Завершение теста: {request.node.nodeid} | статус: {status}")


async def _truncate_and_seed(conn: asyncpg.Connection):
    tables_to_truncate = [
        "cards_states_details",
        "cards_states_history",
        "std_ttable",
        "ttable_versions",
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

    cards_status_rows = await conn.fetch(
        "INSERT INTO cards_statuses (title) VALUES ('accepted'), ('edited'), ('draft') RETURNING id, title"
    )
    cards_statuses = {row["title"]: row["id"] for row in cards_status_rows}
    ttable_status_rows = await conn.fetch(
        "INSERT INTO ttable_statuses (title) VALUES ('accepted'), ('pending') RETURNING id, title"
    )
    ttable_statuses = {row["title"]: row["id"] for row in ttable_status_rows}

    building_id = (
        await conn.fetchrow(
            "INSERT INTO buildings (address) VALUES ('Test address') RETURNING id"
        )
    )["id"]
    user_id = (
        await conn.fetchrow(
            "INSERT INTO users (name, email, passw, role, building_id) "
            "VALUES ('Test User', 'test@example.com', 'pass', 'methodist', $1) RETURNING id",
            building_id
        )
    )["id"]
    group_id = (
        await conn.fetchrow(
            "INSERT INTO groups (name, building_id, is_active) "
            "VALUES ('GR1', $1, true) RETURNING id",
            building_id,
        )
    )["id"]
    discipline_id = (
        await conn.fetchrow(
            "INSERT INTO disciplines (title) VALUES ('Math') RETURNING id"
        )
    )["id"]
    teacher_id = (
        await conn.fetchrow(
            "INSERT INTO teachers (fio) VALUES ('Иванов И.И.') RETURNING id"
        )
    )["id"]

    std_sched_id = (
        await conn.fetchrow(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'standard', true) RETURNING id",
            date.today(),
            ttable_statuses["accepted"],
            building_id,
            user_id,
        )
    )["id"]

    await conn.execute(
        "INSERT INTO std_ttable (sched_ver_id, group_id, discipline_id, position, aud, teacher_id, week_day) "
        "VALUES ($1, $2, $3, 1, '201', $4, 1)",
        std_sched_id,
        group_id,
        discipline_id,
        teacher_id,
    )

    ttable_id = (
        await conn.fetchrow(
            "INSERT INTO ttable_versions (schedule_date, status_id, building_id, user_id, type, is_commited) "
            "VALUES ($1, $2, $3, $4, 'standard', false) RETURNING id",
            date.today(),
            ttable_statuses["accepted"],
            building_id,
            user_id,
        )
    )["id"]

    hist_id = (
        await conn.fetchrow(
            "INSERT INTO cards_states_history (sched_ver_id, user_id, status_id, is_current, group_id) "
            "VALUES ($1, $2, $3, true, $4) RETURNING id",
            ttable_id,
            user_id,
            cards_statuses["edited"],
            group_id,
        )
    )["id"]

    # Добавляем 2 урока, чтобы карточка могла быть утверждена (минимум accept_card_constraint = 2)
    await conn.execute(
        "INSERT INTO cards_states_details (card_hist_id, discipline_id, position, aud, teacher_id, sched_ver_id, is_force) "
        "VALUES ($1, $2, 1, '101', $3, $4, false), ($1, $2, 2, '102', $3, $4, false)",
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
        "building_id": building_id,
        "cards_statuses": cards_statuses,
        "ttable_statuses": ttable_statuses,
    }


@pytest.fixture
async def db_seed():
    pool = await asyncpg.create_pool(**pool_settings, max_size=10)
    async with pool.acquire() as conn:
        seed_info = await _truncate_and_seed(conn)
    try:
        yield pool, seed_info
    finally:
        await pool.close()


@pytest.fixture
async def client(db_seed, aioes):
    pg_pool, seed_info = db_seed
    app = FastAPI()
    app.include_router(main_router)
    app.state.pg_pool = pg_pool
    app.state.seed_info = seed_info
    app.state.es_client = aioes  # Add Elasticsearch client to app state

    @app.middleware("http")
    async def add_state(request, call_next):
        request.state.role = Roles.methodist
        request.state.client_ip = "127.0.0.1"
        request.state.user_id = 1
        request.state.session_id = "test-session"
        # Используем test_building_id если установлен, иначе 1
        request.state.building_id = getattr(app.state, 'test_building_id', 1)
        return await call_next(request)

    async def override_pgsql():
        async with pg_pool.acquire() as conn:
            yield PgSql(conn)

    app.dependency_overrides[get_custom_pgsql] = override_pgsql
    app.dependency_overrides[JWTCookieDep] = lambda: None

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Сохраняем ссылку на app в клиенте
        ac.app = app
        yield ac


@pytest.fixture
def seed_info(db_seed):
    return db_seed[1]


@pytest.fixture
def pg_pool(db_seed):
    return db_seed[0]


@pytest.fixture
async def aioes():
    """
    Fixture providing AsyncElasticsearch client for testing.
    
    Creates a fresh Elasticsearch client instance for each test.
    The client is automatically closed after the test completes.
    """
    from elasticsearch import AsyncElasticsearch
    from core.config_dir.config import es_settings
    
    client = AsyncElasticsearch(**es_settings)
    try:
        yield client
    finally:
        await client.close()
