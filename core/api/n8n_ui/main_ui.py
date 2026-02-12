from fastapi import APIRouter, Depends
from starlette.requests import Request

from core.data.postgre import PgSqlDep
from core.response_schemas.n8n_ui import TtableCreateResponse, StdTtableGetAllResponse, StdTtableCheckExistsResponse, CurrentTtableGetAllResponse
from core.response_schemas.ttable_versions_tab import TtableVersionsCommitResponse
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.n8n_ui.ttable_needs_schema import CreateTtableSchema, StdTtableSchema, SnapshotTtableSchema, StdTtableLoadSchema
from core.schemas.ttable_schema import CommitTtableVersionSchema, PreAcceptTimetableSchema
from core.utils.anything import Roles, TimetableVerStatuses
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event
from core.utils.response_model_utils import (
    TtableVersionsPreCommitSuccessResponse, TtableVersionsPreCommitConflictResponse,
    create_ttable_precommit_response, create_response_json
)

router = APIRouter(prefix='/ttable', tags=['N8N UI📺'])



@router.post("/create", dependencies=[Depends(role_require(Roles.methodist))], response_model=TtableCreateResponse)
async def create_ttable(body: CreateTtableSchema, db: PgSqlDep, request: Request, _:JWTCookieDep):
    ttable_id = await db.ttable.create(request.state.building_id, body.date, body.type, TimetableVerStatuses.pending, request.state.user_id)
    log_event(
        f"Создана версия расписания | sched_ver_id: \033[36m{ttable_id}\033[0m; building_id: {request.state.building_id}; type: \033[34m{body.type}\033[0m; назначено на \033[35m{body.date}\033[0m; user_id: \033[33m{body.user_id}\033[0m",
        request=request
    )
    return {'success': True, "ttable_id": ttable_id}

@router.post("/std/get_all", dependencies=[Depends(role_require(Roles.methodist))], response_model=StdTtableGetAllResponse)
async def get_std_ttable2cards(body: StdTtableLoadSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    std_lessons = await db.n8n_ui.load_std_lessons_as_current(request.state.building_id, body.week_day, body.ttable_id, request.state.user_id)
    log_event(f"Загрузка стандартного расписания | building_id: {request.state.building_id}; sched_ver_id: \033[36m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m", request=request)
    return {'lessons': [dict(lesson) for lesson in std_lessons]}

@router.post("/std/check_exists", dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=StdTtableCheckExistsResponse)
async def check_actuality_of_layout(body: StdTtableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    resp_body = await db.n8n_ui.check_loaded_std_pairs(request.state.building_id, body.ttable_id)
    log_event(
        f"Проверка актуальности выгрузки данных из \033[35mstd_ttable\033[0m | diff_groups: \033[31m{len(resp_body['diff_groups'])}\033[0m; diff_teachers: \033[34m{len(resp_body['diff_teachers'])}\033[0m; diff_disciplines: \033[35m{len(resp_body['diff_disciplines'])}\033[0m",
        request=request, level='WARNING'
    )
    return resp_body

@router.post("/current/get_all", dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))], response_model=CurrentTtableGetAllResponse)
async def get_std_ttable2cards(body: SnapshotTtableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    lessons_cards = await db.n8n_ui.get_cards(body.ttable_id)
    log_event(
        f"Отобразили версию расписания | sched_ver_id: \033[36m{body.ttable_id}\033[0m; user_id: \033[33m{request.state.user_id}\033[0m",
        request=request
    )
    return {'lessons': [dict(lesson) for lesson in lessons_cards]}



@router.put("/versions/pre-commit", dependencies=[Depends(role_require(Roles.methodist))], responses={
    200: {"model": TtableVersionsPreCommitSuccessResponse, "description": "Timetable version ready for commit"},
    202: {"model": TtableVersionsPreCommitConflictResponse, "description": "Timetable version has conflicts with existing schedule"},
    409: {"model": TtableVersionsPreCommitConflictResponse, "description": "Missing groups in timetable version"}
})
async def pre_commit_ttable_version(body: PreAcceptTimetableSchema, db: PgSqlDep, _: JWTCookieDep):
    updating = await db.ttable.check_accept_constraints(body.ttable_id)
    
    if not updating:
        response = create_ttable_precommit_response(success=True)
        return create_response_json(response, status_code=200)
    
    status_code, error_data = updating
    response = create_ttable_precommit_response(
        success=False,
        needed_groups=error_data.get("needed_groups", []),
        ttable_id=body.ttable_id,
        message=error_data.get("message", "Conflicts detected in timetable version"),
        cur_active_ver=error_data.get("cur_active_ver"),
        pending_ver_id=error_data.get("pending_ver_id")
    )
    return create_response_json(response, status_code=status_code)


@router.put("/versions/commit", dependencies=[Depends(role_require(Roles.methodist))], response_model=TtableVersionsCommitResponse)
async def commit_ttable_version(body: CommitTtableVersionSchema, db: PgSqlDep, _: JWTCookieDep):
    await db.ttable.commit_version(body.pending_ver_id, body.target_ver_id)
    return {'success': True, 'message': 'Версии переключены!'}
