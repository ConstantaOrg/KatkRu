import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
from fastapi.params import Depends

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.config_dir.env_modes import AppMode, APP_MODE_CONFIG


environment_files = (
    os.getenv('ENV_FILE') or
    os.getenv('ENV_LOCAL_TEST_FILE') or
    '.env'
)
load_dotenv(environment_files, override=True)
logging.critical(f'\033[35m{environment_files}\033[0m | \033[33m{os.getenv("APP_MODE")}\033[0m')

WORKDIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    pg_user: str
    pg_password: str
    pg_db: str
    pg_port: int
    pg_host: str

    pg_port_docker: int
    pg_host_docker: str


    elastic_user: str
    elastic_password: str
    elastic_host: str
    elastic_host_docker: str
    elastic_port: int
    elastic_cert: str
    elastic_cert_docker: str

    search_index: str

    app_mode: AppMode
    es_init: bool
    trusted_proxies: set[str] =  {'127.0.0.1', '172.25.0.1'}

    model_config = SettingsConfigDict(extra='allow')


@lru_cache
def get_env_vars():
    return Settings()
env = get_env_vars()


"PostgreSQL"
def get_pg_settings(envs: Settings):
    cfg = APP_MODE_CONFIG[envs.app_mode]
    host = getattr(envs, cfg["pg_host"])
    port = getattr(envs, cfg["pg_port"])

    return {"host": host, "port": port}

pool_settings = dict(
    user=env.pg_user,
    database=env.pg_db,
    password=env.pg_password,
    **get_pg_settings(env),
    command_timeout=60
)


"ElasticSearch"
def get_elastic_settings(settings: Settings) -> dict:
    cfg = APP_MODE_CONFIG[settings.app_mode]

    host = getattr(settings, cfg["es_host"])
    cert = getattr(settings, cfg["es_cert"])
    scheme = cfg["es_scheme"]

    es_link = f"{scheme}://{host}:{settings.elastic_port}"
    es_settings = {
        "hosts": [es_link],
        # "basic_auth": (settings.elastic_user, settings.elastic_password),
        # "ca_certs": cert,
        # "verify_certs": False,
    }
    return es_settings


async def get_elastic_client():
    es_client = AsyncElasticsearch(**get_elastic_settings(env))
    try:
        yield es_client
    finally:
        await es_client.close()
ElasticDep = Annotated[AsyncElasticsearch, Depends(get_elastic_client)]