# Dida365 Open API - 任务（Task）接口

提供任务的查询、创建、更新、完成与删除等能力。

## 根据项目与任务 ID 获取任务（Get Task By Project ID And Task ID）

```
GET /open/v1/project/{projectId}/task/{taskId}
```

### 请求参数（Parameters）

| 类型  | 名称                       | 说明                 | 类型   |
| ----- | -------------------------- | -------------------- | ------ |
| Path  | `projectId`（必填）        | 项目标识             | string |
| Path  | `taskId`（必填）           | 任务标识             | string |

### 响应（Responses）

| HTTP Code | 描述        | Schema |
| --------- | ----------- | ------ |
| 200       | 成功        | Task   |
| 401       | 未授权      | -      |
| 403       | 禁止访问    | -      |
| 404       | 未找到      | -      |

### 示例（Example）

请求

```http
GET /open/v1/project/{{projectId}}/task/{{taskId}} HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```

响应

```json
{
  "id": "63b7bebb91c0a5474805fcd4",
  "isAllDay": true,
  "projectId": "6226ff9877acee87727f6bca",
  "title": "Task Title",
  "content": "Task Content",
  "desc": "Task Description",
  "timeZone": "America/Los_Angeles",
  "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
  "startDate": "2019-11-13T03:00:00+0000",
  "dueDate": "2019-11-14T03:00:00+0000",
  "reminders": ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"],
  "priority": 1,
  "status": 0,
  "completedTime": "2019-11-13T03:00:00+0000",
  "sortOrder": 12345,
  "items": [
    {
      "id": "6435074647fd2e6387145f20",
      "status": 0,
      "title": "Item Title",
      "sortOrder": 12345,
      "startDate": "2019-11-13T03:00:00+0000",
      "isAllDay": false,
      "timeZone": "America/Los_Angeles",
      "completedTime": "2019-11-13T03:00:00+0000"
    }
  ]
}
```

## 创建任务（Create Task）

```
POST /open/v1/task
```

### 请求体字段（Body）

| 字段              | 说明                                                | 类型    |
| ----------------- | --------------------------------------------------- | ------- |
| `title`           | 任务标题                                            | string  |
| `projectId`       | 项目 ID                                             | string  |
| `content`         | 任务内容                                            | string  |
| `desc`            | 清单描述                                            | string  |
| `isAllDay`        | 是否为全天任务                                      | boolean |
| `startDate`       | 开始时间，`yyyy-MM-dd'T'HH:mm:ssZ`                  | date    |
| `dueDate`         | 截止时间，`yyyy-MM-dd'T'HH:mm:ssZ`                  | date    |
| `timeZone`        | 时区                                                | string  |
| `reminders`       | 提醒触发器列表                                      | list    |
| `repeatFlag`      | 重复规则                                            | string  |
| `priority`        | 优先级，默认 `0`                                    | integer |
| `sortOrder`       | 排序值                                              | integer |
| `items`           | 子任务列表                                          | list    |
| `items.title`     | 子任务标题                                          | string  |
| `items.startDate` | 子任务开始时间，`yyyy-MM-dd'T'HH:mm:ssZ`            | date    |
| `items.isAllDay`  | 子任务是否全天                                      | boolean |
| `items.sortOrder` | 子任务排序值                                        | integer |
| `items.timeZone`  | 子任务时区                                          | string  |
| `items.status`    | 子任务完成状态                                      | integer |
| `items.completedTime` | 子任务完成时间，`yyyy-MM-dd'T'HH:mm:ssZ`        | date    |

### 响应（Responses）

| HTTP Code | 描述        | Schema |
| --------- | ----------- | ------ |
| 200       | 成功        | Task   |
| 201       | 已创建      | -      |
| 401       | 未授权      | -      |
| 403       | 禁止访问    | -      |
| 404       | 未找到      | -      |

### 示例（Example）

请求

```http
POST /open/v1/task HTTP/1.1
Host: api.dida365.com
Content-Type: application/json
Authorization: Bearer {{token}}
{
  "title": "Task Title",
  "projectId": "6226ff9877acee87727f6bca"
}
```

响应

```json
{
  "id": "63b7bebb91c0a5474805fcd4",
  "projectId": "6226ff9877acee87727f6bca",
  "title": "Task Title",
  "content": "Task Content",
  "desc": "Task Description",
  "isAllDay": true,
  "startDate": "2019-11-13T03:00:00+0000",
  "dueDate": "2019-11-14T03:00:00+0000",
  "timeZone": "America/Los_Angeles",
  "reminders": ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"],
  "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
  "priority": 1,
  "status": 0,
  "completedTime": "2019-11-13T03:00:00+0000",
  "sortOrder": 12345,
  "items": [
    {
      "id": "6435074647fd2e6387145f20",
      "status": 1,
      "title": "Subtask Title",
      "sortOrder": 12345,
      "startDate": "2019-11-13T03:00:00+0000",
      "isAllDay": false,
      "timeZone": "America/Los_Angeles",
      "completedTime": "2019-11-13T03:00:00+0000"
    }
  ]
}
```

## 更新任务（Update Task）

