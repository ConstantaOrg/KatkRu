"""
Response схемы для ttable versions endpoints.
Соответствует core/api/ttable_versions_tab.py
"""

from pydantic import Field

from . import SuccessResponse


class TtableVersionsPreCommitResponse(SuccessResponse):
    """
    Ответ для PUT /private/ttable/versions/pre-commit
    Результат предварительного подтверждения версии расписания.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Расписание подтверждено и активно!"
            }
        }


class TtableVersionsCommitResponse(SuccessResponse):
    """
    Ответ для PUT /private/ttable/versions/commit
    Результат переключения версий расписания.
    """
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Версии переключены!"
            }
        }


# Экспорт схем
__all__ = [
    "TtableVersionsPreCommitResponse",
    "TtableVersionsCommitResponse"
]