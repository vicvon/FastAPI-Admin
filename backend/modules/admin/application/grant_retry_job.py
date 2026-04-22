from __future__ import annotations

import asyncio

from sqlmodel.ext.asyncio.session import AsyncSession

from app_setup.permission_providers import build_permission_manager
from core.database import engine
from core.logger import get_logger
from core.redis_lock import redis_lock
from modules.admin.application.services import (
    RolePermissionApplicationService,
    retry_due_user_role_groupings,
)
from modules.admin.infra.repositories import (
    PermissionRepository,
    RoleGrantJobRepository,
    RoleRepository,
    ScopeRuleRepository,
)

logger = get_logger(__name__)
ROLE_GRANT_RETRY_LOOP_LOCK_KEY = "admin:role_grant_retry_loop"


def _build_service(session: AsyncSession) -> RolePermissionApplicationService:
    return RolePermissionApplicationService(
        roles=RoleRepository(session),
        permissions=PermissionRepository(session),
        scope_rules=ScopeRuleRepository(session),
        grant_jobs=RoleGrantJobRepository(session),
        permission_manager=build_permission_manager(
            session_factory=lambda: AsyncSession(engine, expire_on_commit=False)
        ),
    )


async def run_role_grant_retry_loop(
    stop_event: asyncio.Event,
    interval_seconds: int = 1,
    batch_limit: int = 20,
    role_grant_retry_interval_seconds: int = 60,
    user_role_batch_limit: int = 200,
) -> None:
    last_role_grant_retry_at = 0.0
    while not stop_event.is_set():
        try:
            lock_ttl_seconds = max(interval_seconds * 2, 120)
            async with redis_lock(
                key=ROLE_GRANT_RETRY_LOOP_LOCK_KEY, ttl_seconds=lock_ttl_seconds
            ) as got_lock:
                if got_lock:
                    async with AsyncSession(engine, expire_on_commit=False) as session:
                        permission_manager = build_permission_manager(
                            session_factory=lambda: AsyncSession(
                                engine, expire_on_commit=False
                            )
                        )
                        (
                            user_attempted,
                            user_succeeded,
                        ) = await retry_due_user_role_groupings(
                            permission_manager,
                            limit=user_role_batch_limit,
                        )
                        if user_attempted > 0:
                            logger.info(
                                "admin.user_role_retry_loop attempted={} succeeded={}",
                                user_attempted,
                                user_succeeded,
                            )
                        now_ts = asyncio.get_running_loop().time()
                        should_run_role_retry = (
                            now_ts - last_role_grant_retry_at
                            >= role_grant_retry_interval_seconds
                        )
                        if should_run_role_retry:
                            service = _build_service(session)
                            (
                                attempted,
                                succeeded,
                            ) = await service.retry_failed_grant_jobs(limit=batch_limit)
                            if attempted > 0:
                                logger.info(
                                    "admin.role_grant_retry_loop attempted={} succeeded={}",
                                    attempted,
                                    succeeded,
                                )
                            cleaned = await service.cleanup_synced_grant_jobs(
                                limit=batch_limit
                            )
                            if cleaned > 0:
                                logger.info(
                                    "admin.role_grant_cleanup cleaned={}", cleaned
                                )
                            last_role_grant_retry_at = now_ts
                else:
                    logger.debug("admin.role_grant_retry_loop lock not acquired")
        except Exception:
            logger.opt(exception=True).error("admin role grant retry failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except TimeoutError:
            continue
