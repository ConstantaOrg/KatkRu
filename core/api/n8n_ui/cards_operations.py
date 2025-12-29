from typing import Annotated

from fastapi import APIRouter, Depends, Query
from starlette.requests import Request
import json

from core.data.postgre import PgSqlDep
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.cards_schemas import SaveCardSchema
from core.schemas.n8n_ui.ttable_needs_schema import CreateTtableSchema, StdTtableSchema, ExtCardStateSchema
from core.utils.anything import Roles, TimetableVerStatuses
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter()

@router.post("/std_ttable/get_all", dependencies=[Depends(role_require(Roles.methodist))])
async def get_std_ttable2cards(body: StdTtableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    std_lessons = await db.n8n_ui.load_std_lessons_as_current(body.building_id, body.week_day, body.ttable_id, body.user_id)
    log_event(f"Загрузка стандартного расписания | building_id: {body.building_id}; sched_ver_id: \033[36m{body.ttable_id}\033[0m; user_id: \033[33m{body.user_id}\033[0m", request=request)
    return {'lessons': std_lessons}


@router.post("/ttable/create", dependencies=[Depends(role_require(Roles.methodist))])
async def create_ttable(body: CreateTtableSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    ttable_id = await db.ttable.create(body.building_id, body.date, body.type, TimetableVerStatuses.pending, request.state.user_id)
    log_event(
        f"Создана версия расписания | sched_ver_id: \033[36m{ttable_id}\033[0m; building_id: %s; type: \033[34m{body.type}\033[0m; назначено на \033[35m{body.date}\033[0m; user_id: \033[33m{body.user_id}\033[0m",
        request=request
    )
    return {'success': True, "ttable_id": ttable_id}


@router.post("/cards/get_by_id", dependencies=[Depends(role_require(Roles.methodist))])
async def create_ttable(body: ExtCardStateSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    records = await db.n8n_ui.get_ext_card(body.card_hist_id)
    log_event(f"Загрузка карточки расписания | card_hist_id: \033[31m{body.card_hist_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m", request=request)
    return {'ext_card': records}


@router.post("/cards/save", dependencies=[Depends(role_require(Roles.methodist))])
async def save_card(body: SaveCardSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    new_card_hist_id = await db.n8n_ui.save_card(body.card_hist_id, body.ttable_id, request.state.user_id, json.dumps([lesson.model_dump() for lesson in body.lessons], ensure_ascii=False))
    log_event(
        f"Сохранение карточки | new_card_hist_id: \033[31m{new_card_hist_id['id']}\033[0m; old_card_hist_id: \033[32m{body.card_hist_id}\033[0m; sched_ver_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",
        request=request
    )
    return {'success': True, 'new_card_hist_id': new_card_hist_id['id']}


@router.get("/cards/history", dependencies=[Depends(role_require(Roles.methodist))])
async def get_cards_history(
        sched_ver_id: Annotated[int, Query()],
        group_id: Annotated[int, Query()],
        db: PgSqlDep,
        request: Request,
        _: JWTCookieDep
):
    records = await db.n8n_ui.get_cards_history(sched_ver_id, group_id)
    log_event(
        f"История по расписанию для группы | sched_ver_id: \033[35m{sched_ver_id}\033[0m; group_id: \033[32m{group_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m; rows: \033[31m{len(records)}\033[0m",
        request=request
    )
    return {'history': records}


@router.get("/cards/content", dependencies=[Depends(role_require(Roles.methodist))])
async def get_card_content(card_hist_id: Annotated[int, Query()], db: PgSqlDep, request: Request, _: JWTCookieDep):
    records = await db.n8n_ui.get_card_content(card_hist_id)
    log_event(
        f"Выдали содержимое версии расписания | card_hist_id: \033[31m{card_hist_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m; всего содержимого: \033[31m{len(records)}\033[0m",
        request=request
    )
    return {'card_content': records}
