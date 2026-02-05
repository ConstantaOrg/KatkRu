"""
Тест для сравнения производительности и корректности работы
BaseHTTPMiddleware vs чистого ASGI middleware
"""
import time
import asyncio
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
from httpx import AsyncClient, ASGITransport
import pytest


# ============= Вариант 1: BaseHTTPMiddleware =============
class LoggingBaseHTTPMiddleware(BaseHTTPMiddleware):
    """Логирование через BaseHTTPMiddleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logs = []
    
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        
        response = await call_next(request)
        
        duration = time.perf_counter() - start
        
        self.logs.append({
            'method': request.method,
            'path': str(request.url.path),
            'status': response.status_code,
            'duration': round(duration, 4)
        })
        
        return response


# ============= Вариант 2: Чистый ASGI =============
class LoggingASGIMiddleware:
    """Логирование через чистый ASGI"""
    
    def __init__(self, app: ASGIApp):
        self.app = app
        self.logs = []
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        from starlette.requests import Request
        request = Request(scope, receive=receive)
        
        start = time.perf_counter()
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message['status']
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            
            self.logs.append({
                'method': request.method,
                'path': request.url.path,
                'status': status_code,
                'duration': round(duration, 4)
            })


# ============= Тестовые приложения =============
def create_app_with_basehttpmiddleware():
    """Приложение с BaseHTTPMiddleware"""
    app = FastAPI()
    middleware = LoggingBaseHTTPMiddleware(app)
    app.add_middleware(LoggingBaseHTTPMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.1)
        return {"message": "slow"}
    
    @app.get("/stream")
    async def stream_endpoint():
        async def generate():
            for i in range(5):
                yield f"chunk {i}\n".encode()
                await asyncio.sleep(0.01)
        return StreamingResponse(generate(), media_type="text/plain")
    
    @app.get("/error")
    async def error_endpoint():
        return JSONResponse({"error": "test"}, status_code=400)
    
    # Сохраняем ссылку на middleware для доступа к логам
    app.state.middleware = middleware
    return app


def create_app_with_asgi_middleware():
    """Приложение с чистым ASGI middleware"""
    app = FastAPI()
    middleware = LoggingASGIMiddleware(app)
    app.add_middleware(LoggingASGIMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.1)
        return {"message": "slow"}
    
    @app.get("/stream")
    async def stream_endpoint():
        async def generate():
            for i in range(5):
                yield f"chunk {i}\n".encode()
                await asyncio.sleep(0.01)
        return StreamingResponse(generate(), media_type="text/plain")
    
    @app.get("/error")
    async def error_endpoint():
        return JSONResponse({"error": "test"}, status_code=400)
    
    # Сохраняем ссылку на middleware для доступа к логам
    app.state.middleware = middleware
    return app


# ============= Тесты =============
@pytest.mark.asyncio
async def test_basehttpmiddleware_simple_request():
    """Тест BaseHTTPMiddleware - простой запрос"""
    app = create_app_with_basehttpmiddleware()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test")
    
    assert response.status_code == 200
    assert len(app.state.middleware.logs) == 1
    
    log = app.state.middleware.logs[0]
    assert log['method'] == 'GET'
    assert log['path'] == '/test'
    assert log['status'] == 200
    assert log['duration'] > 0
    
    print(f"✅ BaseHTTPMiddleware - простой запрос: {log}")


@pytest.mark.asyncio
async def test_asgi_middleware_simple_request():
    """Тест ASGI middleware - простой запрос"""
    app = create_app_with_asgi_middleware()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test")
    
    assert response.status_code == 200
    assert len(app.state.middleware.logs) == 1
    
    log = app.state.middleware.logs[0]
    assert log['method'] == 'GET'
    assert log['path'] == '/test'
    assert log['status'] == 200
    assert log['duration'] > 0
    
    print(f"✅ ASGI middleware - простой запрос: {log}")


@pytest.mark.asyncio
async def test_basehttpmiddleware_streaming():
    """Тест BaseHTTPMiddleware - streaming response"""
    app = create_app_with_basehttpmiddleware()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stream")
    
    assert response.status_code == 200
    assert b"chunk 0" in response.content
    assert len(app.state.middleware.logs) == 1
    
    log = app.state.middleware.logs[0]
    print(f"✅ BaseHTTPMiddleware - streaming: {log}")


@pytest.mark.asyncio
async def test_asgi_middleware_streaming():
    """Тест ASGI middleware - streaming response"""
    app = create_app_with_asgi_middleware()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stream")
    
    assert response.status_code == 200
    assert b"chunk 0" in response.content
    assert len(app.state.middleware.logs) == 1
    
    log = app.state.middleware.logs[0]
    print(f"✅ ASGI middleware - streaming: {log}")


@pytest.mark.asyncio
async def test_basehttpmiddleware_error_status():
    """Тест BaseHTTPMiddleware - error status code"""
    app = create_app_with_basehttpmiddleware()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/error")
    
    assert response.status_code == 400
    assert len(app.state.middleware.logs) == 1
    
    log = app.state.middleware.logs[0]
    assert log['status'] == 400
    print(f"✅ BaseHTTPMiddleware - error status: {log}")


@pytest.mark.asyncio
async def test_asgi_middleware_error_status():
    """Тест ASGI middleware - error status code"""
    app = create_app_with_asgi_middleware()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/error")
    
    assert response.status_code == 400
    assert len(app.state.middleware.logs) == 1
    
    log = app.state.middleware.logs[0]
    assert log['status'] == 400
    print(f"✅ ASGI middleware - error status: {log}")


@pytest.mark.asyncio
async def test_performance_comparison():
    """Сравнение производительности"""
    app_base = create_app_with_basehttpmiddleware()
    app_asgi = create_app_with_asgi_middleware()
    
    num_requests = 100
    
    # Тест BaseHTTPMiddleware
    start = time.perf_counter()
    async with AsyncClient(transport=ASGITransport(app=app_base), base_url="http://test") as client:
        tasks = [client.get("/test") for _ in range(num_requests)]
        await asyncio.gather(*tasks)
    base_duration = time.perf_counter() - start
    
    # Тест ASGI middleware
    start = time.perf_counter()
    async with AsyncClient(transport=ASGITransport(app=app_asgi), base_url="http://test") as client:
        tasks = [client.get("/test") for _ in range(num_requests)]
        await asyncio.gather(*tasks)
    asgi_duration = time.perf_counter() - start
    
    print(f"\n📊 Производительность ({num_requests} запросов):")
    print(f"   BaseHTTPMiddleware: {base_duration:.4f}s")
    print(f"   ASGI middleware:    {asgi_duration:.4f}s")
    print(f"   Разница:            {((base_duration - asgi_duration) / base_duration * 100):.2f}%")
    
    assert len(app_base.state.middleware.logs) == num_requests
    assert len(app_asgi.state.middleware.logs) == num_requests


if __name__ == "__main__":
    print("🧪 Запуск тестов сравнения middleware...\n")
    
    asyncio.run(test_basehttpmiddleware_simple_request())
    asyncio.run(test_asgi_middleware_simple_request())
    
    asyncio.run(test_basehttpmiddleware_streaming())
    asyncio.run(test_asgi_middleware_streaming())
    
    asyncio.run(test_basehttpmiddleware_error_status())
    asyncio.run(test_asgi_middleware_error_status())
    
    asyncio.run(test_performance_comparison())
    
    print("\n✅ Все тесты пройдены!")
