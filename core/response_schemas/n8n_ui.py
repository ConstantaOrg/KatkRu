"""
Response схемы для n8n_ui endpoints.
Соответствует core/api/n8n_ui.py
"""

from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field

from . import BaseResponse, SuccessResponse, SuccessWithIdResponse


# Модели для элементов данных (2-й уровень)
class StdLessonItem(BaseModel):
    """Элемент урока из стандартного расписания."""
    card_hist_id: int = Field(..., description="ID записи истории карточки")
    status_card: int = Field(..., description="Статус карточки")
    id: int = Field(..., description="ID группы")
    name: str = Field(..., description="Название группы")
    position: int = Field(..., description="Позиция урока (номер пары)")
    title: str = Field(..., description="Название дисциплины")
    is_force: bool = Field(False, description="Принудительное назначение")
    
    class Config:
        from_attributes = True


class LessonItem(BaseModel):
    """Элемент урока в расписании."""
    card_hist_id: int = Field(..., description="ID записи истории карточки")
    status_card: int = Field(..., description="Статус карточки")
    group_id: int = Field(..., description="ID группы")
    name: str = Field(..., description="Название группы")
    position: int = Field(..., description="Позиция урока (номер пары)")
    discipline_id: int = Field(..., description="ID дисциплины")
    title: str = Field(..., description="Название дисциплины")
    is_force: bool = Field(False, description="Принудительное назначение")
    
    class Config:
        from_attributes = True


class CardHistoryItem(BaseModel):
    """Элемент истории карточки."""
    card_hist_id: int = Field(..., description="ID записи истории карточки")
    created_at: Any = Field(..., description="Дата создания")
    user_id: int = Field(..., description="ID пользователя")
    user_name: str = Field(..., description="Имя пользователя")
    status_id: int = Field(..., description="ID статуса карточки")
    is_current: bool = Field(..., description="Является ли текущей версией")
    
    class Config:
        from_attributes = True


class ExtCardItem(BaseModel):
    """Элемент расширенной карточки."""
    position: int = Field(..., description="Позиция урока")
    teacher_name: str = Field(..., description="ФИО преподавателя")
    teacher_id: int = Field(..., description="ID преподавателя")
    aud: str = Field(..., description="Аудитория")
    
    class Config:
        from_attributes = True


class CardContentItem(BaseModel):
    """Элемент содержимого карточки."""
    position: int = Field(..., description="Позиция урока")
    aud: str = Field(..., description="Аудитория")
    discipline_id: int = Field(..., description="ID дисциплины")
    discipline_title: str = Field(..., description="Название дисциплины")
    teacher_id: int = Field(..., description="ID преподавателя")
    teacher_name: str = Field(..., description="ФИО преподавателя")
    
    class Config:
        from_attributes = True


class ConflictItem(BaseModel):
    """Элемент конфликта при сохранении."""
    teacher_id: int = Field(..., description="ID преподавателя")
    teacher_name: str = Field(..., description="ФИО преподавателя")
    position: int = Field(..., description="Позиция урока")
    existing_group: str = Field(..., description="Группа с которой конфликт")
    conflict_type: str = Field(..., description="Тип конфликта")


# Response схемы для простых эндпоинтов (1-2 уровня)
class TtableCreateResponse(SuccessWithIdResponse):
    """
    Ответ для POST /private/n8n_ui/ttable/create
    Результат создания новой версии расписания.
    """
    ttable_id: int = Field(
        ...,
        description="ID созданной версии расписания"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Версия расписания создана",
                "ttable_id": 42
            }
        }


