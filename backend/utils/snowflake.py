from __future__ import annotations

import socket
import threading
import time
import uuid
from functools import lru_cache

import redis

from config.settings import get_settings


class Snowflake:
    def __init__(self, node_id: int, epoch_ms: int) -> None:
        if not (0 <= node_id < 1024):
            raise ValueError("node_id must be in [0, 1023]")
        self._node_id = node_id
        self._epoch_ms = epoch_ms
        self._lock = threading.Lock()
        self._last_ts_ms = -1
        self._sequence = 0

    def next_id(self) -> int:
        with self._lock:
            ts_ms = self._now_ms()
            if ts_ms < self._last_ts_ms:
                ts_ms = self._wait_until(self._last_ts_ms)

            if ts_ms == self._last_ts_ms:
                self._sequence = (self._sequence + 1) & 0xFFF
                if self._sequence == 0:
                    ts_ms = self._wait_until(ts_ms)
            else:
                self._sequence = 0

            self._last_ts_ms = ts_ms

            timestamp_part = (ts_ms - self._epoch_ms) & ((1 << 41) - 1)
            return (timestamp_part << 22) | (self._node_id << 12) | self._sequence

    @staticmethod
    def _now_ms() -> int:
        return time.time_ns() // 1_000_000

    def _wait_until(self, target_ts_ms: int) -> int:
        ts_ms = self._now_ms()
        while ts_ms <= target_ts_ms:
            time.sleep(0.0005)
            ts_ms = self._now_ms()
        return ts_ms


def _get_local_ip() -> str:
    """获取本机IP地址"""
    try:
        # 尝试通过连接外网探测本机IP(不会实际发送数据)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def _derive_node_id() -> int:
    """
    自动推导 Node ID, 策略优先级:
    1. Redis 自增 Key 取模
    2. IP 地址后两位生成
    3. uuid.getnode() (MAC Address)
    """
    settings = get_settings()

    # 1. Redis Increment Strategy
    try:
        redis_settings = settings.redis
        # 构造同步 Redis 客户端
        if redis_settings.mode == "standalone":
            # 解析 URL 可能会丢失 password 等参数如果 url 不完整, 这里假设 settings.redis.url 是完整的
            # 或者手动构造参数
            r = redis.from_url(
                redis_settings.url,
                password=redis_settings.password if redis_settings.password else None,
                socket_timeout=1.0,  # 快速失败
                decode_responses=True,
            )
        elif redis_settings.mode == "cluster":
            # 简单处理 Cluster 模式, 这里需要 redis-py-cluster 或者 redis.cluster
            # redis-py 4.x+ 支持 cluster
            from redis.cluster import ClusterNode, RedisCluster

            startup_nodes = []
            if redis_settings.nodes:
                for node in redis_settings.nodes.split(","):
                    if ":" in node:
                        host, port = node.strip().split(":")
                        startup_nodes.append(ClusterNode(host, int(port)))

            r = RedisCluster(
                startup_nodes=startup_nodes,
                password=redis_settings.password if redis_settings.password else None,
                socket_timeout=1.0,
                decode_responses=True,
            )
        elif redis_settings.mode == "sentinel":
            # Sentinel 模式同步连接较复杂, 这里简化处理, 如果配置复杂建议 fallback
            from redis.sentinel import Sentinel

            sentinels = []
            if redis_settings.nodes:
                for node in redis_settings.nodes.split(","):
                    if ":" in node:
                        host, port = node.strip().split(":")
                        sentinels.append((host, int(port)))
            sentinel = Sentinel(
                sentinels,
                socket_timeout=1.0,
                password=redis_settings.password if redis_settings.password else None,
            )
            r = sentinel.master_for(redis_settings.master_name, decode_responses=True)
        else:
            r = None

        if r:
            key = f"{redis_settings.prefix}snowflake:node_id_seq"
            # INCR 操作是原子的
            node_seq = r.incr(key)
            # 取模 1024
            return node_seq % 1024

    except Exception:
        # Redis 连接失败或超时, 降级到下一个策略
        # print(f"Warning: Failed to derive node_id from Redis: {e}")
        pass

    # 2. IP Address Strategy (Last 2 octets)
    try:
        ip = _get_local_ip()
        # IP format: a.b.c.d
        parts = ip.split(".")
        if len(parts) == 4:
            # 取后两位: c, d
            c = int(parts[2])
            d = int(parts[3])
            # 组合生成: (c << 8 | d) % 1024
            # 1024 是 2^10, 所以主要是 d (8位) 和 c 的低2位
            return ((c << 8) | d) % 1024
    except Exception:
        pass

    # 3. Fallback to MAC address
    return uuid.getnode() % 1024


@lru_cache(maxsize=1)
def _get_generator() -> Snowflake:
    settings = get_settings()
    # 如果 settings 中显式配置了 node_id (非0), 则使用配置值
    # 否则使用自动推导策略
    node_id = settings.snowflake_node_id or _derive_node_id()

    return Snowflake(node_id=node_id, epoch_ms=settings.snowflake_epoch_ms)


def next_snowflake_id() -> int:
    return _get_generator().next_id()
