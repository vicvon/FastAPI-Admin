from __future__ import annotations

from pathlib import Path
from threading import Lock

import casbin
import casbin_sqlalchemy_adapter

from config.settings import get_settings
from core.logger import get_logger
from core.redis_factory import create_sync_redis_client
from modules.iam.infra.watcher import RedisWatcher

logger = get_logger(__name__)


_ENFORCER: casbin.Enforcer | None = None
_ENFORCER_LOCK = Lock()


def _create_enforcer() -> casbin.Enforcer:
    settings = get_settings()
    db_url = settings.database_url
    if "aiomysql" in db_url:
        db_url = db_url.replace("+aiomysql", "+pymysql")
    if "aiosqlite" in db_url:
        db_url = db_url.replace("+aiosqlite", "")

    adapter = casbin_sqlalchemy_adapter.Adapter(db_url)
    model_path = Path(__file__).resolve().parent / "model.conf"
    enforcer = casbin.Enforcer(str(model_path), adapter)
    enforcer.enable_auto_save(True)
    _init_watcher(enforcer)
    enforcer.load_policy()
    _prune_role_inheritance_grouping_policies(enforcer)
    return enforcer


def _init_watcher(enforcer: casbin.Enforcer) -> None:
    try:
        settings = get_settings()
        redis_settings = settings.redis
        watcher = RedisWatcher(
            client=create_sync_redis_client(
                redis_settings, include_socket_timeout=False
            ),
            prefix=redis_settings.prefix,
        )
        enforcer.set_watcher(watcher)
        watcher.set_update_callback(enforcer.load_policy)
    except Exception as exc:
        logger.warning(
            "iam.enforcer.watcher_init_failed error_type={}",
            type(exc).__name__,
        )


def get_iam_enforcer() -> casbin.Enforcer:
    global _ENFORCER
    if _ENFORCER is not None:
        return _ENFORCER
    with _ENFORCER_LOCK:
        if _ENFORCER is None:
            _ENFORCER = _create_enforcer()
        return _ENFORCER


def refresh_iam_enforcer() -> None:
    global _ENFORCER
    with _ENFORCER_LOCK:
        _close_watcher(_ENFORCER)
        _ENFORCER = None


def has_iam_enforcer() -> bool:
    return _ENFORCER is not None


def shutdown_iam_watcher() -> None:
    _close_watcher(_ENFORCER)


def _close_watcher(enforcer: casbin.Enforcer | None) -> None:
    if enforcer is None:
        return
    watcher = getattr(enforcer, "watcher", None)
    if watcher is not None and hasattr(watcher, "close"):
        try:
            watcher.close()
        except Exception:
            logger.opt(exception=True).warning("iam.enforcer.watcher_close_failed")


def _prune_role_inheritance_grouping_policies(enforcer: casbin.Enforcer) -> None:
    if hasattr(enforcer, "enable_auto_notify_watcher"):
        enforcer.enable_auto_notify_watcher(False)
    try:
        for sub, role in list(enforcer.get_grouping_policy()):
            if str(sub).startswith("role:") and str(role).startswith("role:"):
                enforcer.remove_grouping_policy(sub, role)
    finally:
        if hasattr(enforcer, "enable_auto_notify_watcher"):
            enforcer.enable_auto_notify_watcher(True)
        if hasattr(enforcer, "watcher") and enforcer.watcher:
            enforcer.watcher.update()
