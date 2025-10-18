"""
简单的 ASGI 中间件：为 SSE 入口添加 x-api-key 鉴权。
当前 fastmcp 版本不支持 authenticate 参数时，可通过该中间件实现最小可用的 Header 鉴权。
"""

from typing import Callable, Awaitable
import os


class ApiKeyAuthMiddleware:
    def __init__(self, app, header_name: str = "x-api-key", expected_key: str | None = None, sse_path: str = "/sse"):
        self.app = app
        self.header_name = header_name.lower()
        self.expected_key = expected_key or os.environ.get("MCP_API_KEY", "123")
        self.sse_path = sse_path

    async def __call__(self, scope, receive, send):
        # 仅对 HTTP scope 且 SSE 路径做校验，其余直接放行
        if scope.get("type") == "http":
            path = scope.get("path", "")
            if path.startswith(self.sse_path):
                # 提取 header（bytes）
                headers = {k.decode("latin1").lower(): v.decode("latin1") for k, v in scope.get("headers", [])}
                api_key = headers.get(self.header_name)
                if api_key != self.expected_key:
                    body = b"Unauthorized: missing or invalid x-api-key"
                    await send({
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"text/plain; charset=utf-8")],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": body,
                        "more_body": False,
                    })
                    return
        return await self.app(scope, receive, send)


def with_api_key_auth(app, header_name: str = "x-api-key", expected_key: str | None = None, sse_path: str = "/sse"):
    return ApiKeyAuthMiddleware(app, header_name=header_name, expected_key=expected_key, sse_path=sse_path)
