from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.ttable_needs_schema import CreateTtableSchema, StdTtableSchema
from core.utils.anything import Roles, TimetableVerStatuses
from core.utils.lite_dependencies import role_require

router = APIRouter()

@router.get("/std_ttable/get_all", dependencies=[Depends(role_require(Roles.methodist))])
async def get_std_ttable2cards(body: StdTtableSchema, db: PgSqlDep, _: JWTCookieDep):
    std_lessons = await db.n8n_ui.get_std_lessons(body.building_id, body.week_day)
    return {'lessons': std_lessons}


@router.post("/ttable/create", dependencies=[Depends(role_require(Roles.methodist))])
async def create_ttable(body: CreateTtableSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):

    ttable_id = await db.ttable.create(body.building_id, body.date, body.type, TimetableVerStatuses.pending, request.state.user_id)
    return {'success': True, "ttable_id": ttable_id}


