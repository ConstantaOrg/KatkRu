import time
from datetime import datetime
from typing import Callable

from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp, Send, Receive, Scope

from core.config_dir.config import env
from core.data.postgre import PgSql
from core.utils.anything import get_client_ip
from core.utils.jwt_factory import get_jwt_decode_payload, reissue_aT
from core.utils.logger import log_event


from starlette.background import BackgroundTask
from starlette.responses import Response as StarletteResponse, StreamingResponse


def create_logging_middleware(app_instance):
    """
    Создаёт middleware для логирования HTTP метрик
    Использует декоратор @app.middleware("http") для надёжной работы
    """
    @app_instance.middleware("http")
    async def logging_middleware(request: Request, call_next):
        # Устанавливаем client_ip
        ip = get_client_ip(request)
        request.state.client_ip = ip
        
        start = time.perf_counter()
        
        # Вызываем следующий middleware/endpoint
        response = await call_next(request)
        
        duration = time.perf_counter() - start
        
        # Если это StreamingResponse, нужно собрать chunks
        if isinstance(response, StreamingResponse):
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            res_body = b''.join(chunks)
            
            # Логируем в background task
            async def log_task():
                log_event(
                    f'HTTP {request.method} {request.url.path}',
                    request=request,
                    http_status=response.status_code,
                    response_time=round(duration, 4)
                )
                if duration > 7.0:
                    log_event(f'Долгий ответ | {duration: .4f}', request=request, level='WARNING')
            
            task = BackgroundTask(log_task)
            
            # Возвращаем новый Response
            return StarletteResponse(
                content=res_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=task
            )
        else:
            # Для обычных Response логируем сразу в background task
            async def log_task():
                log_event(
                    f'HTTP {request.method} {request.url.path}',
                    request=request,
                    http_status=response.status_code,
                    response_time=round(duration, 4)
                )
                if duration > 7.0:
                    log_event(f'Долгий ответ | {duration: .4f}', request=request, level='WARNING')
            
            task = BackgroundTask(log_task)
            
            # Добавляем task к существующим background tasks
            if hasattr(response, 'background') and response.background:
                # Если уже есть tasks, добавляем наш
                original_tasks = response.background
                response.background = BackgroundTask(lambda: None)  # Placeholder
                response.background.add_task(original_tasks)
                response.background.add_task(task)
            else:
                response.background = task
            
            return response


class AuthUXASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] not in {'http', 'websocket'}:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        now = datetime.utcnow()
        ip = get_client_ip(request)

        request.state.client_ip = ip
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
        request.state.role = access_token['role']
        await self.app(scope, receive, send)
