import json
import time
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class InMemoryCache:
    """In-memory cache fallback when Redis is not reachable."""

    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        val, expiry = item
        if expiry and time.time() > expiry:
            del self._store[key]
            return None
        return val

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expiry = (time.time() + ex) if ex else float("inf")
        self._store[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def clear(self) -> None:
        self._store.clear()

    async def ping(self) -> bool:
        return True


class CacheService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._memory_cache = InMemoryCache()
        self._using_redis: bool = False
        self._connected: bool = False

    async def initialize(self):
        if not settings.CACHE_ENABLED:
            logger.info("Caching is disabled via configuration.")
            return

        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
            await client.ping()
            self._redis = client
            self._using_redis = True
            self._connected = True
            logger.info(f"Connected to Redis cache at {settings.REDIS_URL}")
        except Exception as e:
            self._using_redis = False
            self._connected = False
            logger.warning(
                f"Redis unavailable ({e}). Gracefully falling back to in-memory cache."
            )

    async def close(self):
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass

    @property
    def is_redis(self) -> bool:
        return self._using_redis

    async def get_json(self, key: str) -> Optional[Any]:
        if not settings.CACHE_ENABLED:
            return None
        try:
            if self._using_redis and self._redis:
                val = await self._redis.get(key)
            else:
                val = await self._memory_cache.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
        return None

    async def set_json(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> bool:
        if not settings.CACHE_ENABLED:
            return False
        ttl = ttl_seconds if ttl_seconds is not None else settings.CACHE_DEFAULT_TTL
        try:
            payload = json.dumps(value)
            if self._using_redis and self._redis:
                await self._redis.set(key, payload, ex=ttl)
            else:
                await self._memory_cache.set(key, payload, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            if self._using_redis and self._redis:
                await self._redis.delete(key)
            else:
                await self._memory_cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False

    async def clear(self) -> None:
        try:
            if self._using_redis and self._redis:
                await self._redis.flushdb()
            else:
                await self._memory_cache.clear()
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")

    async def health_check(self) -> dict[str, Any]:
        if self._using_redis and self._redis:
            try:
                await self._redis.ping()
                return {"status": "healthy", "provider": "redis", "url": settings.REDIS_URL}
            except Exception as e:
                return {"status": "degraded", "provider": "in_memory_fallback", "error": str(e)}
        return {"status": "healthy", "provider": "in_memory", "note": "Redis not active"}


cache_service = CacheService()
