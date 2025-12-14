import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict

environment_files = (
    os.getenv('ENV_FILE') or
    os.getenv('ENV_LOCAL_TEST_FILE') or
    '.env'
)
logging.critical(f'\033[35m{environment_files}\033[0m')
load_dotenv(environment_files, override=True)

WORKDIR = Path(__file__).resolve().parent.parent


trusted_proxies = {'127.0.0.1', '172.25.0.1'}


class Settings(BaseSettings):
    pg_user: str
    pg_password: str
    pg_db: str
    pg_host: str
    pg_port: int

    trusted_proxies: list[str] = []

    model_config = SettingsConfigDict(extra='allow')


@lru_cache
def get_env_vars():
    return Settings()
env = get_env_vars()


pool_settings = dict(
    user=env.pg_user,
    database=env.pg_db,
    password=env.pg_password,
    host=env.pg_host,
    port=env.pg_port,
    command_timeout=60
)
