from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from core.context import RequestContext

_INITIALIZED = False


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _normalize_level(level: str) -> str:
    normalized = (level or "INFO").upper()
    if normalized == "WARN":
        return "WARNING"
    return normalized


def _patch_record(record: dict[str, Any]) -> dict[str, Any]:
    extra = record.setdefault("extra", {})
    extra.setdefault("request_id", RequestContext.get_request_id() or "-")
    extra.setdefault("user_id", RequestContext.get_user_id() or "-")
    extra.setdefault("user_name", RequestContext.get_user_name() or "-")
    extra.setdefault("ip", RequestContext.get_ip() or "-")
    extra.setdefault("app_id", RequestContext.get_app_id() or "-")
    extra.setdefault("logger_name", record.get("name", "-"))
    return record


def _configure_std_logging_intercept(debug: bool, level: str) -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(_normalize_level(level))

    if not debug:
        return

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "sqlalchemy"):
        std_logger = logging.getLogger(name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False
        std_logger.setLevel(_normalize_level(level))


def get_logger(name: str | None = None):
    if name:
        return logger.bind(logger_name=name)
    return logger


def _build_loguru_rotation(max_bytes: int) -> int:
    """构建日志轮转大小配置

    Args:
        max_bytes: 单个日志文件最大字节数

    Returns:
        日志文件大小限制(字节)
    """
    return max_bytes if max_bytes > 0 else 100 * 1024 * 1024


def _build_loguru_retention(retention_days: int) -> int:
    """构建日志保留配置

    Args:
        retention_days: 日志保留天数

    Returns:
        保留的日志文件数量上限
    """
    # 每天一个日志文件, 保留指定天数
    return retention_days if retention_days > 0 else 30


def init_logging(
    *,
    level: str = "INFO",
    console_enabled: bool = True,
    file_enabled: bool = True,
    directory: str = "logs",
    filename: str = "app.log",
    fmt: str = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | rid={extra[request_id]} uid={extra[user_id]} ip={extra[ip]} | {message}",
    debug: bool = False,
    retention: str = "30 days",
    rotation: str = "100 MB",
    force: bool = False,
) -> None:
    global _INITIALIZED
    if _INITIALIZED and not force:
        return

    logger.remove()
    logger.configure(patcher=_patch_record)

    normalized_level = _normalize_level(level)
    if console_enabled:
        logger.add(
            sink=sys.stdout,
            level=normalized_level,
            format=fmt,
            colorize=False,
            backtrace=False,
            diagnose=False,
            enqueue=True,
        )

    if file_enabled:
        log_dir = Path(directory).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = str((log_dir / filename).resolve())
        logger.add(
            sink=file_path,
            level=normalized_level,
            format=fmt,
            encoding="utf-8",
            rotation=rotation,
            retention=retention,
            backtrace=False,
            diagnose=False,
            enqueue=True,
        )

    _configure_std_logging_intercept(debug=debug, level=normalized_level)
    _INITIALIZED = True
