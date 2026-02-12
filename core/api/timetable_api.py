from fastapi import APIRouter, Request

from core.data.postgre import PgSqlDep
from core.response_schemas.timetable_api import TimetableGetResponse
from core.schemas.ttable_schema import ScheduleFilterSchema
from core.utils.logger import log_event

router = APIRouter(prefix='/public/ttable',tags=["Timetable📘"])


@router.post("/get", response_model=TimetableGetResponse)
async def get_ttable_doc(body: ScheduleFilterSchema, db: PgSqlDep, request: Request):
    schedule = await db.ttable.get_ttable(body.group, body.date_field)
    log_event(f'Отдали расписание студенту с параметрами: {repr(body)}', request=request)
    return {"schedule": [dict(item) for item in schedule]}