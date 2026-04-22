from contextvars import ContextVar

# 定义 ContextVars
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[int | None] = ContextVar("user_id", default=None)
user_name_ctx: ContextVar[str | None] = ContextVar("user_name", default=None)
ip_address_ctx: ContextVar[str] = ContextVar("ip_address", default="")
user_agent_ctx: ContextVar[str] = ContextVar("user_agent", default="")
app_id_ctx: ContextVar[str | None] = ContextVar(
    "app_id", default=None
)  # 预留给多应用隔离


class RequestContext:
    """
    上下文管理工具类,用于便捷地获取当前请求的上下文信息
    """

    @staticmethod
    def get_request_id() -> str:
        return request_id_ctx.get()

    @staticmethod
    def set_request_id(request_id: str) -> None:
        request_id_ctx.set(request_id)

    @staticmethod
    def get_user_id() -> int | None:
        return user_id_ctx.get()

    @staticmethod
    def set_user_id(user_id: int) -> None:
        user_id_ctx.set(user_id)

    @staticmethod
    def get_user_name() -> str | None:
        return user_name_ctx.get()

    @staticmethod
    def set_user_name(user_name: str) -> None:
        user_name_ctx.set(user_name)

    @staticmethod
    def get_ip() -> str:
        return ip_address_ctx.get()

    @staticmethod
    def set_ip(ip: str) -> None:
        ip_address_ctx.set(ip)

    @staticmethod
    def get_user_agent() -> str:
        return user_agent_ctx.get()

    @staticmethod
    def set_user_agent(ua: str) -> None:
        user_agent_ctx.set(ua)

    @staticmethod
    def get_app_id() -> str | None:
        return app_id_ctx.get()

    @staticmethod
    def set_app_id(app_id: str) -> None:
        app_id_ctx.set(app_id)
