# 本地调试指南：MCP Inspector 与 mcp-cli

## 前置

- 已完成 OAuth 授权（.env 中有 DIDA_ACCESS_TOKEN，或 oauth_config.json 存在）
- 已设置 `MCP_API_KEY`

## 启动 MCP（SSE）

```bash
export MCP_API_KEY=your-strong-key
python main.py --sse --host 127.0.0.1 --port 3000
# SSE 入口： http://127.0.0.1:3000/sse
```

当前 fastmcp 版本不支持 authenticate 参数时，服务已内置 ASGI 中间件校验 Header：`x-api-key`。

## 使用 MCP Inspector（可视化）

```bash
npx @modelcontextprotocol/inspector
```

连接设置：

- Transport: SSE
- URL: `http://127.0.0.1:3000/sse`
- Headers: `x-api-key: your-strong-key`

连接后，UI 会列出所有工具，可直接在页面填参数测试。

## 使用 mcp-cli（命令行）

```bash
npx @wong2/mcp-cli
```

选择 SSE 连接并设置 Headers：

- URL: `http://127.0.0.1:3000/sse`
- Headers: `x-api-key=your-strong-key`

然后可以列工具、执行调用以验证行为。

## 常见问题

- 401 未授权：确认 `x-api-key` 与服务端的 `MCP_API_KEY` 一致；或服务未使用 SSE 中间件（升级代码）。
- 连接不上：确认 SSE URL 正确（带 `/sse` 路径），服务正在 3000 端口运行。
- API 返回 401：OAuth token 过期。使用 `python scripts/oauth_authenticate.py --port 38000` 重新授权（.env 将写入新 token）。
