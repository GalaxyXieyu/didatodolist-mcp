# OpenClaw 插件：滴答清单

本插件会通过本仓库提供的 MCP 服务（SSE）来操作滴答清单任务与项目。

## 前置条件

- 已按 README 完成 OAuth 认证与环境变量配置。
- 已启动 MCP 服务（SSE），默认地址为 http://127.0.0.1:3000/sse。

## 安装插件

在仓库根目录执行：

```bash
openclaw plugins install -l ./openclaw-plugin
```

## 配置示例

编辑 OpenClaw 配置文件（例如 ~/.openclaw/config.json），加入插件条目：

```json
{
  "plugins": {
    "enabled": true,
    "entries": {
      "dida-todo": {
        "enabled": true,
        "config": {
          "sseUrl": "http://127.0.0.1:3000/sse",
          "apiKey": "<你的 MCP_API_KEY>",
          "timeoutMs": 15000,
          "protocolVersion": "2024-11-05"
        }
      }
    }
  }
}
```

本插件注册的工具标记为 optional，请在 allowlist 中显式允许：

```json
{
  "tools": {
    "allow": ["dida-todo"]
  }
}
```

如果你使用按代理配置的 allowlist，可把 dida-todo 加到对应 agent 的工具允许列表中。

## 已提供的工具

- dida_get_tasks
- dida_create_task
- dida_update_task
- dida_complete_task
- dida_delete_task
- dida_get_projects
- dida_create_project
- dida_update_project
- dida_delete_project

## 常见问题

- 连接失败：确认 MCP 服务正在运行，并且配置的 sseUrl 与 MCP_API_KEY 正确。
- 超时：可适当提高 timeoutMs。

