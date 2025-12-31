from fastapi import APIRouter

from .n8n_ui import n8n_ui_router
from .specialties import router as specialties_router
from .elastic_search import router as search_router
from .timetable.timetable_api import router as timetable_router
from .users.users_api import router as users_router
from .groups_tab import router as groups_router
from .ttable_versions_tab import router as ttable_versions_router

main_router = APIRouter(prefix='/api/v1')


main_router.include_router(specialties_router)
main_router.include_router(search_router)
main_router.include_router(timetable_router)
main_router.include_router(users_router)
main_router.include_router(n8n_ui_router)
main_router.include_router(groups_router)
main_router.include_router(ttable_versions_router)

@main_router.post('/healthcheck')
async def healthcheck():
    return {'status': 'ok', 'version': '0.1'}
