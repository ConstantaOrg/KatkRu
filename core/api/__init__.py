from fastapi import APIRouter
from .specialties import router as specialties_router
from .elastic_search import router as search_router

main_router = APIRouter()


main_router.include_router(specialties_router)
main_router.include_router(search_router)

@main_router.post('/healthcheck')
async def healthcheck():
    return {'status': 'ok', 'version': '0.1'}
