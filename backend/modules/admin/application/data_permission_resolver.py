from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession

from modules.admin.application.scope_handlers import (
    ScopeHandlerRegistry,
    build_default_scope_handler_registry,
)
from modules.admin.domain.entities import DataScope
from modules.admin.domain.repositories import (
    ScopeRuleRepository,
    UserRepository,
)


class DataPermissionResolver:
    def __init__(
        self,
        scope_rule_repo: ScopeRuleRepository,
        user_repo: UserRepository,
        handler_registry: ScopeHandlerRegistry | None = None,
    ):
        self.scope_rule_repo = scope_rule_repo
        self.user_repo = user_repo
        self.handler_registry = (
            handler_registry
            if handler_registry is not None
            else build_default_scope_handler_registry()
        )

    async def build_query_scope(
        self, *, user_id: int, resource_type: str, action: str, model_cls
    ):
        scope = await self.resolve_scope(
            user_id=user_id, resource_type=resource_type, action=action
        )
        handler = self.handler_registry.get(scope)
        return handler.build_query_filter(user_id=user_id, model_cls=model_cls)

    async def can_operate_entity(
        self, *, user_id: int, resource_type: str, action: str, entity
    ) -> bool:
        scope = await self.resolve_scope(
            user_id=user_id, resource_type=resource_type, action=action
        )
        handler = self.handler_registry.get(scope)
        return handler.can_operate_entity(user_id=user_id, entity=entity)

    async def resolve_scope(self, *, user_id: int, resource_type: str, action: str) -> str:
        normalized_resource_type = resource_type.strip().lower()

        user_rule = await self.scope_rule_repo.find_user_scope_rule_with_fallback(
            user_id=user_id,
            resource_type=normalized_resource_type,
            fallback_resource_type="__all__",
        )
        if user_rule is not None:
            return self._pick_scope(
                action=action,
                view_scope=user_rule.view_scope,
                edit_scope=user_rule.edit_scope,
            )

        role_ids = await self.user_repo.get_role_ids(user_id)
        role_scopes: list[DataScope] = []
        for rid in role_ids:
            role_rule = await self.scope_rule_repo.find_role_scope_rule_with_fallback(
                role_id=int(rid),
                resource_type=normalized_resource_type,
                fallback_resource_type="__all__",
            )
            if role_rule is not None:
                role_scopes.append(
                    self._pick_scope_enum(
                        action=action,
                        view_scope=role_rule.view_scope,
                        edit_scope=role_rule.edit_scope,
                    )
                )

        if role_scopes:
            return self._merge_role_scopes(role_scopes).value

        return DataScope.SELF.value

    def _pick_scope(
        self, *, action: str, view_scope: DataScope, edit_scope: DataScope
    ) -> str:
        return self._pick_scope_enum(
            action=action, view_scope=view_scope, edit_scope=edit_scope
        ).value

    def _pick_scope_enum(
        self, *, action: str, view_scope: DataScope, edit_scope: DataScope
    ) -> DataScope:
        normalized_action = action.strip().lower()
        if normalized_action == "view":
            return view_scope
        return edit_scope

    def _merge_role_scopes(self, scopes: list[DataScope]) -> DataScope:
        if DataScope.ALL in scopes:
            return DataScope.ALL
        priority = {
            DataScope.SELF: 0,
            DataScope.CUSTOM: 1,
            DataScope.DEPT: 2,
            DataScope.DEPT_AND_SUB: 3,
        }
        return max(scopes, key=lambda scope: priority.get(scope, 0))


def build_data_permission_resolver(session: AsyncSession) -> DataPermissionResolver:
    from modules.admin.infra.repositories import (
        ScopeRuleRepository as ScopeRuleRepositoryImpl,
        UserRepository as UserRepositoryImpl,
    )

    scope_repo = ScopeRuleRepositoryImpl(session)
    user_repo = UserRepositoryImpl(session)
    return DataPermissionResolver(scope_rule_repo=scope_repo, user_repo=user_repo)
