from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.response_schemas.disciplines_tab import (
    DisciplinesGetResponse, DisciplinesUpdateResponse, DisciplinesAddResponse
)
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.disciplines_schema import DisciplineUpdateSchema, DisciplineAddSchema
from core.schemas.schemas2depends import DisciplinesPagenSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter(prefix='/private/disciplines', tags=['Disciplines📚'])


@router.get('/get', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=DisciplinesGetResponse)
async def get_disciplines(pagen: DisciplinesPagenSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    teachers = await db.disciplines.get_all(pagen.limit, pagen.offset)
    log_event(f"Отобразили Учителей | user_id: \033[31m{request.state.user_id}\033[0m", request=request)
    return {'disciplines': teachers}

@router.put('/update', dependencies=[Depends(role_require(Roles.methodist))], response_model=DisciplinesUpdateResponse)
async def update_disciplines(body: DisciplineUpdateSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    active_upd_count, depr_upd_count = await db.disciplines.switch_status(body.set_as_active, body.set_as_deprecated)
    log_event(f'Обновили статусы Предметов | user_id: \033[31m{request.state.user_id}\033[0m | input: {body.model_dump()}', request=request)
    return {'success': True, 'message': "Дисциплины сменили статусы", 'active_upd_count': active_upd_count, 'depr_upd_count': depr_upd_count}


@router.post('/add', dependencies=[Depends(role_require(Roles.methodist))], response_model=DisciplinesAddResponse)
async def add_discipline(body: DisciplineAddSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    discipline_id = await db.disciplines.add(body.fio)
    if not discipline_id:
        log_event(f'Не удалось добавить предмет | user_id: \033[31m{request.state.user_id}\033[0m | title: \033[34m{body.title}\033[0m',
            request=request, level='WARNING')
        raise HTTPException(status_code=409, detail='Такой предмет уже есть')

    log_event(f'Обновили статусы группам | user_id: \033[31m{request.state.user_id}\033[0m | title, discipline_id: \033[34m{body.title}, {discipline_id}\033[0m', request=request)
    return {'success': True, 'discipline_id': discipline_id}

