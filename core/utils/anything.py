from pathlib import Path



def create_log_dirs():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)
    (LOG_DIR / 'info_warning_error').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'critical').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'debug').mkdir(exist_ok=True, parents=True)

from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config import trusted_proxies


def get_client_ip(request: Request | WebSocket):
    "Доверяем заголовку от клиента, в тестах маст-хев"  # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    xff = request.headers.get('X-Forwarded-For')
    ip = xff.split(',')[0].strip() if (
            xff and request.client.host in trusted_proxies
    ) else request.client.host
    return ip

# def get_client_ip(request: Request | WebSocket):
#     "При затирании XFF в Nginx"  # proxy_set_header X-Forwarded-For $remote_addr;
#     xff = request.headers.get('X-Forwarded-For')
#     ip = xff if (
#             xff and request.client.host in trusted_proxies
#     ) else request.client.host
#     return ip