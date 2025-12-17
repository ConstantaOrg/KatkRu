from typing import Annotated

from asyncpg import Connection
from fastapi.params import Depends
from starlette.requests import Request

from core.data.sql_queries.specialties_sql import SpecsQueries
from core.data.sql_queries.ttable_sql import TimetableQueries


class PgSql:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.specialties = SpecsQueries(conn)
        self.ttable = TimetableQueries(conn)


async def get_pg_pool(request: Request):
    async with request.app.state.pg_pool.acquire() as conn:
        yield conn

async def get_custom_pgsql(conn: Annotated[Connection, Depends(get_pg_pool)]):
    yield PgSql(conn)

PgSqlDep = Annotated[PgSql, Depends(get_custom_pgsql)]
