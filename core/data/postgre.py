from typing import Annotated

from asyncpg import Connection
from fastapi.params import Depends
from starlette.requests import Request


from core.data.sql_queries.disciplines_sql import DisciplinesQueries
from core.data.sql_queries.groups_sql import GroupsQueries
from core.data.sql_queries.n8n_iu_sql import N8NIUQueries
from core.data.sql_queries.specialties_sql import SpecsQueries
from core.data.sql_queries.teachers_sql import TeachersQueries
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
        self.groups = GroupsQueries(conn)
        self.teachers = TeachersQueries(conn)
        self.disciplines = DisciplinesQueries(conn)

async def get_pg_pool(request: Request):
    async with request.app.state.pg_pool.acquire() as conn:
        yield conn

async def get_custom_pgsql(conn: Annotated[Connection, Depends(get_pg_pool)]):
    yield PgSql(conn)

PgSqlDep = Annotated[PgSql, Depends(get_custom_pgsql)]
