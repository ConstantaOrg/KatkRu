from dataclasses import dataclass
from pathlib import Path

from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config_dir.config import env

default_avatar = '/users/avatars/default_picture.png'
accept_card_constraint = 2

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
    accepted: int = 1   # Утверждено
    pending: int = 2    # В ожидании

@dataclass
class CardsStatesStatuses:
    accepted: int = 1  # Утверждено
    edited: int = 2    # Редактировано
    draft: int = 3     # Не трогали

@dataclass
class Roles:
    methodist: str = 'methodist'
    read_all: str = 'read_all'

@dataclass
class ModuleNames:
    """Константы для названий модулей в генераторе документации."""
    specialties: str = 'specialties'
    groups: str = 'groups'
    teachers: str = 'teachers'
    disciplines: str = 'disciplines'
    timetable: str = 'timetable'
    users: str = 'users'
    n8n_ui: str = 'n8n_ui'
    elastic_search: str = 'elastic_search'
    ttable_versions: str = 'ttable_versions'

@dataclass
class HttpMethods:
    """Константы для HTTP методов."""
    GET: str = 'GET'
    POST: str = 'POST'
    PUT: str = 'PUT'
    DELETE: str = 'DELETE'
    PATCH: str = 'PATCH'

@dataclass
class ParameterLocations:
    """Константы для расположения параметров."""
    query: str = 'query'
    path: str = 'path'
    header: str = 'header'
    body: str = 'body'

@dataclass
class FieldTypes:
    """Константы для типов полей."""
    string: str = 'string'
    integer: str = 'integer'
    number: str = 'number'
    boolean: str = 'boolean'
    array: str = 'array'
    object: str = 'object'

@dataclass
class ModulePaths:
    """Пути к модулям для анализа зависимостей."""
    elastic_search: str = "core.api.elastic_search"
    n8n_ui: str = "core.api.n8n_ui"
    ttable_versions: str = "core.api.ttable_versions_tab"
    timetable: str = "core.api.timetable.timetable_api"
    users: str = "core.api.users.users_api"

def hide_log_param(param, start=3, end=8):
    return param[:start] + '*' * len(param[start:-end-1]) + param[-end:]


def create_log_dirs():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)

def get_client_ip(request: Request | WebSocket):
    "Доверяем заголовку от клиента, в тестах маст-хев"  # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    xff = request.headers.get('X-Forwarded-For')
    ip = xff.split(',')[0].strip() if (
            xff and request.client.host in env.trusted_proxies
    ) else request.client.host
    return ip

def extract_conflict_values(detail_str: str):
    bracket1, bracket2 = None, None
    need_vals = []
    for i, ch in enumerate(detail_str):
        if ch == '(':
            bracket1 = i + 1
            continue
        elif ch == ')':
            bracket2 = i
            continue

        if bracket1 and bracket2:
            need_vals.append(tuple(detail_str[bracket1:bracket2].split(',')))
            bracket1, bracket2 = None, None
    return need_vals



# def get_client_ip(request: Request | WebSocket):
#     "При затирании XFF в Nginx"  # proxy_set_header X-Forwarded-For $remote_addr;
#     xff = request.headers.get('X-Forwarded-For')
#     ip = xff if (
#             xff and request.client.host in trusted_proxies
#     ) else request.client.host
#     return ip