from fastapi import APIRouter
from .cards_operations import router as cards_ops_router

n8n_ui_router = APIRouter(prefix='/private/n8n_ui', tags=['N8N UI📺'])

n8n_ui_router.include_router(cards_ops_router)