"""
Пример того, как FastAPI генерирует OpenAPI схему для Union типов.

Swagger UI покажет все возможные варианты ответов с правильными схемами.
"""

from typing import Union, Literal
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.responses import JSONResponse


class SuccessResponse(BaseModel):
    success: Literal[True] = True
    data: dict = Field(..., description="Данные ответа")


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: str = Field(..., description="Сообщение об ошибке")
    code: int = Field(..., description="Код ошибки")


# Union тип для множественных ответов
ApiResponse = Union[SuccessResponse, ErrorResponse]

app = FastAPI(title="API с Union Response Types")


@app.post("/test-endpoint", response_model=ApiResponse)
async def test_endpoint(data: dict):
    """
    Эндпоинт с множественными типами ответов.
    
    Swagger автоматически покажет:
    - Schema для SuccessResponse (когда success=true)
    - Schema для ErrorResponse (когда success=false)
    - Примеры для каждого типа ответа
    """
    if data.get("valid"):
        return SuccessResponse(data={"result": "OK"})
    else:
        return ErrorResponse(error="Invalid data", code=400)


# Альтернативный способ - использование responses в декораторе
@app.post("/advanced-endpoint")
async def advanced_endpoint(data: dict):
    """
    Продвинутый способ с явным указанием статус кодов.
    
    Swagger покажет разные схемы для разных HTTP статусов.
    """
    if data.get("valid"):
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": {"result": "OK"}}
        )
    else:
        return JSONResponse(
            status_code=400, 
            content={"success": False, "error": "Invalid data", "code": 400}
        )


# Конфигурация responses для Swagger
@app.post(
    "/cards/save",
    responses={
        200: {
            "description": "Успешное сохранение или конфликт",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Успешное сохранение",
                            "value": {"success": True, "new_card_hist_id": 103}
                        },
                        "conflict": {
                            "summary": "Конфликт при сохранении", 
                            "value": {
                                "success": False,
                                "conflicts": {"position": 1, "teacher_id": 1},
                                "description": "Преподаватель занят"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def save_card_with_examples(payload: dict):
    """
    Эндпоинт с детальными примерами для Swagger.
    
    Swagger покажет:
    - Два примера ответов (success и conflict)
    - Правильные схемы для каждого случая
    - Описания для каждого сценария
    """
    # Логика эндпоинта...
    pass


if __name__ == "__main__":
    import uvicorn
    
    print("Swagger UI будет доступен по адресу: http://localhost:8000/docs")
    print("Там вы увидите правильные схемы для Union типов!")
    
    # uvicorn.run(app, host="0.0.0.0", port=8000)