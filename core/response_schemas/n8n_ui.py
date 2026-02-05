"""
Response схемы для n8n_ui endpoints.
Соответствует core/api/n8n_ui.py
"""

from typing import List, Any
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
class GroupDiffItem(BaseModel):
    """Элемент различия в группах."""
    name: str = Field(..., description="Название группы")


class TeacherDiffItem(BaseModel):
    """Элемент различия в преподавателях."""
    fio: str = Field(..., description="ФИО преподавателя")


class DisciplineDiffItem(BaseModel):
    """Элемент различия в дисциплинах."""
    title: str = Field(..., description="Название дисциплины")


class StdTtableCheckExistsResponse(BaseResponse):
    """
    Ответ для POST /private/n8n_ui/std_ttable/check_exists
    Проверка актуальности выгрузки данных из стандартного расписания.
    """
    diff_groups: List[GroupDiffItem] = Field(
        ...,
        description="Различия в группах",
        example=[
            {
                "name": "ИС-21-1"
            },
            {
                "name": "ПР-21-1"
            }
        ]
    )
    diff_teachers: List[TeacherDiffItem] = Field(
        ...,
        description="Различия в преподавателях",
        example=[
            {
                "fio": "Иванов И.И."
            },
            {
                "fio": "Петрова А.С."
            }
        ]
    )
    diff_disciplines: List[DisciplineDiffItem] = Field(
        ...,
        description="Различия в дисциплинах",
        example=[
            {
                "title": "Математика"
            },
            {
                "title": "Физика"
            }
        ]
    )


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
    "StdTtableCheckExistsResponse"
]