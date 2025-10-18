# 滴答清单 OAuth 2.0 统一指南（对齐官方 Open API）

本项目使用官方 OAuth 2.0 与 Open API（/open/v1）进行鉴权与访问，替代早期逆向接口，提升稳定性与安全性。

---

## 总览

- 认证模式：Authorization Code（授权码模式）
- 回调地址：`http://localhost:38000/callback`（本地一次性授权端口）
- 令牌保存：`oauth_config.json`（已加入 .gitignore）
- 官方文档：`https://developer.dida365.com/docs#/openapi`

---

## 双层鉴权模型

- 客户端 → MCP 服务：使用 API Key（`x-api-key` 请求头），由 `MCP_API_KEY` 环境变量配置。
- MCP 服务 → 滴答官方 API：使用 OAuth `access_token`，由 `oauth_config.json` 提供。

说明：38000 端口仅用于“浏览器授权回调”的一次性本地服务器，不是长期监听端口。完成授权后即可关闭。

---

## 一次性 OAuth 授权步骤（生成 oauth_config.json）

1) 准备配置文件（若未创建）

```json
{
  "client_id": "<YOUR_CLIENT_ID>",
  "client_secret": "<YOUR_CLIENT_SECRET>",
  "redirect_uri": "http://localhost:38000/callback"
}
```

2) 运行认证脚本（推荐）

```bash
python scripts/oauth_authenticate.py --port 38000
```

流程：启动本地回调 → 生成授权 URL → 浏览器登陆并授权 → 自动交换令牌 → 保存到 `oauth_config.json`。

3) 远程服务器场景（可选）

```bash
# 在本地做端口转发
ssh -L 8001:localhost:38000 user@your-server
```

---

## 运行 MCP 服务与后续鉴权

1) 设置 API Key（客户端 → MCP）

```bash
export MCP_API_KEY="your-strong-key"
```

2) 启动 MCP（建议 SSE，便于携带请求头）

```bash
python main.py --sse --host 127.0.0.1 --port 3000
```

3) 客户端请求时携带头部

```
x-api-key: your-strong-key
```

4) MCP → 官方 API 使用 `oauth_config.json` 中的 `access_token` 调用接口；若返回 401 且存在 `refresh_token`，会尝试自动刷新。

---

## 官方端点与适配

- 授权 URL：`https://dida365.com/oauth/authorize`
- 令牌 URL：`https://dida365.com/oauth/token`
- 基础 URL：`https://api.dida365.com/open/v1`

项目（Project）
- GET `/project`（列表）
- POST `/project`（创建）
- POST `/project/{projectId}`（更新）
- DELETE `/project/{projectId}`（删除）
- GET `/project/{projectId}/data`（聚合，含 tasks/columns）

任务（Task）
- POST `/task`（创建）
- POST `/task/{taskId}`（更新）
- POST `/project/{projectId}/task/{taskId}/complete`（完成）
- DELETE `/project/{projectId}/task/{taskId}`（删除）
- 说明：无“全局任务列表”端点，需遍历项目并读取 `/project/{id}/data` 聚合。

---

## 代码使用示例

初始化客户端

```python
from tools.official_api import init_api

api = init_api(config_path="oauth_config.json")
```

常见调用

```python
# 获取项目
projects = api.get("/project")

# 创建任务
task = api.post("/task", {"title": "新任务", "projectId": "<project_id>"})

# 更新任务
api.post(f"/task/{task['id']}", {"id": task['id'], "projectId": task['projectId'], "priority": 1})

# 完成任务
api.post(f"/project/{task['projectId']}/task/{task['id']}/complete", {})

# 删除任务
api.delete(f"/project/{task['projectId']}/task/{task['id']}")
```

---

## 令牌刷新与过期处理

- 自动刷新：收到 401 时，若 `refresh_token` 存在会自动刷新并重试请求。
- 手动刷新：`api.refresh_access_token()`。
- 若无 `refresh_token` 或刷新失败：重新执行授权脚本生成新的 `oauth_config.json`。

---

## 安全与合规

- 不要将 `oauth_config.json` 提交到 Git。
- 不要在文档或代码中暴露真实 `client_secret`、`access_token`。
- 建议为 `MCP_API_KEY` 使用强随机值，并避免与默认值 `123` 相同。

---

## 故障排查

- 授权卡住：检查 Redirect URI 是否与开放平台配置一致（含端口与路径）。
- API 返回 401：令牌过期或 Scope 不足；尝试刷新或重新授权。
- 端点 404/500：核对路径是否以 `/open/v1` 开头，参数是否完整。

---

## 相关文件

- `tools/official_api.py`：官方 API 客户端
- `tools/adapter.py`：官方 API 适配层（时间/状态统一）
- `scripts/oauth_authenticate.py`：一次性完整认证脚本
- `scripts/generate_auth_url.py`：仅生成授权 URL
- `oauth_config.json`：OAuth 令牌与凭据（勿入库）

---

文档版本：1.0  ｜  最后更新：2025-10-18
