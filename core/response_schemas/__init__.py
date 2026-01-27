"""
Response схемы для API endpoints.
Все схемы для ответов API должны наследоваться от BaseResponse.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Базовый класс для всех ответов API."""
    
    class Config:
        # Разрешаем дополнительные поля для гибкости
        extra = "forbid"
        # Используем алиасы для полей
        populate_by_name = True


class SuccessResponse(BaseResponse):
    """Стандартный успешный ответ с булевым флагом и сообщением."""
    success: bool = Field(True, description="Флаг успешности операции")
    message: str = Field(..., description="Сообщение о результате операции")


class SuccessWithIdResponse(SuccessResponse):
    """Успешный ответ с ID созданного/обновленного ресурса."""
    # Поле id будет переопределено в наследниках с конкретным именем
    pass


class ListResponse(BaseResponse):
    """Базовый класс для ответов со списками данных."""
    total: Optional[int] = Field(None, description="Общее количество элементов")


class PaginatedListResponse(ListResponse):
    """Ответ для пагинированных списков."""
    limit: int = Field(..., description="Лимит элементов на странице")
    offset: int = Field(..., description="Смещение от начала списка")
    total: int = Field(..., description="Общее количество элементов")


class ErrorResponse(BaseResponse):
    """Стандартный ответ об ошибке."""
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Описание ошибки")
    details: Optional[List[dict]] = Field(None, description="Детали ошибки")


class ValidationErrorResponse(ErrorResponse):
    """Ответ при ошибке валидации."""
    error: str = Field("Validation Error", description="Тип ошибки")
    details: List[dict] = Field(..., description="Список ошибок валидации")


# Экспортируем основные классы
__all__ = [
    "BaseResponse",
    "SuccessResponse", 
    "SuccessWithIdResponse",
    "ListResponse",
    "PaginatedListResponse",
    "ErrorResponse",
    "ValidationErrorResponse"
]