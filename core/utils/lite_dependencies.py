from fastapi import HTTPException
from starlette.requests import Request

from core.config_dir.config import env


def role_require(*roles: str):
    async def checker(request: Request):
        cur_role = request.state.role
        ip = request.state.client_ip

        "Проверка на соответствие указанным ролям"
        if ip not in env.allowed_ips and cur_role not in set(roles):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

    return checker