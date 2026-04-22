from common.ports.data_scope import IDataScopeResolver
from common.ports.permission import IPermissionChecker, IPermissionManager
from common.ports.principal import ICurrentPrincipalResolver

__all__ = [
    "ICurrentPrincipalResolver",
    "IDataScopeResolver",
    "IPermissionChecker",
    "IPermissionManager",
]
