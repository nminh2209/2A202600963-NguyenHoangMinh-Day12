"""Shared Redis connection for stateless storage."""
import logging

import redis

from app.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_use_redis = False


def init_redis() -> bool:
    global _client, _use_redis
    if not settings.redis_url:
        logger.warning("REDIS_URL not set — using in-memory fallback (not scalable)")
        _use_redis = False
        return False
    try:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        _client.ping()
        _use_redis = True
        logger.info("Connected to Redis")
        return True
    except Exception as exc:
        logger.error("Redis connection failed: %s", exc)
        _use_redis = False
        _client = None
        return False


def get_redis() -> redis.Redis | None:
    return _client if _use_redis else None


def redis_available() -> bool:
    if not _use_redis or _client is None:
        return False
    try:
        _client.ping()
        return True
    except Exception:
        return False
