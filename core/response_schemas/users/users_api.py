"""
Response схемы для users API endpoints.
Соответствует core/api/users/users_api.py
"""

from typing import List, Dict, Any
from pydantic import Field

from .. import BaseResponse, SuccessResponse


class UserRegistrationResponse(SuccessResponse):
    """
    Ответ для POST /server/users/sign_up
    Результат регистрации нового пользователя.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Пользователь добавлен"
            }
        }


class UserLoginResponse(SuccessResponse):
    """
    Ответ для POST /public/users/login
    Результат успешного входа в систему.
    Куки устанавливаются автоматически в заголовках ответа.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Куки у Юзера"
            }
        }


class UserLogoutResponse(SuccessResponse):
    """
    Ответ для PUT /private/users/logout
    Результат выхода из системы.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Пользователь вне аккаунта"
            }
        }


class UserSeancesResponse(BaseResponse):
    """
    Ответ для POST /private/users/seances
    Список всех активных сессий пользователя.
    """
    seances: List[Dict[str, Any]] = Field(
        ...,
        description="Список активных сессий пользователя",
        example=[
            {
                "session_id": "abc123",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "ip_address": "192.168.1.1",
                "created_at": "2024-01-01T10:00:00Z",
                "last_activity": "2024-01-01T12:00:00Z",
                "is_current": True
            },
            {
                "session_id": "def456", 
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
                "ip_address": "192.168.1.2",
                "created_at": "2024-01-01T09:00:00Z",
                "last_activity": "2024-01-01T11:30:00Z",
                "is_current": False
            }
        ]
    )


class UserPasswordResetResponse(SuccessResponse):
    """
    Ответ для PUT /server/users/passw/set_new_passw
    Результат сброса пароля пользователя.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Пароль обновлён!"
            }
        }


class UserAnyResponse(SuccessResponse):
    """
    Ответ для PUT /private/users/any
    Возвращает информацию о текущем пользователе и сессии.
    """
    user_id: int = Field(
        ...,
        description="ID текущего пользователя"
    )
    session_id: str = Field(
        ..., 
        description="ID текущей сессии"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "user_id": 123,
                "session_id": "abc123def456"
            }
        }


# Экспорт схем
__all__ = [
    "UserRegistrationResponse",
    "UserLoginResponse",
    "UserLogoutResponse", 
    "UserSeancesResponse",
    "UserPasswordResetResponse",
    "UserAnyResponse"
]