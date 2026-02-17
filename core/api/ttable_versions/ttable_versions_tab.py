from typing import Annotated, Literal

from fastapi import APIRouter, Depends, UploadFile, Query
from starlette.requests import Request

from core.api.ttable_versions.ttable_parser import std_ttable_doc_processer
from core.data.postgre import PgSqlDep
from core.response_schemas.timetable_api import TimetableImportResponse
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.schemas2depends import PagenSchema
from core.schemas.ttable_schema import TtableVersionsGetSchema, PreAcceptTimetableSchema
from core.utils.anything import Roles
from core.utils.lite_dependencies import role_require
from core.utils.logger import log_event

router = APIRouter(prefix='/private/ttable/versions', tags=['Ttable Versions'])



@router.post('/get_all', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))])
async def get_all_versions(body: TtableVersionsGetSchema, pagen: PagenSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    ttable_versions = await db.ttable.filtered_layout(
        request.state.building_id, body.status_id, body.type, body.is_commited,
        body.schedule_date, body.date_sort, pagen.limit, pagen.offset
    )
    log_event(f'Отдали версии расписания. Фильтры: {repr(body)}; user_id: \033[31m{request.state.user_id}\033[0m; length: \033[32m{len(ttable_versions)}\033[0m', request=request)
    return {'ttable_versions': ttable_versions}


@router.post('/get_by_id', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))])
async def search_by_id(body: PreAcceptTimetableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    ttable_ver = await db.ttable.get_by_id(body.ttable_id, request.state.building_id)
    log_event(f'Нашли версию расписания | ttable_ver_id: \033[33m{ttable_ver.get("id") if ttable_ver else None}\033[0m; user_id: \033[31m{request.state.user_id}\033[0m; building_id: \033[35m{request.state.building_id}\033[0m', request=request)
    return {'ttable_version': ttable_ver}


@router.post('/replace/get_candidates', dependencies=[Depends(role_require(Roles.methodist, Roles.read_all))])
async def replace_candidates(body: PreAcceptTimetableSchema, db: PgSqlDep, request: Request, _: JWTCookieDep):
    ttable_candidates = await db.ttable.get_candidates_by_ver(body.ttable_id, request.state.building_id)
    log_event(f'Кандидаты для замены версии №\033[35m{body.ttable_id}\033[0m; length_candidates: \033[34m{len(ttable_candidates)}\033[0m ;user_id: \033[31m{request.state.user_id}\033[0m; building_id: \033[31m{request.state.building_id}\033[0m;', request=request)
    return {'ttable_candidates': ttable_candidates}


@router.post("/standard/import",  dependencies=[Depends(role_require(Roles.methodist))], response_model=TimetableImportResponse)
async def upload_ttable_file(
        file_obj: UploadFile,
        semester: Annotated[Literal["1", "2"], Query(alias='smtr')],
        request: Request,
        db: PgSqlDep,
        _: JWTCookieDep
):
    """
    Будет полноценный файл-лоадер.
    Есть ли смысл сохранять файлы в облако?
    """
    log_event(f'Обрабатываем документ со Стандартным Расписанием \033[34m{file_obj.filename}\033[0m', request=request)
    std_ttable = std_ttable_doc_processer(file_obj.file, semester=int(semester))

    log_event(f'Нормализуем данные \033[33m{file_obj.filename}\033[0m', request=request)
    inserted_ttable_id = await db.ttable.import_raw_std_ttable(std_ttable, request.state.building_id, request.state.user_id)

    return {'success': True, 'message': 'Расписание сохранено', 'ttable_ver_id': inserted_ttable_id, 'status': 'В Ожидании'}