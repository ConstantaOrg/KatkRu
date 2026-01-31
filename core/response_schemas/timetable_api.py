"""
Response схемы для timetable endpoints.
Соответствует core/api/timetable/timetable_api.py
"""

from typing import List, Dict, Any
from pydantic import Field

from . import BaseResponse, SuccessResponse


class TimetableImportResponse(SuccessResponse):
    """
    Ответ для POST /private/timetable/standard/import
    Результат импорта файла расписания.
    """
    ttable_ver_id: int = Field(
        ...,
        description="ID версии импортированного расписания"
    )
    status: str = Field(
        ...,
        description="Статус импортированного расписания"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Расписание сохранено",
                "ttable_ver_id": 123,
                "status": "В Ожидании"
            }
        }


class TimetableGetResponse(BaseResponse):
    """
    Ответ для POST /public/timetable/get
    Возвращает расписание по заданным фильтрам.
    """
    schedule: List[Dict[str, Any]] = Field(
        ...,
        description="Расписание занятий",
        example=[
            {
                "position": 1,
                "title": "Математика",
                "fio": "Иванов И.И.",
                "aud": "101"
            },
            {
                "position": 2,
                "title": "Физика",
                "fio": "Петрова А.С.",
                "aud": "205"
            }
        ]
    )


# Экспорт схем
__all__ = [
    "TimetableImportResponse",
    "TimetableGetResponse"
]