from typing import Optional
from fastapi import HTTPException, Request
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import time
import aioredis
from datetime import datetime, timedelta

api_key_header = APIKeyHeader(name="X-API-Key")


class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = aioredis.from_url(
            "redis://localhost",
            encoding="utf-8",
            decode_responses=True
        )
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (API key or IP)
        client_id = request.headers.get("X-API-Key", request.client.host)

        # Check rate limit
        current = int(time.time())
        window_key = f"ratelimit:{client_id}:{current // self.window}"

        # Increment request count
        request_count = await self.redis.incr(window_key)

        # Set expiry if first request in window
        if request_count == 1:
            await self.redis.expire(window_key, self.window)

        if request_count > self.rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.rate_limit - request_count)
        )
        response.headers["X-RateLimit-Reset"] = str(
            (current // self.window * self.window) + self.window
        )

        return response


async def verify_api_key(
        api_key: str = Depends(api_key_header)
) -> str:
    """Verify API key and return associated wallet address"""
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            api_key,
            "",  # Should be in config
            algorithms=["HS256"]
        )

        # Check if token is expired
        if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            raise HTTPException(
                status_code=401,
                detail="API key expired"
            )

        return payload["wallet_address"]

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


class RequestLogger(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis = aioredis.from_url(
            "redis://localhost",
            encoding="utf-8",
            decode_responses=True
        )

    async def dispatch(self, request: Request, call_next):
        # Record request start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Log request details
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "api_key": request.headers.get("X-API-Key", "none")
        }

        await self.redis.lpush(
            "api:request_logs",
            json.dumps(log_entry)
        )
        await self.redis.ltrim("api:request_logs", 0, 9999)  # Keep last 10K logs

        return response


async def get_api_usage(api_key: str) -> Dict[str, Any]:
    """Get API usage statistics for an API key"""
    try:
        redis = aioredis.from_url(
            "redis://localhost",
            encoding="utf-8",
            decode_responses=True
        )

        # Get current window
        current_window = int(time.time()) // 60

        # Get usage for last hour
        hourly_usage = 0
        for minute in range(60):
            window_key = f"ratelimit:{api_key}:{current_window - minute}"
            count = await redis.get(window_key)
            if count:
                hourly_usage += int(count)

        # Get total requests from logs
        total_requests = 0
        logs = await redis.lrange("api:request_logs", 0, -1)
        for log in logs:
            log_data = json.loads(log)
            if log_data["api_key"] == api_key:
                total_requests += 1

        return {
            "hourly_usage": hourly_usage,
            "total_requests": total_requests,
            "rate_limit": 100,
            "remaining": max(0, 100 - hourly_usage)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting API usage: {str(e)}"
        )