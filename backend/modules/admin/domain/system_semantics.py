from __future__ import annotations

from modules.admin.domain.entities import Role

LEGACY_SYSTEM_USER_ID = 1
LEGACY_SYSTEM_ROLE_ID = 1
SYSTEM_ROLE_CODES = frozenset(
    {"role:admin", "role:super-admin", "role:system-admin", "role:system_admin"}
)


def is_protected_role(role: Role | None) -> bool:
    if role is None:
        return False
    if role.is_system:
        return True
    if role.id == LEGACY_SYSTEM_ROLE_ID:
        return True
    return role.code in SYSTEM_ROLE_CODES
