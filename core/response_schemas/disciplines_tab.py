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
        description="Список дисциплин (поле названо teachers из-за копирования кода)",
        example=[
            {
                "id": 1,
                "title": "Математика",
                "code": "MATH-101",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "title": "Физика",
                "code": "PHYS-101", 
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
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