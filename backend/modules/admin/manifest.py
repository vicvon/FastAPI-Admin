from __future__ import annotations

from common.module_registry import ModuleManifest, RuntimeTaskRegistration
from modules.admin.api.v1.router import router as admin_router
from modules.admin.runtime import start_admin_runtime_tasks, stop_admin_runtime_tasks

module_manifest = ModuleManifest(
    name="admin",
    router=admin_router,
    runtime_tasks=(
        RuntimeTaskRegistration(
            name="role_grant_retry_loop",
            startup=start_admin_runtime_tasks,
            shutdown=stop_admin_runtime_tasks,
        ),
    ),
)
