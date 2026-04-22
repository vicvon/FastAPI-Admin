import functools
import json
import pickle
from collections.abc import Callable
from typing import Any, TypeVar

from config.settings import get_settings
from core.redis_factory import create_async_redis_client

T = TypeVar("T")


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

    def _serialize(self, value: Any, use_pickle: bool = False) -> str | bytes:
        if use_pickle:
            return pickle.dumps(value)
        return json.dumps(value, default=str)

    def _deserialize(self, value: Any, use_pickle: bool = False) -> Any:
        if value is None:
            return None
        if use_pickle:
            return pickle.loads(value)
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def get(self, key: str, default: Any = None, use_pickle: bool = False) -> Any:
        """获取缓存"""
        full_key = self._make_key(key)
        # 如果是 pickle 模式, 客户端需要是 bytes 模式,或者手动 encode/decode
        # 由于初始化时设置了 decode_responses=True,对于 pickle 可能需要特殊处理
        # 简单起见,这里假设 pickle 存的是 bytes,但是 redis client 会尝试 decode utf-8 可能会出错
        # 所以对于 pickle,建议单独处理或存为 hex 字符串
        # 修正:为了兼容性,如果 use_pickle=True,我们应该使用 bytes 操作。
        # 但 client 是全局的 decode_responses=True。
        # 方案:使用 client.get(key) 获取 str,如果是 pickle 存的时候转为 latin-1 或 base64?
        # 更优雅的方案:CacheManager 初始化时 decode_responses=False,然后在 json 处理时 decode。
        # 或者:set/get 时临时覆盖 decode_responses? (Redis 客户端通常不支持动态覆盖)
        #
        # 调整策略:为了支持 Pickle,存储时转为 bytes,读取时也是 bytes。
        # 但 client 设置了 decode_responses=True 会强制解码。
        # 妥协:Pickle 模式下,我们将 bytes 编码为 latin-1 字符串存储 (1:1 映射)

        try:
            value = await self.client.get(full_key)
            if value is None:
                return default

            if use_pickle:
                # 假设存储时是以 latin-1 编码的字符串
                return pickle.loads(value.encode("latin-1"))

            return self._deserialize(value)
        except Exception:
            # log error
            return default

    async def set(
        self, key: str, value: Any, ttl: int | None = None, use_pickle: bool = False
    ) -> bool:
        """设置缓存"""
        full_key = self._make_key(key)
        try:
            if use_pickle:
                data = pickle.dumps(value).decode("latin-1")
            else:
                data = self._serialize(value)

            await self.client.set(full_key, data, ex=ttl)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
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
    ttl: int = 60, key_builder: Callable | None = None, use_pickle: bool = False
):
    """
    缓存装饰器
    :param ttl: 过期时间 (秒)
    :param key_builder: 自定义 Key 生成函数 (func, *args, **kwargs) -> str
    :param use_pickle: 是否使用 pickle 序列化 (支持复杂对象)
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
            cached_value = await cache.get(key, use_pickle=use_pickle)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 写入缓存
            if result is not None:
                await cache.set(key, result, ttl=ttl, use_pickle=use_pickle)

            return result

        return wrapper

    return decorator
