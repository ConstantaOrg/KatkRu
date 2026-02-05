"""
Простой тест для сравнения BaseHTTPMiddleware vs ASGI middleware
"""
import time
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.requests import Request
from httpx import AsyncClient, ASGITransport


# Глобальные списки для логов
base_logs = []
asgi_logs = []


# ============= Вариант 1: BaseHTTPMiddleware =============
class LoggingBaseHTTPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        
        base_logs.append({
            'method': request.method,
            'path': str(request.url.path),
            'status': response.status_code,
            'duration': round(duration, 4)
        })
        
        return response


# ============= Вариант 2: Чистый ASGI =============
class LoggingASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
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
            asgi_logs.append({
                'method': request.method,
                'path': request.url.path,
                'status': status_code,
                'duration': round(duration, 4)
            })


# ============= Тестовые приложения =============
def create_base_app():
    app = FastAPI()
    app.add_middleware(LoggingBaseHTTPMiddleware)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    @app.get("/stream")
    async def stream():
        async def generate():
            for i in range(3):
                yield f"chunk {i}\n".encode()
        return StreamingResponse(generate())
    
    return app


def create_asgi_app():
    app = FastAPI()
    app.add_middleware(LoggingASGIMiddleware)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    @app.get("/stream")
    async def stream():
        async def generate():
            for i in range(3):
                yield f"chunk {i}\n".encode()
        return StreamingResponse(generate())
    
    return app


# ============= Тесты =============
async def test_base_simple():
    global base_logs
    base_logs = []
    
    app = create_base_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test")
    
    print(f"✅ BaseHTTPMiddleware - простой запрос:")
    print(f"   Status: {response.status_code}")
    print(f"   Logs: {base_logs}")
    assert len(base_logs) == 1
    assert base_logs[0]['status'] == 200


async def test_asgi_simple():
    global asgi_logs
    asgi_logs = []
    
    app = create_asgi_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test")
    
    print(f"✅ ASGI middleware - простой запрос:")
    print(f"   Status: {response.status_code}")
    print(f"   Logs: {asgi_logs}")
    assert len(asgi_logs) == 1
    assert asgi_logs[0]['status'] == 200


async def test_base_streaming():
    global base_logs
    base_logs = []
    
    app = create_base_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stream")
    
    print(f"✅ BaseHTTPMiddleware - streaming:")
    print(f"   Status: {response.status_code}")
    print(f"   Content: {response.content[:50]}")
    print(f"   Logs: {base_logs}")
    assert len(base_logs) == 1
    assert base_logs[0]['status'] == 200


async def test_asgi_streaming():
    global asgi_logs
    asgi_logs = []
    
    app = create_asgi_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stream")
    
    print(f"✅ ASGI middleware - streaming:")
    print(f"   Status: {response.status_code}")
    print(f"   Content: {response.content[:50]}")
    print(f"   Logs: {asgi_logs}")
    assert len(asgi_logs) == 1
    assert asgi_logs[0]['status'] == 200


async def test_performance():
    global base_logs, asgi_logs
    
    num_requests = 100
    
    # BaseHTTPMiddleware
    base_logs = []
    app_base = create_base_app()
    start = time.perf_counter()
    async with AsyncClient(transport=ASGITransport(app=app_base), base_url="http://test") as client:
        tasks = [client.get("/test") for _ in range(num_requests)]
        await asyncio.gather(*tasks)
    base_duration = time.perf_counter() - start
    
    # ASGI middleware
    asgi_logs = []
    app_asgi = create_asgi_app()
    start = time.perf_counter()
    async with AsyncClient(transport=ASGITransport(app=app_asgi), base_url="http://test") as client:
        tasks = [client.get("/test") for _ in range(num_requests)]
        await asyncio.gather(*tasks)
    asgi_duration = time.perf_counter() - start
    
    print(f"\n📊 Производительность ({num_requests} запросов):")
    print(f"   BaseHTTPMiddleware: {base_duration:.4f}s ({base_duration/num_requests*1000:.2f}ms/req)")
    print(f"   ASGI middleware:    {asgi_duration:.4f}s ({asgi_duration/num_requests*1000:.2f}ms/req)")
    
    if asgi_duration < base_duration:
        improvement = ((base_duration - asgi_duration) / base_duration * 100)
        print(f"   🚀 ASGI быстрее на:  {improvement:.2f}%")
    else:
        diff = ((asgi_duration - base_duration) / base_duration * 100)
        print(f"   ⚠️  ASGI медленнее на: {diff:.2f}%")
    
    assert len(base_logs) == num_requests
    assert len(asgi_logs) == num_requests


if __name__ == "__main__":
    print("🧪 Тест сравнения middleware\n")
    print("=" * 60)
    
    asyncio.run(test_base_simple())
    print()
    asyncio.run(test_asgi_simple())
    print()
    asyncio.run(test_base_streaming())
    print()
    asyncio.run(test_asgi_streaming())
    print()
    asyncio.run(test_performance())
    
    print("\n" + "=" * 60)
    print("✅ Все тесты пройдены!")
