from contextlib import asynccontextmanager

import uvicorn
from asyncpg import create_pool
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.api import main_router
from core.config_dir.config import pool_settings



@asynccontextmanager
async def lifespan(web_app):
    web_app.state.pg_pool = await create_pool(**pool_settings)
    try:
        yield
    finally:
        await web_app.state.pg_pool.close()

app = FastAPI(docs_url='/api/docs', openapi_url='/api/openapi.json', lifespan=lifespan)

app.include_router(main_router)

"Миддлвари"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)



if __name__ == '__main__':
    uvicorn.run('core.main:app', host="0.0.0.0", port=8000, log_config=None)
