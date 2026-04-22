import pytest

from common.exceptions import PermissionError
from modules.iam.application.permission_checker import PermissionCheckerImpl


class _FakeRbacService:
    def __init__(self, allowed: bool):
        self.allowed = allowed
        self.calls: list[tuple[str, str, str]] = []

    def evaluate(self, subject: str, resource: str, action: str) -> bool:
        self.calls.append((subject, resource, action))
        return self.allowed


@pytest.mark.asyncio
async def test_permission_checker_returns_true_for_allowed_subject() -> None:
    checker = PermissionCheckerImpl(_FakeRbacService(allowed=True))

    allowed = await checker.has_permission(7, "/api/v1/labels", "GET")

    assert allowed is True


@pytest.mark.asyncio
async def test_permission_checker_raises_permission_error_when_denied() -> None:
    checker = PermissionCheckerImpl(_FakeRbacService(allowed=False))

    with pytest.raises(PermissionError) as exc_info:
        await checker.check_permission(7, "/api/v1/labels", "GET")

    assert exc_info.value.code == 403
