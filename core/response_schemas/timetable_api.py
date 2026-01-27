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
                "id": 1,
                "group_name": "ИС-21-1",
                "discipline": "Математика",
                "teacher": "Иванов И.И.",
                "auditorium": "101",
                "date": "2024-01-15",
                "time_start": "08:30",
                "time_end": "10:00",
                "lesson_type": "Лекция"
            },
            {
                "id": 2,
                "group_name": "ИС-21-1", 
                "discipline": "Физика",
                "teacher": "Петрова А.С.",
                "auditorium": "205",
                "date": "2024-01-15",
                "time_start": "10:15",
                "time_end": "11:45",
                "lesson_type": "Практика"
            }
        ]
    )


# Экспорт схем
__all__ = [
    "TimetableImportResponse",
    "TimetableGetResponse"
]