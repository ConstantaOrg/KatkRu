"""
Response схемы для disciplines endpoints.
Соответствует core/api/disciplines_tab.py
"""

from typing import List, Dict, Any
from pydantic import Field

from . import BaseResponse, SuccessResponse, SuccessWithIdResponse


class DisciplinesGetResponse(BaseResponse):
    """
    Ответ для GET /private/disciplines/get
    Возвращает список дисциплин с пагинацией.
    """
    disciplines: List[Dict[str, Any]] = Field(
        ...,
        description="Список дисциплин",
        example=[
            {
                "id": 1,
                "title": "Математика",
                "is_active": True
            },
            {
                "id": 2,
                "title": "Физика",
                "is_active": True
            }
        ]
    )


class DisciplinesUpdateResponse(SuccessResponse):
    """
    Ответ для PUT /private/disciplines/update
    Результат обновления статусов дисциплин.
    """
    active_upd_count: int = Field(
        ...,
        description="Количество дисциплин, переведенных в активное состояние"
    )
    depr_upd_count: int = Field(
        ...,
        description="Количество дисциплин, переведенных в неактивное состояние"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Дисциплины сменили статусы",
                "active_upd_count": 3,
                "depr_upd_count": 1
            }
        }


class DisciplinesAddResponse(SuccessWithIdResponse):
    """
    Ответ для POST /private/disciplines/add
    Результат создания новой дисциплины.
    """
    discipline_id: int = Field(
        ...,
        description="ID созданной дисциплины"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Дисциплина успешно создана",
                "discipline_id": 42
            }
        }


# Экспорт схем
__all__ = [
    "DisciplinesGetResponse",
    "DisciplinesUpdateResponse",
    "DisciplinesAddResponse"
]