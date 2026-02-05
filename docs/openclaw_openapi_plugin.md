# OpenClaw 原生插件：滴答清单（Open API）

该插件直接调用滴答清单官方 Open API，不依赖 MCP 服务。

## 前置条件

- 在滴答开放平台创建应用，获得 Client ID 与 Client Secret。
- 配置 Redirect URI（建议 http://localhost:38000/callback）。

## 安装插件

在仓库根目录执行：

```bash
openclaw plugins install -l ./openclaw-openapi-plugin
```

## 配置示例

编辑 OpenClaw 配置文件（默认 `~/.openclaw/openclaw.json`），加入插件条目：

```json
{
  "plugins": {
    "enabled": true,
    "entries": {
      "dida-openapi": {
        "enabled": true,
        "config": {
          "clientId": "<YOUR_CLIENT_ID>",
          "clientSecret": "<YOUR_CLIENT_SECRET>",
          "redirectUri": "http://localhost:38000/callback",
          "accessToken": "<ACCESS_TOKEN>",
          "refreshToken": "<REFRESH_TOKEN>",
          "timeoutMs": 15000,
          "timeZone": "America/Los_Angeles",
          "autoRefresh": true
        }
      }
    }
  }
}
```

## 获取 Token（推荐流程）

1) 使用 dida_auth_url 工具生成授权链接。
2) 浏览器打开链接完成授权，复制返回的 code。
3) 使用 dida_exchange_code 工具换取 access_token / refresh_token。
4) 将返回的 token 写入 OpenClaw 配置文件以持久化。

提示：自动刷新仅更新运行时内存，配置文件需要手动更新。
修改配置后请执行 `openclaw gateway restart` 使其生效。

## 使用本地脚本自动写入

```bash
python3 scripts/oauth_openclaw.py
```

该脚本会读取 `~/.openclaw/openclaw.json` 的 `dida-openapi` 配置，完成授权并把 token 写回同一文件，同时确保插件启用并把 `dida-openapi` 加入 allowlist。

## 允许工具

本插件注册的工具标记为 optional，请在 allowlist 中显式允许：

```json
{
  "tools": {
    "allow": ["dida-openapi"]
  }
}
```

## 已提供的工具

- dida_auth_url
- dida_exchange_code
- dida_refresh_token
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

- 未配置 accessToken：请先完成 OAuth 授权。
- 401：检查 refreshToken 与 clientId/clientSecret 是否有效，或手动刷新。
