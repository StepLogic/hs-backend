import json
import os
from typing import Any, Callable

from redis import Redis

_redis: Redis | None = None


def _client() -> Redis | None:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "")
        if url:
            _redis = Redis.from_url(url, decode_responses=True)
        else:
            try:
                _redis = Redis(host="localhost", port=6379, decode_responses=True)
                _redis.ping()
            except Exception:
                _redis = None
    return _redis


def get(key: str) -> Any | None:
    client = _client()
    if not client:
        return None
    raw = client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def set(key: str, value: Any, ttl: int = 300) -> None:
    client = _client()
    if not client:
        return
    client.setex(key, ttl, json.dumps(value))


def delete(key: str) -> None:
    client = _client()
    if client:
        client.delete(key)


def cached(key_fn: Callable, ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            cached_value = get(key)
            if cached_value is not None:
                return cached_value
            result = func(*args, **kwargs)
            set(key, result, ttl)
            return result
        return wrapper
    return decorator
