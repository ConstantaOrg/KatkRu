from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Body, Query
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.cards_schemas import GroupAddSchema, GroupUpdateSchema
from core.schemas.schemas2depends import GroupPagenDep
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter(prefix='/private/groups', tags=['Groups👥👥👥'])


@router.get('/get', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))])
async def get_groups(building_id: Annotated[int, Query(alias='bid')], pagen: GroupPagenDep, db: PgSqlDep, request: Request, _: JWTCookieDep):
    groups = await db.groups.get_all(building_id, pagen.limit, pagen.offset)
    log_event(f"Отобразили группы | user_id: \033[31m{request.state.user_id}\033[0m", request=request)
    return {'groups': groups}

@router.put('/update', dependencies=[Depends(role_require(Roles.methodist))])
async def get_groups(body: GroupUpdateSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    active_upd_count, depr_upd_count = await db.groups.switch_status(body.set_as_active, body.set_as_deprecated)
    log_event(f'Обновили статусы группам | user_id: \033[31m{request.state.user_id}\033[0m | input: {body.model_dump()}', request=request)
    return {'success': True, 'message': "Группы сменили статусы", 'active_upd_count': active_upd_count, 'depr_upd_count': depr_upd_count}


@router.put('/add', dependencies=[Depends(role_require(Roles.methodist))])
async def get_groups(body: GroupAddSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    group_id = await db.groups.add(body.group_name, body.building_id)
    if not group_id:
        log_event(f'Не удалось создать группу статусы группам | user_id: \033[31m{request.state.user_id}\033[0m | group_name: \033[34m{body.group_name}\033[0m',
            request=request, level='WARNING')
        raise HTTPException(status_code=409, detail='Группа с таким названием в этом здании уже существует')

    log_event(f'Обновили статусы группам | user_id: \033[31m{request.state.user_id}\033[0m | group_name, group_id: \033[34m{body.group_name}, {group_id['id']}\033[0m', request=request)
    return {'success': True, 'group_id': group_id['id']}

