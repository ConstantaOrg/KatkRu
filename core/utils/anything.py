from dataclasses import dataclass
from pathlib import Path

from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config_dir.config import env

default_avatar = '/users/avatars/default_picture.png'

@dataclass
class TokenTypes:
    access_token: str = 'aT'
    refresh_token: str = 'rT'
    ws_token: str = 'wT'

token_types = {
    'access_token': 'aT',
    'refresh_token': 'rT',
    'ws_token': 'wT'
}

@dataclass
class TimetableTypes:
    standard: str = 'standard'
    replaces: str = 'replacements'

@dataclass
class TimetableVerStatuses:
    accepted: int = 1
    pending: int = 2

@dataclass
class Roles:
    methodist: str = 'methodist'
    read_all: str = 'read_all'

def hide_log_param(param, start=3, end=8):
    return param[:start] + '*' * len(param[start:-end-1]) + param[-end:]


def create_log_dirs():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)
    (LOG_DIR / 'info_warning_error').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'critical').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'debug').mkdir(exist_ok=True, parents=True)

def get_client_ip(request: Request | WebSocket):
    "Доверяем заголовку от клиента, в тестах маст-хев"  # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    xff = request.headers.get('X-Forwarded-For')
    ip = xff.split(',')[0].strip() if (
            xff and request.client.host in env.trusted_proxies
    ) else request.client.host
    return ip

# def get_client_ip(request: Request | WebSocket):
#     "При затирании XFF в Nginx"  # proxy_set_header X-Forwarded-For $remote_addr;
#     xff = request.headers.get('X-Forwarded-For')
#     ip = xff if (
#             xff and request.client.host in trusted_proxies
#     ) else request.client.host
#     return ip