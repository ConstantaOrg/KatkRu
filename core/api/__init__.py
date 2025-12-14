from fastapi import APIRouter

main_router = APIRouter(prefix='/api')


@main_router.post('/healthcheck')
async def healthcheck():
    return {'status': 'ok', 'version': '0.1'}
