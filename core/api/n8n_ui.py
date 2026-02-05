from typing import Annotated, Union

from fastapi import APIRouter, Depends, Query, Body
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.response_schemas.n8n_ui import (
    TtableCreateResponse, StdTtableGetAllResponse, StdTtableCheckExistsResponse,
    CurrentTtableGetAllResponse, CardsGetByIdResponse,
    CardsHistoryResponse, CardsContentResponse, CardsAcceptResponse
)
from core.utils.response_model_utils import (
    CardsSaveSuccessResponse, CardsSaveConflictResponse,
    create_cards_save_response, create_response_json
)
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.cards_schemas import SaveCardSchema
from core.schemas.n8n_ui.ttable_needs_schema import CreateTtableSchema, StdTtableSchema, ExtCardStateSchema, \
    SnapshotTtableSchema, StdTtableLoadSchema
from core.utils.anything import Roles, TimetableVerStatuses
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter(prefix='/private/n8n_ui', tags=['N8N UI📺'])



@router.post("/ttable/create", dependencies=[Depends(role_require(Roles.methodist))], response_model=TtableCreateResponse)
async def create_ttable(body: CreateTtableSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    ttable_id = await db.ttable.create(body.building_id, body.date, body.type, TimetableVerStatuses.pending, request.state.user_id)
    log_event(
        f"Создана версия расписания | sched_ver_id: \033[36m{ttable_id}\033[0m; building_id: %s; type: \033[34m{body.type}\033[0m; назначено на \033[35m{body.date}\033[0m; user_id: \033[33m{body.user_id}\033[0m",
        request=request
    )
    return {'success': True, "ttable_id": ttable_id}

@router.post("/std_ttable/get_all", dependencies=[Depends(role_require(Roles.methodist))], response_model=StdTtableGetAllResponse)
async def get_std_ttable2cards(body: StdTtableLoadSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    std_lessons = await db.n8n_ui.load_std_lessons_as_current(body.building_id, body.week_day, body.ttable_id, request.state.user_id)
    log_event(f"Загрузка стандартного расписания | building_id: {body.building_id}; sched_ver_id: \033[36m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m", request=request)
    return {'lessons': [dict(lesson) for lesson in std_lessons]}

@router.post("/std_ttable/check_exists", dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=StdTtableCheckExistsResponse)
async def check_actuality_of_layout(body: StdTtableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    resp_body = await db.n8n_ui.check_loaded_std_pairs(body.building_id, body.ttable_id)
    log_event(
        f"Проверка актуальности выгрузки данных из \033[35mstd_ttable\033[0m | diff_groups: \033[31m{len(resp_body['diff_groups'])}\033[0m; diff_teachers: \033[34m{len(resp_body['diff_teachers'])}\033[0m; diff_disciplines: \033[35m{len(resp_body['diff_disciplines'])}\033[0m",
        request=request, level='WARNING'
    )
    return resp_body

@router.post("/current_ttable/get_all", dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=CurrentTtableGetAllResponse)
async def get_std_ttable2cards(body: SnapshotTtableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    lessons_cards = await db.n8n_ui.get_cards(body.ttable_id)
    log_event(
        f"Отобразили версию расписания | sched_ver_id: \033[36m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",
        request=request
    )
    return {'lessons': [dict(lesson) for lesson in lessons_cards]}




@router.post("/cards/get_by_id", dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsGetByIdResponse)
async def create_ttable(body: ExtCardStateSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    records = await db.n8n_ui.get_ext_card(body.card_hist_id)
    log_event(f"Загрузка карточки расписания | card_hist_id: \033[31m{body.card_hist_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m", request=request)
    return {'ext_card': [dict(record) for record in records]}


@router.post("/cards/save", dependencies=[Depends(role_require(Roles.methodist))], responses={
    200: {"model": Union[CardsSaveSuccessResponse, CardsSaveConflictResponse], "description": "Card save result (success or conflict)"}
})
async def save_card(body: SaveCardSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    new_card_hist_id = await db.n8n_ui.save_card(body.card_hist_id, body.ttable_id, request.state.user_id, body.lessons)
    
    if isinstance(new_card_hist_id, int):
        log_event(
            f"Сохранение карточки Успешно! | new_card_hist_id: \033[31m{new_card_hist_id}\033[0m; old_card_hist_id: \033[32m{body.card_hist_id}\033[0m; sched_ver_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",
            request=request
        )
        response = create_cards_save_response(
            success=True,
            new_card_hist_id=new_card_hist_id
        )
        return create_response_json(response, status_code=200)

    log_event(
        f"Конфликты при сохранении карточки | conflicts: \033[31m{new_card_hist_id}\033[0m; old_card_hist_id: \033[32m{body.card_hist_id}\033[0m; sched_ver_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",
        request=request, level='WARNING'
    )
    response = create_cards_save_response(
        success=False,
        conflicts=new_card_hist_id,
        description="У этого преподавателя уже есть группа на эту пару"
    )
    return create_response_json(response, status_code=200)



@router.get("/cards/history", dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsHistoryResponse)
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
    return {'history': [dict(record) for record in records]}


@router.get("/cards/content", dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsContentResponse)
async def get_card_content(card_hist_id: Annotated[int, Query()], db: PgSqlDep, request: Request, _: JWTCookieDep):
    records = await db.n8n_ui.get_card_content(card_hist_id)
    log_event(
        f"Выдали содержимое версии расписания | card_hist_id: \033[31m{card_hist_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m; всего содержимого: \033[31m{len(records)}\033[0m",
        request=request
    )
    return {'card_content': [dict(record) for record in records]}

@router.put('/cards/accept', dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsAcceptResponse)
async def switch_card_status(card_hist_id: Annotated[int, Body(embed=True)], db: PgSqlDep, _: JWTCookieDep):
    await db.n8n_ui.accept_card(card_hist_id)
    return {'success': True, 'message': 'Карточка утверждена!'}
