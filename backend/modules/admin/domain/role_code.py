from __future__ import annotations


def build_role_code(_name: str, role_id: int | None = None) -> str:
    _ = _name
    if role_id is not None:
        return f"role:{role_id}"
    return "role:custom"
