from contextlib import asynccontextmanager

import uvicorn
from asyncpg import create_pool
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from redis.asyncio import Redis
from starlette.middleware.cors import CORSMiddleware

from core.api import main_router
from core.api.elastic_search.api_elastic_search import init_elasticsearch_index
from core.api.middleware import AuthUXASGIMiddleware
from core.config_dir.config import pool_settings, env, es_settings, redis_settings


@asynccontextmanager
async def lifespan(web_app):
    """"""
    "Соединение с БД"
    web_app.state.pg_pool = await create_pool(**pool_settings)
    "Соединение с Эластиком"
    web_app.state.es_client = AsyncElasticsearch(**es_settings)
    "Соединение с Редисом"
    web_app.state.redis = Redis(**redis_settings, decode_responses=True)

    "Иниц. индекса в Elasticsearch"
    if env.es_init:
        await init_elasticsearch_index(["specs_index", "group_index"], web_app.state.pg_pool, web_app.state.es_client)
    try:
        yield
    finally:
        await web_app.state.pg_pool.close()
        await web_app.state.es_client.close()
        await web_app.state.redis.close()

app = FastAPI(
    docs_url='/api/docs',
    openapi_url='/api/openapi.json',
    lifespan=lifespan,
    response_model=env.post_processing_responses,
    response_model_exclude_unset=env.post_processing_responses
)

app.include_router(main_router)
# app.include_router(unnecessary_router)

"Миддлвари"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
app.add_middleware(AuthUXASGIMiddleware)


if __name__ == '__main__':
    uvicorn.run('core.main:app', host="0.0.0.0", port=8000, log_config=None)
