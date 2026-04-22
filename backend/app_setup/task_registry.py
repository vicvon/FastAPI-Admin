import asyncio
from contextlib import suppress

from fastapi import FastAPI

from config.settings import get_settings
from core.logger import get_logger
from modules.admin.application.grant_retry_job import (
    run_role_grant_retry_loop,
)

logger = get_logger(__name__)


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


async def start_runtime_tasks(app: FastAPI) -> None:
    if ":memory:" not in (get_settings().database_url or ""):
        app.state.role_grant_retry_stop = asyncio.Event()
        app.state.role_grant_retry_task = _start_background_task(
            app,
            state_key="role_grant_retry_task",
            coro=run_role_grant_retry_loop(
                stop_event=app.state.role_grant_retry_stop,
                interval_seconds=1,
                batch_limit=20,
                role_grant_retry_interval_seconds=60,
                user_role_batch_limit=200,
            ),
        )
        return

    app.state.role_grant_retry_stop = None
    app.state.role_grant_retry_task = None


async def stop_runtime_tasks(app: FastAPI) -> None:
    stop_event = getattr(app.state, "role_grant_retry_stop", None)
    if stop_event is not None:
        stop_event.set()
    try:
        await _stop_task(getattr(app.state, "role_grant_retry_task", None))
    except Exception:
        logger.opt(exception=True).warning("shutdown role grant retry loop failed")
