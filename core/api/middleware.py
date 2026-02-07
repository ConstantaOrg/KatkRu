import time
from datetime import datetime, UTC

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Send, Receive, Scope

from core.config_dir.config import env
from core.data.postgre import PgSql
from core.utils.anything import get_client_ip
from core.utils.jwt_factory import get_jwt_decode_payload, reissue_aT
from core.utils.logger import log_event


class ASGILoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] not in {'http', 'websocket'}:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        
        ip = get_client_ip(request)
        request.state.client_ip = ip
        
        start = time.perf_counter()
        status_code = 500  # По умолчанию, если что-то пойдет не так
        
        async def send_wrapper(message):
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message['status']
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start

            "Логируем для мониторинга"
            if env.app_mode != 'local' and request.url.path != '/api/v1/healthcheck':
                log_event(f'HTTP \033[33m{request.method}\033[0m {request.url.path}', request=request, http_status=status_code, response_time=round(duration, 4))
            if duration > 7.0:
                log_event(f'Долгий ответ | {duration: .4f}', request=request, level='WARNING')


class AuthUXASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] not in {'http', 'websocket'}:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        now = datetime.now(UTC)

        request.state.role = 'student'
        request.state.user_id = 1
        request.state.session_id = '1'

        url = request.url.path
        "Обращения Сервера / Докер-сети"
        if request.state.client_ip in env.allowed_ips:
            await self.app(scope, receive, send)
            return

        "Не нуждаются в авторизации, Если юрл в белом списке"
        if any(url.startswith(prefix) for prefix in ('/api/v1/public', )):
            log_event("Публичный Юрл", request=request)
            await self.app(scope, receive, send)
            return


        encoded_access_token = request.cookies.get('access_token')
        if (access_token:= get_jwt_decode_payload(encoded_access_token)) == 401:
            # невалидный аксес_токен
            log_event("Попытка подмены access_token", request=request, level='CRITICAL')
            response =  JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
            await response(scope, receive, send)
            return

        if datetime.fromtimestamp(access_token['exp'], tz=UTC) < now:
            # аксес_токен ИСТЁК
            "процесс выпуска токена"
            async with request.app.state.pg_pool.acquire() as conn:
                db = PgSql(conn)
                refresh_token = request.cookies.get('refresh_token')
                new_token = await reissue_aT(access_token, refresh_token, db)

            if new_token == 401:
                # рефреш_токен НЕ ВАЛИДЕН
                log_event(f"Попытка подмены refresh_token | s_id: {access_token.get('s_id', '')}; user_id: {access_token.get('sub', '')}",
                          request=request, level='CRITICAL')
                response = JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
                await response(scope, receive, send)
                return

            request.state.new_a_t = new_token

        request.state.user_id = int(access_token['sub'])
        request.state.session_id = access_token['s_id']
        request.state.role = access_token['role']
        await self.app(scope, receive, send)
