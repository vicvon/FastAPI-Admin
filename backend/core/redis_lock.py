from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from core.cache import cache
from core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def redis_lock(*, key: str, ttl_seconds: int):
    token = uuid.uuid4().hex
    full_key = cache.make_key(key)
    ok = False
    try:
        try:
            ok = bool(
                await cache.client.set(
                    name=full_key, value=token, nx=True, ex=ttl_seconds
                )
            )
        except Exception as e:
            logger.opt(exception=True).warning(
                "infra.redis_lock.acquire_failed key={} full_key={} reason={}",
                key,
                full_key,
                type(e).__name__,
            )
            ok = False
        yield ok
    finally:
        if ok:
            try:
                release_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                  return redis.call("del", KEYS[1])
                else
                  return 0
                end
                """
                await cache.client.eval(release_script, 1, full_key, token)
            except Exception:
                logger.opt(exception=True).warning(
                    "infra.redis_lock.release_failed key={} full_key={}",
                    key,
                    full_key,
                )
