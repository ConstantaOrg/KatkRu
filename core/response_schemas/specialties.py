"""
Response схемы для specialties endpoints.
Соответствует core/api/specialties.py
"""

from typing import List, Dict, Any, Optional
from pydantic import Field

from . import BaseResponse


class SpecialtiesAllResponse(BaseResponse):
    """
    Ответ для POST /public/specialties/all
    Возвращает список всех специальностей с пагинацией.
    """
    specialties: List[Dict[str, Any]] = Field(
        ..., 
        description="Список специальностей",
        example=[
            {
                "id": 1,
                "name": "Информационные системы и программирование",
                "code": "09.02.07",
                "description": "Описание специальности"
            }
        ]
    )


class SpecialtyGetResponse(BaseResponse):
    """
    Ответ для GET /public/specialties/{spec_id}
    Возвращает детальную информацию об одной специальности.
    """
    speciality: Dict[str, Any] = Field(
        ...,
        description="Детальная информация о специальности",
        example={
            "id": 1,
            "name": "Информационные системы и программирование", 
            "code": "09.02.07",
            "description": "Подготовка специалистов в области разработки ПО",
            "duration_years": 3,
            "qualification": "Программист"
        }
    )


# Экспорт схем
__all__ = [
    "SpecialtiesAllResponse",
    "SpecialtyGetResponse"
]