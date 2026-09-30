"""The cache must never make a request slower than a cache miss."""
import time

from app import cache


def test_no_redis_url_means_no_cache_and_no_probing(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    t = time.monotonic()
    for _ in range(50):
        assert cache.get("k") is None
        cache.set("k", {"a": 1})
        cache.delete("k:*")
    assert time.monotonic() - t < 0.1


def test_unreachable_redis_is_a_fast_miss_then_skipped(monkeypatch):
    # 10.255.255.1 is non-routable: a connect attempt hangs until its timeout.
    monkeypatch.setenv("REDIS_URL", "redis://10.255.255.1:6379/0")
    monkeypatch.setattr(cache, "_redis", None)
    monkeypatch.setattr(cache, "_down_until", 0.0)
    t = time.monotonic()
    assert cache.get("k") is None          # pays one short timeout
    first = time.monotonic() - t
    t = time.monotonic()
    for _ in range(20):
        assert cache.get("k") is None      # then stops trying for a while
    assert first < 2 and time.monotonic() - t < 0.05


def test_pattern_delete_removes_every_matching_key(monkeypatch):
    deleted = []

    class Fake:
        def scan_iter(self, match):
            return [k for k in ("learning:path:s1:c1", "learning:path:s1:c2", "learning:path:s2:c1")
                    if k.startswith(match.rstrip("*"))]

        def delete(self, *keys):
            deleted.extend(keys)

    monkeypatch.setenv("REDIS_URL", "redis://example")
    monkeypatch.setattr(cache, "_redis", Fake())
    monkeypatch.setattr(cache, "_down_until", 0.0)
    cache.delete("learning:path:s1:*")
    assert deleted == ["learning:path:s1:c1", "learning:path:s1:c2"]
