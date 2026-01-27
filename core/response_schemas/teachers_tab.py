"""
Response схемы для teachers endpoints.
Соответствует core/api/teachers_tab.py
"""

from typing import List, Dict, Any
from pydantic import Field

from . import BaseResponse, SuccessResponse, SuccessWithIdResponse


class TeachersGetResponse(BaseResponse):
    """
    Ответ для GET /private/teachers/get
    Возвращает список учителей с пагинацией.
    """
    teachers: List[Dict[str, Any]] = Field(
        ...,
        description="Список учителей",
        example=[
            {
                "id": 1,
                "fio": "Иванов Иван Иванович",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "disciplines_count": 3
            },
            {
                "id": 2,
                "fio": "Петрова Анна Сергеевна",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "disciplines_count": 2
            }
        ]
    )


class TeachersUpdateResponse(SuccessResponse):
    """
    Ответ для PUT /private/teachers/update
    Результат обновления статусов учителей.
    """
    active_upd_count: int = Field(
        ...,
        description="Количество учителей, переведенных в активное состояние"
    )
    depr_upd_count: int = Field(
        ...,
        description="Количество учителей, переведенных в неактивное состояние"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Учителя сменили статусы",
                "active_upd_count": 2,
                "depr_upd_count": 1
            }
        }


class TeachersAddResponse(SuccessWithIdResponse):
    """
    Ответ для POST /private/teachers/add
    Результат создания нового учителя.
    """
    teacher_id: int = Field(
        ...,
        description="ID созданного учителя"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Учитель успешно добавлен",
                "teacher_id": 15
            }
        }


# Экспорт схем
__all__ = [
    "TeachersGetResponse",
    "TeachersUpdateResponse",
    "TeachersAddResponse"
]