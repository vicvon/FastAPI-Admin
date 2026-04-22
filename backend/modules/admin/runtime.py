from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import FastAPI

from config.settings import get_settings
from core.logger import get_logger
from modules.admin.application.grant_retry_job import run_role_grant_retry_loop

logger = get_logger(__name__)

ROLE_GRANT_RETRY_STOP_KEY = "role_grant_retry_stop"
ROLE_GRANT_RETRY_TASK_KEY = "role_grant_retry_task"


def _start_background_task(app: FastAPI, *, state_key: str, coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    setattr(app.state, state_key, task)
    return task


async def _stop_task(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def start_admin_runtime_tasks(app: FastAPI) -> None:
    if ":memory:" in (get_settings().database_url or ""):
        setattr(app.state, ROLE_GRANT_RETRY_STOP_KEY, None)
        setattr(app.state, ROLE_GRANT_RETRY_TASK_KEY, None)
        logger.info("admin.runtime.role_grant_retry.disabled reason=in_memory_database")
        return

    stop_event = asyncio.Event()
    setattr(app.state, ROLE_GRANT_RETRY_STOP_KEY, stop_event)
    _start_background_task(
        app,
        state_key=ROLE_GRANT_RETRY_TASK_KEY,
        coro=run_role_grant_retry_loop(
            stop_event=stop_event,
            interval_seconds=1,
            batch_limit=20,
            role_grant_retry_interval_seconds=60,
            user_role_batch_limit=200,
        ),
    )
    logger.info(
        "admin.runtime.role_grant_retry.started state_key={} stop_key={}",
        ROLE_GRANT_RETRY_TASK_KEY,
        ROLE_GRANT_RETRY_STOP_KEY,
    )


async def stop_admin_runtime_tasks(app: FastAPI) -> None:
    stop_event = getattr(app.state, ROLE_GRANT_RETRY_STOP_KEY, None)
    if stop_event is not None:
        stop_event.set()
    try:
        await _stop_task(getattr(app.state, ROLE_GRANT_RETRY_TASK_KEY, None))
        logger.info(
            "admin.runtime.role_grant_retry.stopped state_key={}",
            ROLE_GRANT_RETRY_TASK_KEY,
        )
    except Exception:
        logger.opt(exception=True).warning(
            "admin.runtime.role_grant_retry.stop_failed state_key={}",
            ROLE_GRANT_RETRY_TASK_KEY,
        )
