from modules.admin.domain.entities import Role
from modules.admin.domain.role_code import build_role_code
from modules.admin.domain.system_semantics import is_protected_role


def test_is_protected_role_returns_true_for_system_flag() -> None:
    role = Role(id=200, name="system", code="role:any", is_system=True)

    assert is_protected_role(role) is True


def test_is_protected_role_returns_true_for_builtin_code() -> None:
    role = Role(id=200, name="admin", code="role:admin", is_system=False)

    assert is_protected_role(role) is True


def test_build_role_code_for_api_created_role_uses_id() -> None:
    assert build_role_code("anything", 123) == "role:123"
