from fastapi import APIRouter
from .schedule_parse import router as schedule_parser_router

unnecessary_router = APIRouter(prefix='/no_need_api', tags=['No Need API'])


unnecessary_router.include_router(schedule_parser_router)