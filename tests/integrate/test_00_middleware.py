import pytest
import httpx
from fastapi import FastAPI

from core.api.middleware import AuthUXASGIMiddleware


@pytest.fixture
async def mw_client():
    app = FastAPI()

    @app.get("/api/v1/private/hello")
    async def private_hello():
        return {"ok": True}

    @app.get("/api/v1/public/hello")
    async def public_hello():
        return {"ok": True}

    app.add_middleware(AuthUXASGIMiddleware)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _headers_with_ip(ip: str):
    return {"X-Forwarded-For": ip}


@pytest.mark.asyncio
async def test_allowed_ip_passes_without_auth(mw_client):
    resp = await mw_client.get("/api/v1/private/hello")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_public_url_allows_without_tokens(mw_client):
    resp = await mw_client.get("/api/v1/public/hello", headers=_headers_with_ip("8.8.8.8"))
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_invalid_access_token_returns_401(mw_client):
    cookies = {"access_token": "invalid"}
    resp = await mw_client.get("/api/v1/private/hello", headers=_headers_with_ip("8.8.8.8"), cookies=cookies)
    assert resp.status_code == 401
    assert resp.json().get("message") == "Нужна повторная аутентификация"
