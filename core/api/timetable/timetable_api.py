from typing import Annotated, Literal

from fastapi import APIRouter, UploadFile, Query, Request

from core.api.timetable.ttable_parser import std_ttable_doc_processer
from core.data.postgre import PgSqlDep
from core.response_schemas.timetable_api import TimetableImportResponse, TimetableGetResponse
from core.schemas.cookie_settings_schema import JWTCookieDep
from core.schemas.ttable_schema import ScheduleFilterSchema
from core.utils.logger import log_event

router = APIRouter(tags=["Timetable📘"])


@router.post("/private/timetable/standard/import", response_model=TimetableImportResponse)
async def upload_ttable_file(
        file_obj: UploadFile,
        semester: Annotated[Literal["1", "2"], Query(alias='smtr')],
        building_id: Annotated[int, Query(alias='bid')],
        request: Request,
        db: PgSqlDep,
        _: JWTCookieDep
):
    """
    Будет полноценный файл-лоадер. Пока для алгоритма парсинга - путь принимает только
    Есть ли смысл сохранять файлы в облако?
    """
    log_event(f'Обрабатываем документ со Стандартным Расписанием \033[34m{file_obj.filename}\033[0m', request=request)
    std_ttable = std_ttable_doc_processer(file_obj.file, semester=int(semester))

    log_event(f'Нормализуем данные \033[33m{file_obj.filename}\033[0m', request=request)
    inserted_ttable_id = await db.ttable.import_raw_std_ttable(std_ttable, building_id, request.state.user_id)

    return {'success': True, 'message': 'Расписание сохранено', 'ttable_ver_id': inserted_ttable_id, 'status': 'В Ожидании'}


@router.post("/public/timetable/get", response_model=TimetableGetResponse)
async def get_ttable_doc(body: ScheduleFilterSchema, db: PgSqlDep):
    schedule = await db.ttable.get_ttable(body.building_id, body.group, body.date_start, body.date_end)
    return {"schedule": [dict(item) for item in schedule]}