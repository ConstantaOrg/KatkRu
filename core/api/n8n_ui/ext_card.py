from typing import Annotated, Union

from fastapi import Depends, Query, Body, APIRouter, HTTPException
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.response_schemas.n8n_ui import CardsHistoryResponse, CardsGetByIdResponse, CardsContentResponse, \
    CardsAcceptResponse
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.cards_schemas import SaveCardSchema, BulkCardsSchema
from core.schemas.n8n_ui.ttable_needs_schema import ExtCardStateSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event
from core.utils.response_model_utils import create_response_json, CardsSaveSuccessResponse, CardsSaveConflictResponse, \
    create_cards_save_response

router = APIRouter(prefix="/cards")



@router.post("/get_by_id", dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsGetByIdResponse)
async def create_ttable(body: ExtCardStateSchema, db: PgSqlDep, request: Request, _ :JWTCookieDep):
    """Вызывается при нажатии на карточку/При переходе к изменению карточки-пар для группы"""
    records = await db.n8n_ui.get_ext_card(body.card_hist_id)
    log_event(f"Загрузка карточки расписания | card_hist_id: \033[31m{body.card_hist_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m", request=request)
    return {'ext_card': [dict(record) for record in records]}


@router.post("/save", dependencies=[Depends(role_require(Roles.methodist))], responses={
    200: {"model": Union[CardsSaveSuccessResponse, CardsSaveConflictResponse], "description": "Card save result (success or conflict)"}
})
async def save_card(body: SaveCardSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    """Сохранить карточку"""
    new_card_hist_id = await db.n8n_ui.save_card(body.card_hist_id, body.ttable_id, request.state.user_id, body.lessons)

    if not new_card_hist_id:
        log_event(f"Попытка изменить утверждённую версию расписания | old_card_hist_id: \033[32m{body.card_hist_id}\033[0m; sched_ver_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",request=request, level='WARNING')
        response = create_cards_save_response(
            success=False,
            conflicts={},
            description="Версия расписания уже утверждена, изменения запрещены"
        )
        return create_response_json(response, status_code=403)

    if isinstance(new_card_hist_id, int):
        log_event(f"Сохранение карточки Успешно! | new_card_hist_id: \033[31m{new_card_hist_id}\033[0m; old_card_hist_id: \033[32m{body.card_hist_id}\033[0m; sched_ver_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",request=request)
        response = create_cards_save_response(
            success=True,
            new_card_hist_id=new_card_hist_id
        )
        return create_response_json(response, status_code=200)

    log_event(f"Конфликты при сохранении карточки | conflicts: \033[31m{new_card_hist_id}\033[0m; old_card_hist_id: \033[32m{body.card_hist_id}\033[0m; sched_ver_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",request=request, level='WARNING')
    response = create_cards_save_response(
        success=False,
        conflicts=new_card_hist_id,
        description="У этого преподавателя уже есть группа на эту пару"
    )
    return create_response_json(response, status_code=200)



@router.get("/history", dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsHistoryResponse)
async def get_cards_history(
        sched_ver_id: Annotated[int, Query()],
        group_id: Annotated[int, Query()],
        db: PgSqlDep,
        request: Request,
        _: JWTCookieDep
):
    """Вкладка 'История' в окне редактирования карточки"""
    records = await db.n8n_ui.get_cards_history(sched_ver_id, group_id)
    log_event(f"История по расписанию для группы | sched_ver_id: \033[35m{sched_ver_id}\033[0m; group_id: \033[32m{group_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m; rows: \033[31m{len(records)}\033[0m",request=request)
    return {'history': [dict(record) for record in records]}


@router.get("/history_content", dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsContentResponse)
async def get_card_content(card_hist_id: Annotated[int, Query()], db: PgSqlDep, request: Request, _: JWTCookieDep):
    """Выведет содержимое из истории состояний карточки"""
    records = await db.n8n_ui.get_card_content(card_hist_id)
    log_event(f"Выдали содержимое версии расписания | card_hist_id: \033[31m{card_hist_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m; всего содержимого: \033[31m{len(records)}\033[0m",request=request)
    return {'card_content': [dict(record) for record in records]}


@router.put('/accept', dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsAcceptResponse)
async def switch_card_status(card_hist_id: Annotated[int, Body(embed=True)], db: PgSqlDep, _: JWTCookieDep, request: Request):
    """Поменять статус карточки на 'Утверждено'"""
    status, msg = await db.n8n_ui.accept_card(card_hist_id)
    if status == 409:
        log_event(f'Карточка не удовлетворяет условиям: \033[31m"{msg}"\033[0m', request=request, level='WARNING')
        raise HTTPException(status_code=409, detail=msg)
    if status == 403:
        log_event(f'Это расписание нельзя редактировать, так как оно уже утверждено', request=request, level='WARNING')
        raise HTTPException(status_code=403, detail=msg)
    log_event(f'Утвердили карточку \033[35m#{card_hist_id}\033[0m', request=request)
    return {'success': True, 'message': msg}


@router.put('/switch_as_edit', dependencies=[Depends(role_require(Roles.methodist))], response_model=CardsAcceptResponse)
async def switch_card_status(card_hist_id: Annotated[int, Body(embed=True)], db: PgSqlDep, _: JWTCookieDep, request: Request):
    """Поменять статус карточки на 'Редактировано'"""
    await db.n8n_ui.switch_as_edit(card_hist_id)
    log_event(f'Карточка \033[33m#{card_hist_id}\033[0m Теперь со статусом "Edit"', request=request)
    return {'success': True, 'message': f'Карточка {card_hist_id} теперь в статусе "Редактировано"'}


@router.post('/bulk_add', dependencies=[Depends(role_require(Roles.methodist))])
async def bulk_add_cards(body: BulkCardsSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    """Бульк вставка. Для вставки через UI и для вставки из буфера обмена (Ctrl + V)"""
    cards_ids, msg = await db.n8n_ui.bulk_add_cards(body.ttable_id, request.state.user_id, body.group_names, body.lessons)

    if cards_ids is None:
        log_event(f'Попытка добавить карточки в утверждённую версию | ttable_id: \033[35m{body.ttable_id}\033[0m; groups: {body.group_names}; user_id: \033[33m{request.state.user_id}\033[0m',request=request, level='WARNING')
        raise HTTPException(status_code=403, detail=msg)
    
    if msg:
        log_event(f'Не все группы найдены | ttable_id: \033[35m{body.ttable_id}\033[0m; error: \033[31m{msg}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m', request=request, level='WARNING')
        raise HTTPException(status_code=404, detail=msg)
    
    log_event(f'Добавили карточки | cards_ids: \033[33m{cards_ids}\033[0m; groups: {body.group_names}; ttable_id: \033[35m{body.ttable_id}\033[0m; user_id: \033[31m{request.state.user_id}\033[0m',request=request)
    return {'success': True, 'cards_ids': cards_ids}
