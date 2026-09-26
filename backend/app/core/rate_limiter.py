import time
from typing import Optional
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.core.logging import logger
from app.core.redis import cache_service


class RateLimiter:
    """
    Fixed-window rate limiter utilizing Redis (when connected) or thread-safe InMemoryCache.
    Limits abuse against external OpenAI, Weather, and market quote APIs.
    """

    async def check_rate_limit(
        self,
        identifier: str,
        action: str = "chat",
        limit_per_minute: Optional[int] = None,
    ) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        limit = limit_per_minute or (
            settings.RATE_LIMIT_CHAT_PER_MINUTE
            if action == "chat"
            else settings.RATE_LIMIT_TOOLS_PER_MINUTE
        )

        now = time.time()
        current_minute = int(now // 60)
        cache_key = f"rate_limit:{action}:{identifier}:{current_minute}"

        # Fetch current request count in this 60s window
        current_count = await cache_service.get_json(cache_key) or 0

        if current_count >= limit:
            retry_after = max(1, int(60 - (now % 60)))
            logger.warning(
                f"Rate limit exceeded for {identifier} on '{action}'. Current: {current_count}, Limit: {limit}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} {action} requests per minute. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        # Increment count and set 65s expiration
        await cache_service.set_json(cache_key, current_count + 1, ttl_seconds=65)


rate_limiter = RateLimiter()


async def check_chat_rate_limit(request: Request, user_id: str) -> None:
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"{user_id}:{client_ip}"
    await rate_limiter.check_rate_limit(identifier, action="chat")


async def check_tool_rate_limit(request: Request, user_id: Optional[str] = None) -> None:
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"{user_id or 'anon'}:{client_ip}"
    await rate_limiter.check_rate_limit(identifier, action="tools")
