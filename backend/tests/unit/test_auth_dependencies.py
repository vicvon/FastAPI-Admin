from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from common.auth import CurrentPrincipal
from common.exceptions import PermissionError
from modules.admin.api import dependencies as admin_dependencies


class _FakeUserRepo:
    def __init__(self, user):
        self._user = user

    async def get(self, user_id: int):
        assert user_id == self._user.id
        return self._user


class _FakeChecker:
    def __init__(self, should_raise: bool):
        self.should_raise = should_raise

    async def check_permission(self, user_id: int, resource: str, action: str) -> None:
        assert user_id == 99
        assert resource == "/api/v1/labels"
        assert action == "GET"
        if self.should_raise:
            raise PermissionError("Forbidden")


@pytest.mark.asyncio
async def test_resolve_authenticated_user_returns_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = SimpleNamespace(
        id=99,
        username="admin",
        is_active=True,
        token_version=2,
    )

    class _FakeTokenService:
        async def is_access_token_revoked(self, payload):
            return False

    monkeypatch.setattr(
        admin_dependencies, "decode_access_token", lambda _: {"sub": "99", "tv": 2}
    )
    monkeypatch.setattr(admin_dependencies, "TokenService", _FakeTokenService)

    resolved = await admin_dependencies._resolve_authenticated_user(
        token="token",
        user_repo=_FakeUserRepo(user),
    )

    assert resolved.username == "admin"


@pytest.mark.asyncio
async def test_require_permission_returns_403_when_checker_denies() -> None:
    dependency = admin_dependencies.require_permission()
    principal = CurrentPrincipal(
        user_id=99,
        username="admin",
        is_active=True,
        token_version=1,
    )
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/labels",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await dependency(
            request=request,
            current_user=principal,
            checker=_FakeChecker(should_raise=True),
        )

    assert exc_info.value.status_code == 403
