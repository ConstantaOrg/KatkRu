from fastapi import APIRouter
from .main_ui import router as main_ui_router
from .ext_card import router as ext_card_router

n8n_ui_router = APIRouter(prefix='/private/n8n_ui', tags=['N8N UI📺'])

n8n_ui_router.include_router(main_ui_router)
n8n_ui_router.include_router(ext_card_router)
