from __future__ import annotations

from modules.iam.application.policy_projector import (
    build_role_subject,
    build_user_subject,
    iter_grouping_policies,
    iter_role_policies,
    sync_policies_from_db,
    sync_role_api_policies_incremental,
    sync_user_role_grouping_incremental,
)


def split_permission_code(code: str) -> tuple[str, str]:
    if ":" not in code:
        return code, "*"

    parts = code.rsplit(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return code, "*"


__all__ = [
    "build_role_subject",
    "build_user_subject",
    "iter_grouping_policies",
    "iter_role_policies",
    "split_permission_code",
    "sync_policies_from_db",
    "sync_role_api_policies_incremental",
    "sync_user_role_grouping_incremental",
]
