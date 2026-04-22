from __future__ import annotations

import casbin


class RbacDomainService:
    """对 Casbin Enforcer 做领域语义封装。"""

    def __init__(self, enforcer: casbin.Enforcer):
        self._enforcer = enforcer

    def evaluate(self, subject: str, resource: str, action: str) -> bool:
        return bool(self._enforcer.enforce(subject, resource, action))
