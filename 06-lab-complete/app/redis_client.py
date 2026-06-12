"""Shared Redis connection for stateless storage."""
import logging
import time

import redis

from app.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_use_redis = False

_STARTUP_RETRIES = 8
_RETRY_DELAY_SEC = 3


def init_redis() -> bool:
    global _client, _use_redis
    if not settings.redis_url:
        logger.warning("REDIS_URL not set — using in-memory fallback (not scalable)")
        _use_redis = False
        return False

    safe_url = settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url
    logger.info("Connecting to Redis at %s", safe_url)

    for attempt in range(1, _STARTUP_RETRIES + 1):
        try:
            _client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=8,
                socket_timeout=8,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            _client.ping()
            _use_redis = True
            logger.info("Connected to Redis")
            return True
        except Exception as exc:
            logger.warning(
                "Redis connection attempt %s/%s failed: %s",
                attempt,
                _STARTUP_RETRIES,
                exc,
            )
            _client = None
            _use_redis = False
            if attempt < _STARTUP_RETRIES:
                time.sleep(_RETRY_DELAY_SEC)

    logger.error(
        "Redis unavailable — using in-memory fallback. "
        "On Render: delete Redis, recreate in Singapore, relink REDIS_URL on day12-agent."
    )
    return False


def ensure_redis() -> bool:
    """Retry Redis connection if URL is configured but not connected."""
    if redis_available():
        return True
    if settings.redis_url:
        return init_redis()
    return False


def get_redis() -> redis.Redis | None:
    ensure_redis()
    return _client if _use_redis else None


def redis_available() -> bool:
    global _use_redis
    if not _use_redis or _client is None:
        return False
    try:
        _client.ping()
        return True
    except Exception:
        _use_redis = False
        return False