```
POST /open/v1/task/{taskId}
```

### 路径参数（Parameters）

| 类型 | 名称                   | 说明       | 类型   |
| ---- | ---------------------- | ---------- | ------ |
| Path | `taskId`（必填）       | 任务标识   | string |

### 请求体字段（Body）

| 字段                  | 说明                                             | 类型    |
| --------------------- | ------------------------------------------------ | ------- |
| `id`                  | 任务 ID（与路径 `taskId` 对应）                 | string  |
| `projectId`           | 项目 ID                                         | string  |
| `title`               | 任务标题                                         | string  |
| `content`             | 任务内容                                         | string  |
| `desc`                | 清单描述                                         | string  |
| `isAllDay`            | 是否全天                                         | boolean |
| `startDate`           | 开始时间 `yyyy-MM-dd'T'HH:mm:ssZ`               | date    |
| `dueDate`             | 截止时间 `yyyy-MM-dd'T'HH:mm:ssZ`               | date    |
| `timeZone`            | 时区                                             | string  |
| `reminders`           | 提醒触发器                                       | list    |
| `repeatFlag`          | 重复规则                                         | string  |
| `priority`            | 优先级，默认“normal”                             | integer |
| `sortOrder`           | 排序值                                           | integer |
| `items`               | 子任务列表                                       | list    |
| `items.title`         | 子任务标题                                       | string  |
| `items.startDate`     | 子任务开始时间 `yyyy-MM-dd'T'HH:mm:ssZ`          | date    |
| `items.isAllDay`      | 子任务是否全天                                   | boolean |
| `items.sortOrder`     | 子任务排序值                                     | integer |
| `items.timeZone`      | 子任务时区                                       | string  |
| `items.status`        | 子任务完成状态                                   | integer |
| `items.completedTime` | 子任务完成时间 `yyyy-MM-dd'T'HH:mm:ssZ`          | date    |

### 响应（Responses）

| HTTP Code | 描述        | Schema |
| --------- | ----------- | ------ |
| 200       | 成功        | Task   |
| 201       | 已创建      | -      |
| 401       | 未授权      | -      |
| 403       | 禁止访问    | -      |
| 404       | 未找到      | -      |

### 示例（Example）

请求

```http
POST /open/v1/task/{{taskId}} HTTP/1.1
Host: api.dida365.com
Content-Type: application/json
Authorization: Bearer {{token}}
{
  "id": "{{taskId}}",
  "projectId": "{{projectId}}",
  "title": "Task Title",
  "priority": 1
}
```

响应

```json
{
  "id": "63b7bebb91c0a5474805fcd4",
  "projectId": "6226ff9877acee87727f6bca",
  "title": "Task Title",
  "content": "Task Content",
  "desc": "Task Description",
  "isAllDay": true,
  "startDate": "2019-11-13T03:00:00+0000",
  "dueDate": "2019-11-14T03:00:00+0000",
  "timeZone": "America/Los_Angeles",
  "reminders": ["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"],
  "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
  "priority": 1,
  "status": 0,
  "completedTime": "2019-11-13T03:00:00+0000",
  "sortOrder": 12345,
  "items": [
    {
      "id": "6435074647fd2e6387145f20",
      "status": 1,
      "title": "Item Title",
      "sortOrder": 12345,
      "startDate": "2019-11-13T03:00:00+0000",
      "isAllDay": false,
      "timeZone": "America/Los_Angeles",
      "completedTime": "2019-11-13T03:00:00+0000"
    }
  ],
  "kind": "CHECKLIST"
}
```

## 完成任务（Complete Task）

```
POST /open/v1/project/{projectId}/task/{taskId}/complete
```

### 请求参数（Parameters）

| 类型 | 名称                       | 说明         | 类型   |
| ---- | -------------------------- | ------------ | ------ |
| Path | `projectId`（必填）        | 项目标识     | string |
| Path | `taskId`（必填）           | 任务标识     | string |

### 响应（Responses）

| HTTP Code | 描述        | Schema |
| --------- | ----------- | ------ |
| 200       | 成功        | -      |
| 201       | 已创建      | -      |
| 401       | 未授权      | -      |
| 403       | 禁止访问    | -      |
| 404       | 未找到      | -      |

### 示例（Example）

```http
POST /open/v1/project/{{projectId}}/task/{{taskId}}/complete HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```

## 删除任务（Delete Task）

```
DELETE /open/v1/project/{projectId}/task/{taskId}
```

### 请求参数（Parameters）

| 类型 | 名称                       | 说明         | 类型   |
| ---- | -------------------------- | ------------ | ------ |
| Path | `projectId`（必填）        | 项目标识     | string |
| Path | `taskId`（必填）           | 任务标识     | string |

### 响应（Responses）

| HTTP Code | 描述        | Schema |
| --------- | ----------- | ------ |
| 200       | 成功        | -      |
| 201       | 已创建      | -      |
| 401       | 未授权      | -      |
| 403       | 禁止访问    | -      |
| 404       | 未找到      | -      |

### 示例（Example）

```http
DELETE /open/v1/project/{{projectId}}/task/{{taskId}} HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```
