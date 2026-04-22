from __future__ import annotations

from common.module_registry import ModuleManifest, ResourceRegistration
from common.resource_registry import ResourceAction
from modules.label_manager.api.v1.router import router as label_manager_router

module_manifest = ModuleManifest(
    name="label_manager",
    router=label_manager_router,
    resource_registrations=(
        ResourceRegistration(
            path_pattern="/api/v1/labels",
            method="GET",
            action=ResourceAction(
                resource_type="labels",
                action="view",
                primary_resource="labels",
            ),
        ),
        ResourceRegistration(
            path_pattern="/api/v1/labels/{id}",
            method="PUT",
            action=ResourceAction(
                resource_type="labels",
                action="edit",
                primary_resource="labels",
            ),
        ),
        ResourceRegistration(
            path_pattern="/api/v1/labels/{id}",
            method="DELETE",
            action=ResourceAction(
                resource_type="labels",
                action="edit",
                primary_resource="labels",
            ),
        ),
    ),
)
