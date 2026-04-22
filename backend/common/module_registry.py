from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import APIRouter, FastAPI

from common.resource_registry import ResourceAction


@dataclass(frozen=True)
class ResourceRegistration:
    path_pattern: str
    method: str
    action: ResourceAction


@dataclass(frozen=True)
class RuntimeTaskRegistration:
    name: str
    startup: Callable[[FastAPI], Awaitable[None]]
    shutdown: Callable[[FastAPI], Awaitable[None]]


@dataclass(frozen=True)
class ModuleManifest:
    name: str
    router: APIRouter | None = None
    resource_registrations: tuple[ResourceRegistration, ...] = ()
    runtime_tasks: tuple[RuntimeTaskRegistration, ...] = ()
