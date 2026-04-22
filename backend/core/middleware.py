import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from core.context import (
    RequestContext,
    app_id_ctx,
    ip_address_ctx,
    request_id_ctx,
    user_agent_ctx,
)


class ContextMiddleware(BaseHTTPMiddleware):
    """
    请求上下文中间件
    1. 生成 Request ID
    2. 提取 IP 和 User-Agent
    3. 初始化 ContextVars
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token_request_id = request_id_ctx.set(request_id)
        RequestContext.set_request_id(request_id)

        ip = request.client.host if request.client else "127.0.0.1"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        token_ip = ip_address_ctx.set(ip)
        RequestContext.set_ip(ip)

        ua = request.headers.get("User-Agent", "")
        token_ua = user_agent_ctx.set(ua)
        RequestContext.set_user_agent(ua)

        header_app_id = request.headers.get("X-App-ID")
        token_app_id = None
        if header_app_id:
            token_app_id = app_id_ctx.set(header_app_id)
            RequestContext.set_app_id(header_app_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token_request_id)
            ip_address_ctx.reset(token_ip)
            user_agent_ctx.reset(token_ua)
            if token_app_id is not None:
                app_id_ctx.reset(token_app_id)
