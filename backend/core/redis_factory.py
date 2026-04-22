from __future__ import annotations

from typing import Any

import redis as sync_redis
from redis import asyncio as async_redis
from redis.asyncio.cluster import RedisCluster as AsyncRedisCluster
from redis.asyncio.sentinel import Sentinel as AsyncSentinel
from redis.cluster import RedisCluster as SyncRedisCluster
from redis.sentinel import Sentinel as SyncSentinel


def _build_connection_kwargs(
    redis_settings: Any, *, include_socket_timeout: bool = True
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "decode_responses": True,
        "max_connections": redis_settings.max_connections,
    }
    if include_socket_timeout:
        kwargs["socket_timeout"] = redis_settings.socket_timeout
    if redis_settings.password:
        kwargs["password"] = redis_settings.password
    return kwargs


def _parse_nodes(nodes: str) -> list[tuple[str, int]]:
    parsed: list[tuple[str, int]] = []
    if not nodes:
        return parsed
    for node in nodes.split(","):
        if ":" not in node:
            continue
        host, port = node.strip().split(":", 1)
        parsed.append((host, int(port)))
    return parsed


def create_async_redis_client(redis_settings: Any):
    mode = redis_settings.mode.lower()
    connection_kwargs = _build_connection_kwargs(redis_settings)
    if mode == "cluster":
        startup_nodes = [
            async_redis.cluster.ClusterNode(host, port)
            for host, port in _parse_nodes(redis_settings.nodes)
        ]
        if not startup_nodes:
            startup_nodes = [async_redis.cluster.ClusterNode("localhost", 6379)]
        return AsyncRedisCluster(
            startup_nodes=startup_nodes,
            **connection_kwargs,
        )
    if mode == "sentinel":
        sentinels = _parse_nodes(redis_settings.nodes)
        sentinel_client = AsyncSentinel(
            sentinels,
            sentinel_kwargs=connection_kwargs,
        )
        return sentinel_client.master_for(
            redis_settings.master_name,
            **connection_kwargs,
        )
    return async_redis.from_url(redis_settings.url, **connection_kwargs)


def create_sync_redis_client(
    redis_settings: Any, *, include_socket_timeout: bool = True
):
    mode = redis_settings.mode.lower()
    connection_kwargs = _build_connection_kwargs(
        redis_settings, include_socket_timeout=include_socket_timeout
    )
    if mode == "cluster":
        startup_nodes = [
            sync_redis.cluster.ClusterNode(host, port)
            for host, port in _parse_nodes(redis_settings.nodes)
        ]
        if not startup_nodes:
            startup_nodes = [sync_redis.cluster.ClusterNode("localhost", 6379)]
        return SyncRedisCluster(
            startup_nodes=startup_nodes,
            **connection_kwargs,
        )
    if mode == "sentinel":
        sentinels = _parse_nodes(redis_settings.nodes)
        sentinel_client = SyncSentinel(
            sentinels,
            sentinel_kwargs=connection_kwargs,
        )
        return sentinel_client.master_for(
            redis_settings.master_name,
            **connection_kwargs,
        )
    return sync_redis.from_url(redis_settings.url, **connection_kwargs)
