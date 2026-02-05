"""
Response схемы для elastic search endpoints.
Соответствует core/api/api_elastic_search.py
"""

from typing import List, Dict, Any, Tuple
from pydantic import Field

from . import BaseResponse, SuccessResponse


class SearchResultItem(BaseResponse):
    """
    Элемент результата поиска.
    """
    id: str = Field(..., description="ID специальности")
    spec_code: str = Field(..., description="Код специальности")
    title: str = Field(..., description="Название специальности")


class AutocompleteSearchResponse(BaseResponse):
    """
    Ответ для POST /public/elastic/autocomplete_spec
    Быстрый поиск специальностей для автодополнения.
    """
    search_res: Tuple[SearchResultItem, ...] = Field(
        ...,
        description="Результаты поиска (до 5 элементов)",
        example=(
            {
                "id": "1",
                "spec_code": "09.02.07",
                "title": "Информационные системы и программирование"
            },
            {
                "id": "2", 
                "spec_code": "09.02.03",
                "title": "Программирование в компьютерных системах"
            }
        )
    )


class DeepSearchResponse(BaseResponse):
    """
    Ответ для POST /public/elastic/ext_spec
    Расширенный поиск специальностей с пагинацией.
    """
    search_res: Tuple[SearchResultItem, ...] = Field(
        ...,
        description="Результаты поиска с учетом пагинации",
        example=(
            {
                "id": "1",
                "spec_code": "09.02.07",
                "title": "Информационные системы и программирование"
            },
            {
                "id": "2",
                "spec_code": "09.02.03", 
                "title": "Программирование в компьютерных системах"
            },
            {
                "id": "3",
                "spec_code": "10.02.05",
                "title": "Обеспечение информационной безопасности"
            }
        )
    )


class ElasticInitResponse(SuccessResponse):
    """
    Ответ для инициализации Elasticsearch индекса.
    Используется внутренней функцией init_elasticsearch_index.
    """
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "Индекс specialties_index поднят, документы вставлены"
                },
                {
                    "success": False,
                    "message": "Индекс уже был создан и Проиндексирован"
                }
            ]
        }


# Экспорт схем
__all__ = [
    "SearchResultItem",
    "AutocompleteSearchResponse",
    "DeepSearchResponse",
    "ElasticInitResponse"
]