from typing import Any


class AppError(Exception):
    """应用基础异常类"""

    def __init__(self, code: int, message: str, data: Any | None = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class BusinessError(AppError):
    """通用业务异常"""

    def __init__(
        self,
        message: str = "业务操作失败",
        code: int = 400,
        data: Any | None = None,
    ):
        super().__init__(code=code, message=message, data=data)


class AuthenticationError(AppError):
    """认证失败异常"""

    def __init__(
        self,
        message: str = "认证失败",
        code: int = 401,
        data: Any | None = None,
    ):
        super().__init__(code=code, message=message, data=data)


class PermissionError(AppError):
    """权限不足异常"""

    def __init__(
        self,
        message: str = "无权限执行该操作",
        code: int = 403,
        data: Any | None = None,
    ):
        super().__init__(code=code, message=message, data=data)


class NotFoundError(AppError):
    """资源不存在异常"""

    def __init__(self, message: str = "Resource not found", data: Any | None = None):
        super().__init__(code=404, message=message, data=data)


class ValidationError(AppError):
    """数据验证异常"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(code=400, message=message)


class InfrastructureError(AppError):
    """基础设施异常，如缓存、锁、内部运行时故障。"""

    def __init__(
        self,
        message: str = "基础设施异常",
        code: int = 500,
        data: Any | None = None,
    ):
        super().__init__(code=code, message=message, data=data)


class ExternalServiceError(AppError):
    """外部依赖异常，如 Redis、第三方服务、消息系统等。"""

    def __init__(
        self,
        message: str = "外部依赖异常",
        code: int = 502,
        data: Any | None = None,
    ):
        super().__init__(code=code, message=message, data=data)
