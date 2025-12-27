from fastapi import HTTPException
from starlette.requests import Request


def role_require(*roles: str):
    async def checker(request: Request):
        cur_role = request.state.role

        "Проверка на соответствие указанным ролям"
        if cur_role not in set(roles):
            raise HTTPException(status_code=403, detail="Недостаточно прав")

    return checker