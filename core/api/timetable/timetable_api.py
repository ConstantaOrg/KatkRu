from typing import Literal

from fastapi import APIRouter

from core.api.timetable.ttable_parser import ttable_doc_processer
from core.data.postgre import PgSqlDep
from core.schemas.ttable_schema import ScheduleFilterSchema

router = APIRouter(prefix="/api/v1", tags=["Timetable📘"])


@router.post("/private/timetable/import")
async def upload_ttable_file(semester: int):
    """
    Будет полноценный файл-лоадер. Пока для алгоритма парсинга - путь принимает только
    """
    return ttable_doc_processer(semester=semester)


@router.post("/public/timetable/get")
async def get_ttable_doc(body: ScheduleFilterSchema, db: PgSqlDep):
    schedule = await db.ttable.get_ttable(body.building_id, body.group, body.date_start, body.date_end)
    return {"schedule": schedule}