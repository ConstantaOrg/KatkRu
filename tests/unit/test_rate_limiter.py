"""
Unit tests for rate limiter decorator.

Tests the rate_limit decorator directly without going through HTTP/ASGI,
ensuring that the rate limiting logic works correctly with Redis.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from core.api.users.rate_limiter import rate_limit


class MockRequest:
    """Mock request object for testing."""
    def __init__(self, client_ip: str = "127.0.0.1"):
        self.state = Mock()
        self.state.client_ip = client_ip


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_under_limit(flush_redis):
    """
    Test that rate limiter allows requests when under the limit.
    
    Should allow up to max_attempts (5) failed requests without blocking.
    """
    @rate_limit(max_attempts=5, window_seconds=300)
    async def mock_login(request):
        # Simulate failed login by raising 401
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    request = MockRequest(client_ip="192.168.1.100")
    
    # First 5 attempts should be allowed (but fail with 401)
    for attempt in range(1, 6):
        with pytest.raises(HTTPException) as exc_info:
            await mock_login(request)
        
        assert exc_info.value.status_code == 401, f"Attempt {attempt} should return 401"
        
        # Check Redis counter
        key = f"login_attempts:{request.state.client_ip}"
        counter = await flush_redis.get(key)
        assert counter == str(attempt), f"Counter should be {attempt} after attempt {attempt}"


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit_exceeded(flush_redis):
    """
    Test that rate limiter blocks requests after exceeding the limit.
    
    After max_attempts (5) failed requests, the 6th request should be blocked with 429.
    """
    @rate_limit(max_attempts=5, window_seconds=300)
    async def mock_login(request):
        # Simulate failed login
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    request = MockRequest(client_ip="192.168.1.101")
    
    # Make 5 failed attempts
    for _ in range(5):
        with pytest.raises(HTTPException) as exc_info:
            await mock_login(request)
        assert exc_info.value.status_code == 401
    
    # 6th attempt should be blocked with 429
    with pytest.raises(HTTPException) as exc_info:
        await mock_login(request)
    
    assert exc_info.value.status_code == 429, "6th attempt should return 429"
    assert "Слишком много попыток" in exc_info.value.detail


@pytest.mark.asyncio
async def test_rate_limiter_resets_on_successful_login(flush_redis):
    """
    Test that rate limiter resets counter after successful login.
    
    After a successful login, the counter should be reset to 0.
    """
    @rate_limit(max_attempts=5, window_seconds=300)
    async def mock_login(request, should_succeed: bool = False):
        if should_succeed:
            return {"success": True, "message": "Login successful"}
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    request = MockRequest(client_ip="192.168.1.102")
    
    # Make 3 failed attempts
    for _ in range(3):
        with pytest.raises(HTTPException):
            await mock_login(request, should_succeed=False)
    
    # Check counter is at 3
    key = f"login_attempts:{request.state.client_ip}"
    counter = await flush_redis.get(key)
    assert counter == "3"
    
    # Successful login should reset counter
    result = await mock_login(request, should_succeed=True)
    assert result["success"] is True
    
    # Counter should be deleted
    counter = await flush_redis.get(key)
    assert counter is None, "Counter should be reset after successful login"
    
    # Should be able to make 5 more failed attempts
    for attempt in range(1, 6):
        with pytest.raises(HTTPException) as exc_info:
            await mock_login(request, should_succeed=False)
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_rate_limiter_per_ip_isolation(flush_redis):
    """
    Test that rate limiter tracks attempts separately per IP address.
    
    Different IPs should have independent counters.
    """
    @rate_limit(max_attempts=5, window_seconds=300)
    async def mock_login(request):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    request_ip1 = MockRequest(client_ip="192.168.1.103")
    request_ip2 = MockRequest(client_ip="192.168.1.104")
    
    # Make 3 failed attempts from IP1
    for _ in range(3):
        with pytest.raises(HTTPException):
            await mock_login(request_ip1)
    
    # Make 2 failed attempts from IP2
    for _ in range(2):
        with pytest.raises(HTTPException):
            await mock_login(request_ip2)
    
    # Check counters are independent
    key1 = f"login_attempts:{request_ip1.state.client_ip}"
    key2 = f"login_attempts:{request_ip2.state.client_ip}"
    
    counter1 = await flush_redis.get(key1)
    counter2 = await flush_redis.get(key2)
    
    assert counter1 == "3", "IP1 should have 3 attempts"
    assert counter2 == "2", "IP2 should have 2 attempts"
    
    # IP1 can make 2 more attempts before being blocked
    for _ in range(2):
        with pytest.raises(HTTPException) as exc_info:
            await mock_login(request_ip1)
        assert exc_info.value.status_code == 401
    
    # IP1's 6th attempt should be blocked
    with pytest.raises(HTTPException) as exc_info:
        await mock_login(request_ip1)
    assert exc_info.value.status_code == 429
    
    # IP2 should still be able to make requests (only 2 attempts so far)
    with pytest.raises(HTTPException) as exc_info:
        await mock_login(request_ip2)
    assert exc_info.value.status_code == 401, "IP2 should not be blocked yet"


@pytest.mark.asyncio
async def test_rate_limiter_only_counts_401_errors(flush_redis):
    """
    Test that rate limiter only increments counter for 401 errors.
    
    Other HTTP errors (like 500) should not increment the counter.
    """
    @rate_limit(max_attempts=5, window_seconds=300)
    async def mock_login(request, error_code: int = 401):
        raise HTTPException(status_code=error_code, detail="Error")
    
    request = MockRequest(client_ip="192.168.1.105")
    key = f"login_attempts:{request.state.client_ip}"
    
    # Make 3 requests with 401 errors
    for _ in range(3):
        with pytest.raises(HTTPException):
            await mock_login(request, error_code=401)
    
    counter = await flush_redis.get(key)
    assert counter == "3", "Counter should be 3 after three 401 errors"
    
    # Make 2 requests with 500 errors (should not increment counter)
    for _ in range(2):
        with pytest.raises(HTTPException):
            await mock_login(request, error_code=500)
    
    counter = await flush_redis.get(key)
    assert counter == "3", "Counter should still be 3 (500 errors don't count)"
    
    # Make 2 more 401 errors to reach the limit
    for _ in range(2):
        with pytest.raises(HTTPException):
            await mock_login(request, error_code=401)
    
    counter = await flush_redis.get(key)
    assert counter == "5", "Counter should be 5 after five 401 errors"
    
    # Next attempt should be blocked
    with pytest.raises(HTTPException) as exc_info:
        await mock_login(request, error_code=401)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limiter_expiration(flush_redis):
    """
    Test that rate limiter sets expiration on Redis keys.
    
    The key should have TTL set to window_seconds.
    """
    @rate_limit(max_attempts=5, window_seconds=300)
    async def mock_login(request):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    request = MockRequest(client_ip="192.168.1.106")
    key = f"login_attempts:{request.state.client_ip}"
    
    # Make one failed attempt
    with pytest.raises(HTTPException):
        await mock_login(request)
    
    # Check that key has TTL set
    ttl = await flush_redis.ttl(key)
    assert ttl > 0, "Key should have TTL set"
    assert ttl <= 300, "TTL should be at most window_seconds (300)"
