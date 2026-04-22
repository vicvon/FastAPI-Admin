from fastapi import Request

from app_setup.module_registry import get_module_manifests
from app_setup.resource_registry import (
    init_resource_registry,
    resolve_required_resource_action,
)


def test_module_registry_contains_current_template_modules() -> None:
    manifests = get_module_manifests()

    assert {manifest.name for manifest in manifests} == {"admin", "label_manager"}


def test_resource_registry_collects_module_resource_registrations() -> None:
    registry = init_resource_registry()

    action = registry.resolve("/api/v1/labels", "GET")

    assert action is not None
    assert action.resource_type == "labels"
    assert action.action == "view"


def test_resource_registry_resolves_action_from_request_route() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/labels",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "root_path": "",
            "route": type("RouteStub", (), {"path": "/api/v1/labels"})(),
        }
    )

    action = resolve_required_resource_action(request)

    assert action.resource_type == "labels"
    assert action.action == "view"