class CardsAcceptResponse(SuccessResponse):
    """
    Ответ для PUT /private/n8n_ui/cards/accept
    Результат утверждения карточки.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Карточка утверждена!"
            }
        }


# Response схемы для средней сложности (2-3 уровня)
class StdTtableGetAllResponse(BaseResponse):
    """
    Ответ для POST /private/n8n_ui/std_ttable/get_all
    Возвращает уроки из стандартного расписания.
    """
    lessons: List[StdLessonItem] = Field(
        ...,
        description="Список уроков из стандартного расписания",
        example=[
            {
                "card_hist_id": 2,
                "status_card": 3,
                "id": 1,
                "name": "ИС-21-1",
                "position": 1,
                "title": "Математика",
                "is_force": False
            },
            {
                "card_hist_id": 3,
                "status_card": 3,
                "id": 2,
                "name": "ИС-21-1",
                "position": 2,
                "title": "Физика",
                "is_force": False
            }
        ]
    )


class CurrentTtableGetAllResponse(BaseResponse):
    """
    Ответ для POST /private/n8n_ui/current_ttable/get_all
    Возвращает карточки текущего расписания.
    """
    lessons: List[LessonItem] = Field(
        ...,
        description="Список карточек текущего расписания",
        example=[
            {
                "id": 10,
                "position": 1,
                "discipline_id": 5,
                "discipline_name": "Математика",
                "teacher_id": 3,
                "teacher_name": "Иванов И.И.",
                "group_id": 2,
                "group_name": "ИС-21-1",
                "auditorium": "101",
                "is_force": True
            }
        ]
    )


class CardsGetByIdResponse(BaseResponse):
    """
    Ответ для POST /private/n8n_ui/cards/get_by_id
    Возвращает расширенную информацию о карточке.
    """
    ext_card: List[ExtCardItem] = Field(
        ...,
        description="Расширенная информация о карточке (список элементов)",
        example=[
            {
                "position": 1,
                "teacher_name": "Иванов И.И.",
                "teacher_id": 1,
                "aud": "101"
            }
        ]
    )


class CardsHistoryResponse(BaseResponse):
    """
    Ответ для GET /private/n8n_ui/cards/history
    Возвращает историю изменений карточек.
    """
    history: List[CardHistoryItem] = Field(
        ...,
        description="История изменений карточек",
        example=[
            {
                "card_hist_id": 100,
                "created_at": "2024-01-15T10:30:00Z",
                "user_id": 1,
                "user_name": "Иванов И.И.",
                "status_id": 2,
                "is_current": True
            },
            {
                "card_hist_id": 99,
                "created_at": "2024-01-14T15:20:00Z",
                "user_id": 2,
                "user_name": "Петрова А.С.",
                "status_id": 1,
                "is_current": False
            }
        ]
    )


class CardsContentResponse(BaseResponse):
    """
    Ответ для GET /private/n8n_ui/cards/content
    Возвращает содержимое карточки.
    """
    card_content: List[CardContentItem] = Field(
        ...,
        description="Содержимое карточки",
        example=[
            {
                "position": 1,
                "aud": "101",
                "discipline_id": 1,
                "discipline_title": "Математика",
                "teacher_id": 1,
                "teacher_name": "Иванов И.И."
            },
            {
                "position": 2,
                "aud": "205",
                "discipline_id": 2,
                "discipline_title": "Физика",
                "teacher_id": 2,
                "teacher_name": "Петрова А.С."
            }
        ]
    )


# Response схемы для сложных эндпоинтов (до 3 уровней)
class DiffItem(BaseModel):
    """Элемент различия в данных."""
    id: int = Field(..., description="ID элемента")
    name: str = Field(..., description="Название элемента")
    status: str = Field(..., description="Статус различия (added/modified/removed/unchanged)")


class StdTtableCheckExistsResponse(BaseResponse):
    """
    Ответ для POST /private/n8n_ui/std_ttable/check_exists
    Проверка актуальности выгрузки данных из стандартного расписания.
    """
    diff_groups: List[DiffItem] = Field(
        ...,
        description="Различия в группах",
        example=[
            {
                "id": 1,
                "name": "ИС-21-1",
                "status": "added"
            },
            {
                "id": 2,
                "name": "ПР-21-1", 
                "status": "modified"
            }
        ]
    )
    diff_teachers: List[DiffItem] = Field(
        ...,
        description="Различия в преподавателях",
        example=[
            {
                "id": 3,
                "name": "Иванов И.И.",
                "status": "modified"
            },
            {
                "id": 4,
                "name": "Петрова А.С.",
                "status": "unchanged"
            }
        ]
    )
    diff_disciplines: List[DiffItem] = Field(
        ...,
        description="Различия в дисциплинах",
        example=[
            {
                "id": 5,
                "name": "Математика",
                "status": "unchanged"
            },
            {
                "id": 6,
                "name": "Новая дисциплина",
                "status": "added"
            }
        ]
    )


class CardsSaveSuccessResponse(SuccessWithIdResponse):
    """
    Успешный ответ для POST /private/n8n_ui/cards/save
    Когда карточка сохранена без конфликтов.
    """
    new_card_hist_id: int = Field(
        ...,
        description="ID новой записи истории карточки"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Карточка успешно сохранена",
                "new_card_hist_id": 150
            }
        }


class CardsSaveConflictResponse(BaseResponse):
    """
    Ответ с конфликтами для POST /private/n8n_ui/cards/save
    Когда при сохранении карточки возникли конфликты.
    """
    success: bool = Field(False, description="Флаг неуспешности операции")
    conflicts: List[ConflictItem] = Field(
        ...,
        description="Список конфликтов при сохранении",
        example=[
            {
                "teacher_id": 3,
                "teacher_name": "Иванов И.И.",
                "position": 2,
                "existing_group": "ИС-21-2",
                "conflict_type": "teacher_busy"
            },
            {
                "teacher_id": 4,
                "teacher_name": "Петрова А.С.",
                "position": 3,
                "existing_group": "ПР-21-1",
                "conflict_type": "auditorium_occupied"
            }
        ]
    )
    description: str = Field(
        ...,
        description="Описание проблемы",
        example="У этого преподавателя уже есть группа на эту пару"
    )


# Union тип для ответа cards/save - используем базовую схему
class CardsSaveResponse(BaseResponse):
    """
    Базовый ответ для POST /private/n8n_ui/cards/save
    Может содержать либо успех с new_card_hist_id, либо конфликты.
    """
    success: bool = Field(..., description="Флаг успешности операции")
    message: Optional[str] = Field(None, description="Сообщение о результате")
    new_card_hist_id: Optional[int] = Field(None, description="ID новой записи истории (при успехе)")
    conflicts: Optional[Dict[str, Any]] = Field(None, description="Информация о конфликтах (при неуспехе)")
    description: Optional[str] = Field(None, description="Описание проблемы (при неуспехе)")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "Карточка успешно сохранена",
                    "new_card_hist_id": 150
                },
                {
                    "success": False,
                    "conflicts": {
                        "columns": ["position", "teacher_id", "sched_ver_id"],
                        "values": [1, 1, 2]
                    },
                    "description": "У этого преподавателя уже есть группа на эту пару"
                }
            ]
        }


# Экспорт схем
__all__ = [
    "StdLessonItem",
    "LessonItem",
    "CardHistoryItem", 
    "CardContentItem",
    "ExtCardItem",
    "ConflictItem",
    "DiffItem",
    "TtableCreateResponse",
    "CardsAcceptResponse",
    "StdTtableGetAllResponse",
    "CurrentTtableGetAllResponse",
    "CardsGetByIdResponse",
    "CardsHistoryResponse",
    "CardsContentResponse",
    "StdTtableCheckExistsResponse",
    "CardsSaveResponse"
]