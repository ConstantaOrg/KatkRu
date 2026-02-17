"""
Тесты для критичных SQL методов авторизации.

Эти тесты покрывают:
- SQL методы для работы с пользователями и сессиями
- Очистку истекших refresh токенов  
- Получение пользователей по email
- Получение актуальных refresh токенов
"""
import pytest
from datetime import datetime, timedelta, UTC

from core.data.postgre import PgSql


async def test_slam_refresh_tokens_cleanup(db_seed):
    """
    Тест: очистка истекших refresh токенов из БД.
    
    Покрывает:
    - core/data/sql_queries/users_sql.py: slam_refresh_tokens
    """
    pg_pool, seed_info = db_seed
    user_id = seed_info["user_id"]
    now = datetime.now(UTC)
    
    # Добавляем истекший refresh токен
    async with pg_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            'expired-session',
            user_id,
            now - timedelta(days=2),
            now - timedelta(days=1),  # Истёк вчера
            'expired-token',
            'test-agent',
            '192.168.1.1'
        )
        
        # Добавляем валидный refresh токен
        await conn.execute(
            "INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            'valid-session',
            user_id,
            now,
            now + timedelta(days=7),  # Истечёт через неделю
            'valid-token',
            'test-agent',
            '192.168.1.1'
        )
        
        # Проверяем, что оба токена в БД
        count_before = await conn.fetchval("SELECT COUNT(*) FROM sessions_users WHERE user_id = $1", user_id)
        assert count_before == 2
        
        # Вызываем очистку
        db = PgSql(conn)
        await db.auth.slam_refresh_tokens()
        
        # Проверяем, что истекший токен удалён, а валидный остался
        count_after = await conn.fetchval("SELECT COUNT(*) FROM sessions_users WHERE user_id = $1", user_id)
        assert count_after == 1
        
        # Проверяем, что остался именно валидный токен
        remaining = await conn.fetchrow(
            "SELECT session_id FROM sessions_users WHERE user_id = $1",
            user_id
        )
        assert remaining['session_id'] == 'valid-session'


async def test_select_user_by_email(db_seed):
    """
    Тест: получение пользователя по email.
    
    Покрывает:
    - core/data/sql_queries/users_sql.py: select_user
    """
    pg_pool, seed_info = db_seed
    
    async with pg_pool.acquire() as conn:
        db = PgSql(conn)
        
        # Получаем существующего пользователя
        user = await db.users.select_user('test@example.com')
        assert user is not None
        assert user['id'] == seed_info["user_id"]
        assert user['role'] == 'methodist'
        assert user['building_id'] == seed_info["building_id"]
        assert 'passw' in user
        
        # Пытаемся получить несуществующего пользователя
        non_existent = await db.users.select_user('nonexistent@example.com')
        assert non_existent is None


async def test_get_actual_rt_valid_token(db_seed):
    """
    Тест: получение актуального refresh токена из БД.
    
    Покрывает:
    - core/data/sql_queries/users_sql.py: get_actual_rt
    """
    pg_pool, seed_info = db_seed
    user_id = seed_info["user_id"]
    now = datetime.now(UTC)
    
    async with pg_pool.acquire() as conn:
        # Добавляем валидный refresh токен
        await conn.execute(
            "INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            'test-session-rt',
            user_id,
            now,
            now + timedelta(days=7),
            'valid-refresh-token-123',
            'test-agent',
            '192.168.1.1'
        )
        
        # Получаем токен через метод
        db = PgSql(conn)
        result = await db.auth.get_actual_rt(user_id, 'test-session-rt')
        
        assert result is not None
        assert result['refresh_token'] == 'valid-refresh-token-123'


async def test_get_actual_rt_expired_token(db_seed):
    """
    Тест: истекший refresh токен не возвращается.
    
    Покрывает:
    - core/data/sql_queries/users_sql.py: get_actual_rt (проверка exp > now())
    """
    pg_pool, seed_info = db_seed
    user_id = seed_info["user_id"]
    now = datetime.now(UTC)
    
    async with pg_pool.acquire() as conn:
        # Добавляем истекший refresh токен
        await conn.execute(
            "INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            'expired-session-rt',
            user_id,
            now - timedelta(days=8),
            now - timedelta(days=1),  # Истёк вчера
            'expired-refresh-token-456',
            'test-agent',
            '192.168.1.1'
        )
        
        # Пытаемся получить истекший токен
        db = PgSql(conn)
        result = await db.auth.get_actual_rt(user_id, 'expired-session-rt')
        
        # Должен вернуться None, так как токен истёк
        assert result is None


async def test_get_actual_rt_nonexistent_session(db_seed):
    """
    Тест: несуществующая сессия возвращает None.
    
    Покрывает:
    - core/data/sql_queries/users_sql.py: get_actual_rt (сессия не найдена)
    """
    pg_pool, seed_info = db_seed
    user_id = seed_info["user_id"]
    
    async with pg_pool.acquire() as conn:
        db = PgSql(conn)
        result = await db.auth.get_actual_rt(user_id, 'nonexistent-session-id')
        
        # Должен вернуться None
        assert result is None
