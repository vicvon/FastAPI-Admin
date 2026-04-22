import functools
import base64
import json
import pickle
from collections.abc import Callable
from typing import Any, Literal, TypeVar

from config.settings import get_settings
from core.logger import get_logger
from core.redis_factory import create_async_redis_client

T = TypeVar("T")
CacheEncoding = Literal["json", "pickle"]
logger = get_logger(__name__)


class CacheManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.settings = get_settings().redis
        self.client: Any = None
        self._init_client()
        self._initialized = True

    def _init_client(self):
        self.client = create_async_redis_client(self.settings)

    def _make_key(self, key: str) -> str:
        """生成带前缀的 Key"""
        if not self.settings.prefix:
            return key
        return f"{self.settings.prefix}{key}"

    def make_key(self, key: str) -> str:
        return self._make_key(key)

    def _resolve_encoding(
        self, *, use_pickle: bool = False, encoding: CacheEncoding = "json"
    ) -> CacheEncoding:
        if use_pickle:
            logger.warning(
                "infra.cache.legacy_pickle_flag_used keyless_call=true encoding=pickle"
            )
            return "pickle"
        return encoding

    def _serialize(self, value: Any, *, encoding: CacheEncoding = "json") -> str:
        if encoding == "pickle":
            # Use base64 to keep redis decode_responses=True compatible.
            return base64.b64encode(pickle.dumps(value)).decode("ascii")
        return json.dumps(value, default=str)

    def _deserialize(self, value: Any, *, encoding: CacheEncoding = "json") -> Any:
        if value is None:
            return None
        if encoding == "pickle":
            if isinstance(value, str):
                value = value.encode("ascii")
            return pickle.loads(base64.b64decode(value))
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def get(
        self,
        key: str,
        default: Any = None,
        use_pickle: bool = False,
        *,
        encoding: CacheEncoding = "json",
    ) -> Any:
        """获取缓存"""
        full_key = self._make_key(key)
        resolved_encoding = self._resolve_encoding(
            use_pickle=use_pickle, encoding=encoding
        )
        try:
            value = await self.client.get(full_key)
            if value is None:
                return default
            return self._deserialize(value, encoding=resolved_encoding)
        except Exception as exc:
            logger.opt(exception=True).warning(
                "infra.cache.get_failed key={} encoding={} error_type={}",
                key,
                resolved_encoding,
                type(exc).__name__,
            )
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        use_pickle: bool = False,
        *,
        encoding: CacheEncoding = "json",
    ) -> bool:
        """设置缓存"""
        full_key = self._make_key(key)
        resolved_encoding = self._resolve_encoding(
            use_pickle=use_pickle, encoding=encoding
        )
        try:
            data = self._serialize(value, encoding=resolved_encoding)
            await self.client.set(full_key, data, ex=ttl)
            return True
        except Exception as exc:
            logger.opt(exception=True).warning(
                "infra.cache.set_failed key={} encoding={} error_type={}",
                key,
                resolved_encoding,
                type(exc).__name__,
            )
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        full_key = self._make_key(key)
        return await self.client.delete(full_key) > 0

    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        full_key = self._make_key(key)
        return await self.client.exists(full_key) > 0

    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        full_key = self._make_key(key)
        return await self.client.expire(full_key, ttl)

    async def incr(self, key: str, amount: int = 1) -> int:
        """自增"""
        full_key = self._make_key(key)
        return await self.client.incr(full_key, amount)

    async def scan_iter(self, match: str = "*"):
        """批量扫描 (去除前缀返回)"""
        full_match = self._make_key(match)
        prefix_len = len(self.settings.prefix)

        # RedisCluster 的 scan_iter 行为略有不同,但接口兼容
        async for key in self.client.scan_iter(match=full_match):
            # key 是 str (因为 decode_responses=True)
            yield key[prefix_len:]

    async def hset(self, key: str, field: str, value: str) -> int:
        full_key = self._make_key(key)
        return await self.client.hset(full_key, field, value)

    async def hget(self, key: str, field: str) -> str | None:
        full_key = self._make_key(key)
        return await self.client.hget(full_key, field)

    async def hdel(self, key: str, field: str) -> int:
        full_key = self._make_key(key)
        return await self.client.hdel(full_key, field)

    async def hscan_iter(self, key: str, *, count: int = 1000):
        full_key = self._make_key(key)
        cursor = 0
        while True:
            cursor, data = await self.client.hscan(full_key, cursor=cursor, count=count)
            for field, value in (data or {}).items():
                yield field, value
            if int(cursor) == 0:
                break

    async def rename(self, src_key: str, dst_key: str) -> bool:
        full_src = self._make_key(src_key)
        full_dst = self._make_key(dst_key)
        await self.client.rename(full_src, full_dst)
        return True

    async def close(self):
        """关闭连接"""
        await self.client.aclose()


# Global Instance
cache = CacheManager()


def cached(
    ttl: int = 60,
    key_builder: Callable | None = None,
    use_pickle: bool = False,
    *,
    encoding: CacheEncoding = "json",
):
    """
    缓存装饰器
    :param ttl: 过期时间 (秒)
    :param key_builder: 自定义 Key 生成函数 (func, *args, **kwargs) -> str
    :param use_pickle: 兼容旧调用, 为 True 时等价于 encoding="pickle"
    :param encoding: 缓存序列化格式, 默认 json
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if key_builder:
                key = key_builder(func, *args, **kwargs)
            else:
                # 默认 Key: func_name:arg1:arg2...
                # 简单处理,可能不严谨
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                key = ":".join(key_parts)

            # 尝试获取缓存
            cached_value = await cache.get(
                key, use_pickle=use_pickle, encoding=encoding
            )
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 写入缓存
            if result is not None:
                await cache.set(
                    key,
                    result,
                    ttl=ttl,
                    use_pickle=use_pickle,
                    encoding=encoding,
                )

            return result

        return wrapper

    return decorator
