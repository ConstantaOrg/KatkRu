from fastapi import APIRouter, Depends
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.ttable_needs_schema import CreateTtableSchema, StdTtableSchema, ExtCardStateSchema
from core.utils.anything import Roles, TimetableVerStatuses
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter()

@router.post("/std_ttable/get_all", dependencies=[Depends(role_require(Roles.methodist))])
async def get_std_ttable2cards(body: StdTtableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    std_lessons = await db.n8n_ui.load_std_lessons_as_current(body.building_id, body.week_day, body.ttable_id, body.user_id)
    log_event(f"Загрузка стандартного расписания | building_id: {body.building_id}; sched_ver_id: {body.ttable_id}; user_id: {body.user_id}", request=request)
    return {'lessons': std_lessons}


@router.post("/ttable/create", dependencies=[Depends(role_require(Roles.methodist))])
async def create_ttable(body: CreateTtableSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    ttable_id = await db.ttable.create(body.building_id, body.date, body.type, TimetableVerStatuses.pending, request.state.user_id)
    log_event(
        f"Создана версия расписания | sched_ver_id: {ttable_id}; building_id: %s; type: {body.type}; назначено на {body.date}; user_id: {body.user_id}",
        request=request
    )
    return {'success': True, "ttable_id": ttable_id}


@router.post("/cards/get_by_id", dependencies=[Depends(role_require(Roles.methodist))])
async def create_ttable(body: ExtCardStateSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    records = await db.n8n_ui.get_ext_card(body.card_hist_id)
    log_event(f"Загрузка карточки расписания | card_hist_id: {body.card_hist_id}; user_id: {request.state.user_id}", request=request)
    return {'info': records}



