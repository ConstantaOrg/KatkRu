from functools import wraps

from fastapi import HTTPException

from core.data.redis_storage import get_redis_connection
from core.utils.logger import log_event


def rate_limit(max_attempts: int, window_seconds: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or args[0]  # Получаем request
            client_ip = request.state.client_ip

            async with get_redis_connection() as redis:
                key = f"login_attempts:{client_ip}"
                attempts = await redis.get(key)

                if attempts and int(attempts) >= max_attempts:
                    log_event('Превышено количество ошибок входа в аккаунт', request=request, level='CRITICAL')
                    raise HTTPException(
                        status_code=429,
                        detail=f"Слишком много попыток входа от имени этого пользователя. Попробуйте позже"
                    )

                "Выполняем сам запрос"
                try:
                    result = await func(*args, **kwargs)
                    # Успешный логин - сбрасываем счетчик
                    await redis.delete(key)
                    return result
                except HTTPException as e:
                    if e.status_code == 401:
                        # Неудачная попытка - увеличиваем счетчик
                        await redis.incr(key)
                        await redis.expire(key, window_seconds)
                    raise

        return wrapper
    return decorator