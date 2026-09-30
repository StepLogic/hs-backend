"""Optional Redis cache. With no REDIS_URL it is off, and every call is a no-op.

It used to fall back to probing localhost:6379 on every call when REDIS_URL was
unset, which is how production runs: two probes per cached request, and
/learning/path spent ~8 s in them. A cache must never be slower than a miss, so
connections time out fast and any Redis error is treated as a miss.
"""
import json
import os
import time
from typing import Any, Callable

from redis import Redis

_redis: Redis | None = None
_down_until = 0.0  # after a failure, stop trying for a while instead of paying the timeout again


def _client() -> Redis | None:
    global _redis
    url = os.getenv("REDIS_URL", "")
    if not url or time.monotonic() < _down_until:
        return None
    if _redis is None:
        _redis = Redis.from_url(
            url, decode_responses=True, socket_connect_timeout=0.5, socket_timeout=0.5
        )
    return _redis


def _failed() -> None:
    global _down_until
    _down_until = time.monotonic() + 60


def get(key: str) -> Any | None:
    client = _client()
    if not client:
        return None
    try:
        raw = client.get(key)
    except Exception:
        _failed()
        return None
    return None if raw is None else json.loads(raw)


def set(key: str, value: Any, ttl: int = 300) -> None:
    client = _client()
    if not client:
        return
    try:
        client.setex(key, ttl, json.dumps(value))
    except Exception:
        _failed()


def delete(key: str) -> None:
    """Delete a key, or every key matching a glob such as "learning:path:<id>:*".
    DEL takes literal names, so the pattern form used to delete nothing."""
    client = _client()
    if not client:
        return
    try:
        keys = list(client.scan_iter(match=key)) if any(c in key for c in "*?[") else [key]
        if keys:
            client.delete(*keys)
    except Exception:
        _failed()


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
