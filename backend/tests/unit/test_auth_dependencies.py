import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app_setup import auth_dependencies
from common.auth import CurrentPrincipal
from common.exceptions import AuthenticationError, PermissionError


class _FakeChecker:
    def __init__(self, should_raise: bool):
        self.should_raise = should_raise

    async def check_permission(self, user_id: int, resource: str, action: str) -> None:
        assert user_id == 99
        assert resource == "/api/v1/labels"
        assert action == "GET"
        if self.should_raise:
            raise PermissionError("Forbidden")


class _FakePrincipalResolver:
    def __init__(
        self, principal: CurrentPrincipal | None = None, *, fail: bool = False
    ):
        self._principal = principal
        self._fail = fail

    async def resolve(self, token: str) -> CurrentPrincipal:
        assert token == "token"
        if self._fail:
            raise AuthenticationError("用户认证失败")
        assert self._principal is not None
        return self._principal


@pytest.mark.asyncio
async def test_resolve_authenticated_user_returns_user() -> None:
    principal = CurrentPrincipal(
        user_id=99,
        username="admin",
        is_active=True,
        token_version=2,
    )

    resolved = await auth_dependencies._resolve_current_principal(
        token="token",
        resolver=_FakePrincipalResolver(principal),
    )

    assert resolved.username == "admin"


@pytest.mark.asyncio
async def test_resolve_authenticated_user_returns_401_when_resolver_rejects() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await auth_dependencies._resolve_current_principal(
            token="token",
            resolver=_FakePrincipalResolver(fail=True),
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_permission_returns_403_when_checker_denies() -> None:
    dependency = auth_dependencies.require_permission()
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
