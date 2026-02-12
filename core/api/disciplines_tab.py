from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Body
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.response_schemas.disciplines_tab import (
    DisciplinesGetResponse, DisciplinesUpdateResponse
)
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.disciplines_schema import DisciplineUpdateSchema, DisciplineAddSchema, DisciplineFilterSchema, \
    Group2DisciplineSchema
from core.schemas.schemas2depends import DisciplinesPagenSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event
from core.utils.response_model_utils import (
    DisciplinesAddSuccessResponse, DisciplinesAddConflictResponse,
    create_disciplines_add_response, create_response_json
)

router = APIRouter(prefix='/private/disciplines', tags=['Disciplines📚'])


@router.post('/get', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=DisciplinesGetResponse)
async def get_disciplines(body: DisciplineFilterSchema, pagen: DisciplinesPagenSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    disciplines = await db.disciplines.get_all(body.is_active, body.group_name, pagen.limit, pagen.offset)
    log_event(f"Отобразили Дисциплины | фильтры: \033[33m{repr(body)}\033[0m;user_id: \033[31m{request.state.user_id}\033[0m", request=request)
    return {'disciplines': [dict(discipline) for discipline in disciplines]}

@router.put('/update', dependencies=[Depends(role_require(Roles.methodist))], response_model=DisciplinesUpdateResponse)
async def update_disciplines(body: DisciplineUpdateSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    active_upd_count, depr_upd_count = await db.disciplines.switch_status(body.set_as_active, body.set_as_deprecated)
    log_event(f'Обновили статусы Предметов | user_id: \033[31m{request.state.user_id}\033[0m | input: {body.model_dump()}', request=request)
    return {'success': True, 'message': "Дисциплины сменили статусы", 'active_upd_count': active_upd_count, 'depr_upd_count': depr_upd_count}


@router.post('/add', responses={
    200: {"model": DisciplinesAddSuccessResponse, "description": "Discipline added successfully"},
    409: {"model": DisciplinesAddConflictResponse, "description": "Discipline already exists"}
}, dependencies=[Depends(role_require(Roles.methodist))])
async def add_discipline(body: DisciplineAddSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    discipline_id = await db.disciplines.add(body.title)
    if not discipline_id:
        log_event(f'Не удалось добавить предмет | user_id: \033[31m{request.state.user_id}\033[0m | title: \033[34m{body.title}\033[0m',
            request=request, level='WARNING')
        response = create_disciplines_add_response(success=False)
        return create_response_json(response, status_code=409)

    log_event(f'Добавили дисциплину | user_id: \033[31m{request.state.user_id}\033[0m | title, discipline_id: \033[34m{body.title}, {discipline_id}\033[0m', request=request)
    response = create_disciplines_add_response(success=True, discipline_id=discipline_id)
    return create_response_json(response, status_code=200)


@router.post('/get_relations', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))])
async def show_relations(discipline_id: Annotated[int, Body(embed=True)], db: PgSqlDep, request: Request, _: JWTCookieDep):
    g2d_relas = await db.disciplines.get_relations(discipline_id)
    log_event(f'Отобразили связи g2d для discipline_id \033[35m{discipline_id}\033[0m', request=request)
    return {'group_relations': g2d_relas}

@router.post('/add_relation', dependencies=[Depends(role_require(Roles.methodist))])
async def g2d_relation(body: Group2DisciplineSchema, request: Request, db: PgSqlDep, _: JWTCookieDep):
    status_code, message = await db.disciplines.add_relations_g2d(body.discipline_id, body.group_name)
    if status_code == 400:
        log_event(f'Несуществующая группа | фильтры \033[34m{repr(body)}\033[0m', request=request, level='WARNING')
        raise HTTPException(status_code=400, detail=message)
    if status_code == 409:
        log_event(f'Попытка добавить существующую связку | фильтры \033[34m{repr(body)}\033[0m', request=request)
        raise HTTPException(status_code=409, detail=message)

    log_event(f'Создали связку | фильтры \033[34m{repr(body)}\033[0m', request=request)
    return {'success': True, 'message': message}
