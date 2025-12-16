from typing import Literal

from fastapi import APIRouter
from starlette import status

from core.api.timetable.ttable_parser import ttable_doc_processer

router = APIRouter(prefix="/api/v1/timetable", tags=["Timetable📘"])


@router.post("/import")
async def upload_ttable_file(semester: int):
    """
    Будет полноценный файл-лоадер. Пока для алгоритма парсинга - путь принимает только
    """
    return ttable_doc_processer(semester=semester)
