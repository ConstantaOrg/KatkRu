from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.response_schemas.teachers_tab import (
    TeachersGetResponse, TeachersUpdateResponse, TeachersAddResponse
)
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.teachers_schema import TeachersAddSchema, TeachersUpdateSchema
from core.schemas.schemas2depends import TeachersPagenSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter(prefix='/private/teachers', tags=['Teachers👨‍🏫'])


@router.get('/get', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=TeachersGetResponse)
async def get_teachers(pagen: TeachersPagenSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    teachers = await db.teachers.get_all(pagen.limit, pagen.offset)
    log_event(f"Отобразили Учителей | user_id: \033[31m{request.state.user_id}\033[0m", request=request)
    return {'teachers': teachers}

@router.put('/update', dependencies=[Depends(role_require(Roles.methodist))], response_model=TeachersUpdateResponse)
async def update_teachers(body: TeachersUpdateSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    active_upd_count, depr_upd_count = await db.teachers.switch_status(body.set_as_active, body.set_as_deprecated)
    log_event(f'Обновили статусы Учителям | user_id: \033[31m{request.state.user_id}\033[0m | input: {body.model_dump()}', request=request)
    return {'success': True, 'message': "Учителя сменили статусы", 'active_upd_count': active_upd_count, 'depr_upd_count': depr_upd_count}


@router.post('/add', dependencies=[Depends(role_require(Roles.methodist))], response_model=TeachersAddResponse)
async def add_teacher(body: TeachersAddSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    teacher_id = await db.teachers.add(body.fio)
    if not teacher_id:
        log_event(f'Не удалось добавить учителя | user_id: \033[31m{request.state.user_id}\033[0m | fio: \033[34m{body.fio}\033[0m',
            request=request, level='WARNING')
        raise HTTPException(status_code=409, detail='Такой учитель уже добавлен')

    log_event(f'Обновили статусы группам | user_id: \033[31m{request.state.user_id}\033[0m | fio, teacher_id: \033[34m{body.fio}, {teacher_id}\033[0m', request=request)
    return {'success': True, 'teacher_id': teacher_id}

