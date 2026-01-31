"""
Response схемы для groups endpoints.
Соответствует core/api/groups_tab.py
"""

from typing import List, Dict, Any
from pydantic import Field

from . import BaseResponse, SuccessResponse, SuccessWithIdResponse


class GroupsGetResponse(BaseResponse):
    """
    Ответ для GET /private/groups/get
    Возвращает список групп в указанном здании.
    """
    groups: List[Dict[str, Any]] = Field(
        ...,
        description="Список групп в здании",
        example=[
            {
                "id": 1,
                "name": "ИС-21-1",
                "is_active": True
            },
            {
                "id": 2, 
                "name": "ИС-21-2",
                "is_active": True
            }
        ]
    )


class GroupsUpdateResponse(SuccessResponse):
    """
    Ответ для PUT /private/groups/update
    Результат обновления статусов групп.
    """
    active_upd_count: int = Field(
        ...,
        description="Количество групп, переведенных в активное состояние"
    )
    depr_upd_count: int = Field(
        ...,
        description="Количество групп, переведенных в неактивное состояние"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Группы сменили статусы",
                "active_upd_count": 2,
                "depr_upd_count": 1
            }
        }


class GroupsAddResponse(SuccessWithIdResponse):
    """
    Ответ для POST /private/groups/add
    Результат создания новой группы.
    """
    group_id: int = Field(
        ...,
        description="ID созданной группы"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Группа успешно создана",
                "group_id": 123
            }
        }


# Экспорт схем
__all__ = [
    "GroupsGetResponse",
    "GroupsUpdateResponse", 
    "GroupsAddResponse"
]