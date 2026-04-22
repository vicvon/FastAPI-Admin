from __future__ import annotations

from functools import lru_cache

from common.module_registry import ModuleManifest


@lru_cache(maxsize=1)
def get_module_manifests() -> tuple[ModuleManifest, ...]:
    from modules.admin.manifest import module_manifest as admin_manifest
    from modules.label_manager.manifest import module_manifest as label_manager_manifest

    return (admin_manifest, label_manager_manifest)
