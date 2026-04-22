from __future__ import annotations

from collections.abc import Callable

from sqlmodel.ext.asyncio.session import AsyncSession

from common.auth import CurrentPrincipal
from common.exceptions import AuthenticationError
from common.ports import ICurrentPrincipalResolver
from core.context import RequestContext
from core.security import TokenService, decode_access_token
from modules.admin.infra.repositories import UserRepository


class AdminCurrentPrincipalResolver(ICurrentPrincipalResolver):
    """由 admin 用户域提供的共享身份解析实现。"""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        token_service: TokenService | None = None,
    ):
        self._session_factory = session_factory
        self._token_service = token_service or TokenService()

    async def resolve(self, token: str) -> CurrentPrincipal:
        try:
            payload = decode_access_token(token)
        except ValueError as exc:
            raise AuthenticationError("用户认证失败") from exc

        if await self._token_service.is_access_token_revoked(payload):
            raise AuthenticationError("用户认证失败")

        user_id = self._extract_user_id(payload)
        async with self._session_factory() as session:
            user = await UserRepository(session).get(user_id)

        if user is None or user.id is None or not user.is_active:
            raise AuthenticationError("用户认证失败")
        if int(payload.get("tv", 0)) != int(user.token_version):
            raise AuthenticationError("用户认证失败")

        RequestContext.set_user_id(user.id)
        RequestContext.set_user_name(user.username)
        return CurrentPrincipal(
            user_id=int(user.id),
            username=user.username,
            is_active=bool(user.is_active),
            token_version=int(user.token_version),
        )

    def _extract_user_id(self, payload: dict[str, object]) -> int:
        subject = payload.get("sub")
        if subject is None:
            raise AuthenticationError("用户认证失败")
        try:
            return int(subject)
        except (TypeError, ValueError) as exc:
            raise AuthenticationError("用户认证失败") from exc
