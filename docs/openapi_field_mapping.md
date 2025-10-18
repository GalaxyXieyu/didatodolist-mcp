# Open API 字段映射说明（/open/v1）

本文档对齐仓库当前实现与官方开放平台文档（见 docs/openapi_*.md），说明各核心对象字段在“请求/响应/内部处理”的映射与默认策略。

参考：
- 项目（Project）：docs/openapi_project.md
- 任务（Task）：docs/openapi_task.md

## 项目 Project

- 读取：直接返回官方字段；工具层仅去除空值
- 创建（POST /open/v1/project）/更新（POST /open/v1/project/{id}）：
  - `name`：string
  - `color`：string（如 `#F18181`）
  - `viewMode`：string（`list` | `kanban` | `timeline`）
  - `kind`：string（`TASK` | `NOTE`）
  - `sortOrder`：int

## 任务 Task

内部一律对齐官方字段；完成态通过“完成接口”实现，不直接写 `status`。

请求（创建/更新）核心字段：
- `title`：string
- `projectId`：string（创建必填；若只提供 `project_name` 则在工具层解析为 `projectId`）
- `content`：string
- `desc`：string（清单描述）
- `isAllDay`：boolean
- `startDate` / `dueDate`：时间字符串，入参使用本地时间（`YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`），适配层转换为 API 需要的 UTC 格式 `yyyy-MM-dd'T'HH:mm:ss.000+0000`
- `timeZone`：string；若设置了上述日期且未显式指定，则默认 `Asia/Shanghai`
- `reminders`：list[string]；若只提供单值 `reminder`（旧参数），适配层自动转为 `reminders: [reminder]`
- `repeatFlag`：string（如 `RRULE:FREQ=DAILY;INTERVAL=1`）
- `priority`：int（官方默认 0）
- `sortOrder`：int
- `items`：array（子任务）
  - `title`：string
  - `startDate` / `completedTime`：本地时间字符串，适配层转换为 API UTC 格式
  - `isAllDay`：boolean
  - `sortOrder`：int
  - `timeZone`：string；若设置日期且未显式指定，默认 `Asia/Shanghai`
  - `status`：int

响应（读取）时间与状态：
- 时间：`startDate` / `dueDate` / `completedTime` / `createdTime` / `modifiedTime` 全部转换为本地字符串 `YYYY-MM-DD HH:MM:SS`；子任务 `items` 的相关时间也同样转换
- 状态：统一补充 `isCompleted`（bool）与 `status`（0/2）

完成/删除：
- 完成：`POST /open/v1/project/{projectId}/task/{taskId}/complete`（工具层在 `update_task_logic(status=2)` 或 `complete_task` 中调用）
- 取消完成：官方文档未提供，当前不支持
- 删除：`DELETE /open/v1/project/{projectId}/task/{taskId}`（必须带 `projectId`）

## 兼容说明

- 旧字段 `reminder`：写入时自动映射为 `reminders` 数组；读取时仍透传 `reminders`
- 旧字段 `tags`：官方未提供标签写接口；任务写入不再发送 `tags` 字段；读取若存在时保留透传

## 错误与重试

- 401：适配层尝试刷新 token；失败时抛出 `APIError`，需重新进行 OAuth 认证
- 其他 HTTP 错误：抛出 `APIError(message, status_code)`，保留服务端返回信息
