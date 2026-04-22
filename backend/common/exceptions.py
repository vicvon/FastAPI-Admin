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


class NotFoundError(AppError):
    """资源不存在异常"""

    def __init__(self, message: str = "Resource not found", data: Any | None = None):
        super().__init__(code=404, message=message, data=data)


class ValidationError(AppError):
    """数据验证异常"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(code=400, message=message)
