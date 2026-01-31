"""
Пример использования @overload для типизации множественных ответов эндпоинта.

Это решает проблему с "лишними" полями в JSON ответах при наследовании
от базовых схем и обеспечивает точную типизацию для каждого сценария.
"""

from typing import overload, Union, Literal
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException


# Отдельные модели для каждого типа ответа (без наследования!)
class CardsSaveSuccessResponse(BaseModel):
    """Успешное сохранение карточки - только нужные поля."""
    success: Literal[True] = True
    new_card_hist_id: int = Field(..., description="ID новой записи истории карточки")


class CardsSaveConflictResponse(BaseModel):
    """Конфликт при сохранении - только нужные поля."""
    success: Literal[False] = False
    conflicts: dict = Field(..., description="Информация о конфликтах")
    description: str = Field(..., description="Описание проблемы")


# Union тип для FastAPI
CardsSaveResponse = Union[CardsSaveSuccessResponse, CardsSaveConflictResponse]


# Перегрузки для точной типизации в коде
@overload
def create_cards_save_response(
    success: Literal[True], 
    new_card_hist_id: int
) -> CardsSaveSuccessResponse: ...

@overload
def create_cards_save_response(
    success: Literal[False], 
    conflicts: dict, 
    description: str
) -> CardsSaveConflictResponse: ...

def create_cards_save_response(
    success: bool, 
    new_card_hist_id: int = None, 
    conflicts: dict = None, 
    description: str = None
) -> CardsSaveResponse:
    """
    Создает ответ для cards/save с точной типизацией.
    
    Благодаря @overload TypeScript/IDE точно знает какие поля будут в ответе
    в зависимости от значения success.
    """
    if success:
        return CardsSaveSuccessResponse(new_card_hist_id=new_card_hist_id)
    else:
        return CardsSaveConflictResponse(
            conflicts=conflicts, 
            description=description
        )


# Пример использования в FastAPI эндпоинте
app = FastAPI()

@app.post("/api/v1/private/n8n_ui/cards/save", response_model=CardsSaveResponse)
async def save_card(payload: dict):
    """
    Сохранение карточки с точной типизацией ответов.
    
    FastAPI автоматически сгенерирует правильную OpenAPI схему
    с Union типами для разных сценариев.
    """
    try:
        # Логика сохранения карточки
        if check_conflicts(payload):
            # Возвращаем только нужные поля для конфликта
            return create_cards_save_response(
                success=False,
                conflicts={"position": 1, "teacher_id": 1},
                description="У этого преподавателя уже есть группа на эту пару"
            )
        else:
            # Возвращаем только нужные поля для успеха
            new_id = save_to_database(payload)
            return create_cards_save_response(
                success=True,
                new_card_hist_id=new_id
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def check_conflicts(payload: dict) -> bool:
    """Проверка конфликтов (заглушка)."""
    return payload.get("position") == 1  # Простая логика для примера


def save_to_database(payload: dict) -> int:
    """Сохранение в БД (заглушка)."""
    return 103  # Возвращаем ID новой записи


# Пример для других эндпоинтов
class GroupsGetResponse(BaseModel):
    """Только нужные поля для списка групп."""
    groups: list[dict] = Field(..., description="Список групп")


class TtableVersionsPreCommitSuccessResponse(BaseModel):
    """Успешный pre-commit."""
    success: Literal[True] = True
    message: str = "Версия расписания готова к коммиту"


class TtableVersionsPreCommitConflictResponse(BaseModel):
    """Конфликт при pre-commit."""
    success: Literal[False] = False
    conflicts: list[dict] = Field(..., description="Список конфликтов")
    message: str = "Обнаружены конфликты"


# Union для pre-commit эндпоинта
TtableVersionsPreCommitResponse = Union[
    TtableVersionsPreCommitSuccessResponse,
    TtableVersionsPreCommitConflictResponse
]


@overload
def create_precommit_response(success: Literal[True]) -> TtableVersionsPreCommitSuccessResponse: ...

@overload
def create_precommit_response(
    success: Literal[False], 
    conflicts: list[dict]
) -> TtableVersionsPreCommitConflictResponse: ...

def create_precommit_response(
    success: bool, 
    conflicts: list[dict] = None
) -> TtableVersionsPreCommitResponse:
    """Создает ответ для pre-commit с точной типизацией."""
    if success:
        return TtableVersionsPreCommitSuccessResponse()
    else:
        return TtableVersionsPreCommitConflictResponse(conflicts=conflicts)


if __name__ == "__main__":
    # Демонстрация типизации
    
    # TypeScript/IDE точно знает, что здесь будет CardsSaveSuccessResponse
    success_response = create_cards_save_response(True, new_card_hist_id=103)
    print(f"Success: {success_response.new_card_hist_id}")  # IDE автодополнение работает!
    
    # TypeScript/IDE точно знает, что здесь будет CardsSaveConflictResponse  
    conflict_response = create_cards_save_response(
        False, 
        conflicts={"position": 1}, 
        description="Конфликт"
    )
    print(f"Conflict: {conflict_response.description}")  # IDE автодополнение работает!