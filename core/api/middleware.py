import time
from datetime import datetime
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp, Send, Receive, Scope

from core.config_dir.config import env
from core.data.postgre import PgSql
from core.schemas.cookie_settings_schema import AccToken
from core.utils.anything import get_client_ip
from core.utils.jwt_factory import get_jwt_decode_payload, reissue_aT
from core.utils.logger import log_event


class LoggingTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip = get_client_ip(request)
        request.state.client_ip = ip

        start = time.perf_counter()
        response = await call_next(request)
        end = time.perf_counter() - start
        if end > 7.0:
            log_event(f'Долгий ответ | {end: .4f}', request=request, level='WARNING')
        return response



class AuthUXMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        now = datetime.utcnow()
        request.state.user_id = 1
        request.state.session_id = '1'

        url = request.url.path
        "Обращения Сервера / Докер-сети"
        if request.state.client_ip in env.allowed_ips:
            return await call_next(request)

        "Не нуждаются в авторизации, Если юрл в белом списке"
        if any(url.startswith(prefix) for prefix in ('/api/v1/public', )):
            log_event("Публичный Юрл", request=request, level='WARNING')
            return await call_next(request)


        encoded_access_token = request.cookies.get('access_token')
        if (access_token:= get_jwt_decode_payload(encoded_access_token)) == 401:
            # невалидный аксес_токен
            log_event("Попытка подмены access_token", request=request, level='CRITICAL')
            return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
        if datetime.utcfromtimestamp(access_token['exp']) < now:
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
                return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
            request.state.new_a_t = new_token

        request.state.user_id = int(access_token['sub'])
        request.state.session_id = access_token['s_id']
        response = await call_next(request)

        "Проставляем access_token в ответе"
        if hasattr(request.state, 'new_a_t'):
            response.set_cookie('access_token', access_token, **AccToken().model_dump())

        return response



class AuthUXASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        now = datetime.utcnow()
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

        if datetime.utcfromtimestamp(access_token['exp']) < now:
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
        await self.app(scope, receive, send)
