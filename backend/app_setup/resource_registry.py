from __future__ import annotations

from fastapi import HTTPException, Request, status

from app_setup.module_registry import get_module_manifests
from common.resource_registry import ResourceAction, ResourceRegistry

resource_registry = ResourceRegistry()


def init_resource_registry() -> ResourceRegistry:
    registry = ResourceRegistry()
    for manifest in get_module_manifests():
        for item in manifest.resource_registrations:
            registry.register(item.path_pattern, item.method, item.action)
    return registry


def refresh_resource_registry() -> ResourceRegistry:
    global resource_registry
    resource_registry = init_resource_registry()
    return resource_registry


def resolve_required_resource_action(request: Request) -> ResourceAction:
    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)
    action = resource_registry.resolve(route_path, request.method)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resource mapping not found",
        )
    return action


refresh_resource_registry()

__all__ = [
    "ResourceAction",
    "ResourceRegistry",
    "init_resource_registry",
    "refresh_resource_registry",
    "resolve_required_resource_action",
    "resource_registry",
]
