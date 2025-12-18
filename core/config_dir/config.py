import logging
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from docx.settings import Settings
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
from fastapi.params import Depends
from passlib.context import CryptContext
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.requests import Request

from core.config_dir.env_modes import AppMode, APP_MODE_CONFIG


environment_files = (
    os.getenv('ENV_FILE') or
    os.getenv('ENV_LOCAL_TEST_FILE') or
    '.env'
)
load_dotenv(environment_files, override=True)
logging.critical(f'\033[35m{environment_files}\033[0m | \033[33m{os.getenv("APP_MODE")}\033[0m')

WORKDIR = Path(__file__).resolve().parent.parent.parent

encryption = CryptContext(schemes=['argon2'], deprecated='auto')

@lru_cache
def get_pkey():
    return  (WORKDIR / 'secrets' / 'keys' / 'private_jwt.pem').read_text()

@lru_cache
def get_pubkey():
    return (WORKDIR / 'secrets' / 'keys' / 'public_jwt.pem').read_text()

class AuthConfig(BaseModel):
    private_key: str = get_pkey()
    public_key: str = get_pubkey()
    algorithm: str = 'RS256'
    ttl_aT: timedelta = timedelta(minutes=15)
    ttl_rT: timedelta = timedelta(days=30)
    ttl_wT: timedelta = timedelta(seconds=60)  # timedelta(seconds=15)


class Settings(BaseSettings):
    JWTs: AuthConfig = AuthConfig()

    pg_user: str
    pg_password: str
    pg_db: str
    pg_port: int
    pg_host: str

    pg_port_docker: int
    pg_host_docker: str

    redis_password: str
    redis_host: str
    redis_port: int
    redis_port_docker: int
    redis_host_docker: str

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
    allowed_ips: set[str] = {"172.25.0.1", "127.0.0.1"}
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

es_settings = get_elastic_settings(env)

async def get_elastic_client(request: Request):
    return request.app.state.es_client

ElasticDep = Annotated[AsyncElasticsearch, Depends(get_elastic_client)]


"Redis"
def get_redis_settings(envs: Settings):
    cfg = APP_MODE_CONFIG[envs.app_mode]

    redis_conf = {
        'host': getattr(envs, cfg['redis_host']),
        'port': getattr(envs, cfg['redis_port'])
    }
    if envs.app_mode != 'local':
        redis_conf['password'] = envs.redis_password


    return redis_conf

redis_settings = get_redis_settings(env)