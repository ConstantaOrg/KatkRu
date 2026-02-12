"""
Response схемы для ttable versions endpoints.
Соответствует core/api/ttable_versions_tab.py
"""

from pydantic import ConfigDict

from . import SuccessResponse


class TtableVersionsCommitResponse(SuccessResponse):
    """
    Ответ для PUT /api/v1/private/n8n_ui/ttable/versions/commit
    Результат переключения версий расписания.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Версии переключены!"
            }
        })

# Экспорт схем
__all__ = [
    "TtableVersionsCommitResponse"
]