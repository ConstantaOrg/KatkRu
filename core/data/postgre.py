from typing import Annotated, Optional, AsyncGenerator

from asyncpg import Connection, Pool, create_pool
from fastapi.params import Depends
from starlette.requests import Request

from core.config_dir.config import pool_settings
from core.data.sql_queries.n8n_iu_sql import N8NIUQueries
from core.data.sql_queries.specialties_sql import SpecsQueries
from core.data.sql_queries.ttable_sql import TimetableQueries
from core.data.sql_queries.users_sql import UsersQueries, AuthQueries


class PgSql:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.specialties = SpecsQueries(conn)
        self.ttable = TimetableQueries(conn)
        self.users = UsersQueries(conn)
        self.auth = AuthQueries(conn)
        self.n8n_ui = N8NIUQueries(conn)


connection: Optional[Pool] = None
async def set_connection():
    global connection
    if connection is None:
        connection = await create_pool(**pool_settings)
    return connection


async def set_session(request: Request) -> AsyncGenerator[Connection, None]:
    async with request.app.state.pg_pool.acquire() as session:
        yield session


async def get_pg_pool(request: Request):
    async with request.app.state.pg_pool.acquire() as conn:
        yield conn

async def get_custom_pgsql(conn: Annotated[Connection, Depends(get_pg_pool)]):
    yield PgSql(conn)

PgSqlDep = Annotated[PgSql, Depends(get_custom_pgsql)]
