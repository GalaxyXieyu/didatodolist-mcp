# Dida365 Open API - 项目（Project）接口

提供项目（清单）的查询、创建、更新与删除能力。

## 获取用户的项目列表（Get User Project）

```
GET /open/v1/project
```

### 响应（Responses）

| HTTP Code | 描述        | Schema            |
| --------- | ----------- | ----------------- |
| 200       | 成功        | `<Project> array` |
| 401       | 未授权      | -                 |
| 403       | 禁止访问    | -                 |
| 404       | 未找到      | -                 |

### 示例（Example）

请求

```http
GET /open/v1/project HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```

响应

```json
[
  {
    "id": "6226ff9877acee87727f6bca",
    "name": "project name",
    "color": "#F18181",
    "closed": false,
    "groupId": "6436176a47fd2e05f26ef56e",
    "viewMode": "list",
    "permission": "write",
    "kind": "TASK"
  }
]
```

## 根据项目 ID 获取项目信息（Get Project By ID）

```
GET /open/v1/project/{projectId}
```

### 路径参数（Parameters）

| 类型 | 名称                       | 说明         | 类型   |
| ---- | -------------------------- | ------------ | ------ |
| Path | `projectId`（必填）        | 项目标识     | string |

### 响应（Responses）

| HTTP Code | 描述        | Schema  |
| --------- | ----------- | ------- |
| 200       | 成功        | Project |
| 401       | 未授权      | -       |
| 403       | 禁止访问    | -       |
| 404       | 未找到      | -       |

### 示例（Example）

请求

```http
GET /open/v1/project/{{projectId}} HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```

响应

```json
{
  "id": "6226ff9877acee87727f6bca",
  "name": "project name",
  "color": "#F18181",
  "closed": false,
  "groupId": "6436176a47fd2e05f26ef56e",
  "viewMode": "list",
  "kind": "TASK"
}
```

## 获取项目及其数据（Get Project With Data）

```
GET /open/v1/project/{projectId}/data
```

### 路径参数（Parameters）

| 类型 | 名称                       | 说明         | 类型   |
| ---- | -------------------------- | ------------ | ------ |
| Path | `projectId`（必填）        | 项目标识     | string |

### 响应（Responses）

| HTTP Code | 描述        | Schema      |
| --------- | ----------- | ----------- |
| 200       | 成功        | ProjectData |
| 401       | 未授权      | -           |
| 403       | 禁止访问    | -           |
| 404       | 未找到      | -           |

### 示例（Example）

请求

```http
GET /open/v1/project/{{projectId}}/data HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```

响应

```json
{
  "project": {
    "id": "6226ff9877acee87727f6bca",
    "name": "project name",
    "color": "#F18181",
    "closed": false,
    "groupId": "6436176a47fd2e05f26ef56e",
    "viewMode": "list",
    "kind": "TASK"
  },
  "tasks": [
    {
      "id": "6247ee29630c800f064fd145",
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
          "title": "Subtask Title",
          "sortOrder": 12345,
          "startDate": "2019-11-13T03:00:00+0000",
          "isAllDay": false,
          "timeZone": "America/Los_Angeles",
          "completedTime": "2019-11-13T03:00:00+0000"
        }
      ]
    }
  ],
  "columns": [
    {
      "id": "6226ff9e76e5fc39f2862d1b",
      "projectId": "6226ff9877acee87727f6bca",
      "name": "Column Name",
      "sortOrder": 0
    }
  ]
}
```

## 创建项目（Create Project）

```
POST /open/v1/project
```

### 请求体字段（Body）

| 字段        | 说明                                   | 类型            |
| ----------- | -------------------------------------- | --------------- |
| `name`      | 项目名称                               | string          |
| `color`     | 项目颜色，例如 `#F18181`               | string          |
| `sortOrder` | 项目排序值                             | integer (int64) |
| `viewMode`  | 视图模式：`list`、`kanban`、`timeline` | string          |
| `kind`      | 项目类型：`TASK`、`NOTE`               | string          |

### 响应（Responses）

| HTTP Code | 描述        | Schema  |
| --------- | ----------- | ------- |
| 200       | 成功        | Project |
| 201       | 已创建      | -       |
| 401       | 未授权      | -       |
| 403       | 禁止访问    | -       |
| 404       | 未找到      | -       |

### 示例（Example）

```http
POST /open/v1/project HTTP/1.1
Host: api.dida365.com
Content-Type: application/json
Authorization: Bearer {{token}}
{
  "name": "project name",
  "color": "#F18181",
  "viewMode": "list",
  "kind": "task"
}
```

响应

```json
{
  "id": "6226ff9877acee87727f6bca",
  "name": "project name",
  "color": "#F18181",
  "sortOrder": 0,
  "viewMode": "list",
  "kind": "TASK"
}
```

## 更新项目（Update Project）

```
POST /open/v1/project/{projectId}
```

### 路径参数（Parameters）

| 类型 | 名称                       | 说明     | 类型   |
| ---- | -------------------------- | -------- | ------ |
| Path | `projectId`（必填）        | 项目标识 | string |

### 请求体字段（Body）

| 字段        | 说明                                   | 类型            |
| ----------- | -------------------------------------- | --------------- |
| `name`      | 项目名称                               | string          |
| `color`     | 项目颜色                               | string          |
| `sortOrder` | 排序值，默认 0                         | integer (int64) |
| `viewMode`  | 视图模式：`list`、`kanban`、`timeline` | string          |
| `kind`      | 项目类型：`TASK`、`NOTE`               | string          |

### 响应（Responses）

| HTTP Code | 描述        | Schema  |
| --------- | ----------- | ------- |
| 200       | 成功        | Project |
| 201       | 已创建      | -       |
| 401       | 未授权      | -       |
| 403       | 禁止访问    | -       |
| 404       | 未找到      | -       |

### 示例（Example）

```http
POST /open/v1/project/{{projectId}} HTTP/1.1
Host: api.dida365.com
Content-Type: application/json
Authorization: Bearer {{token}}

{
  "name": "Project Name",
  "color": "#F18181",
  "viewMode": "list",
  "kind": "TASK"
}
```

响应

```json
{
  "id": "6226ff9877acee87727f6bca",
  "name": "Project Name",
  "color": "#F18181",
  "sortOrder": 0,
  "viewMode": "list",
  "kind": "TASK"
}
```

## 删除项目（Delete Project）

```
DELETE /open/v1/project/{projectId}
```

### 路径参数（Parameters）

| 类型 | 名称                       | 说明     | 类型   |
| ---- | -------------------------- | -------- | ------ |
| Path | `projectId`（必填）        | 项目标识 | string |

### 响应（Responses）

| HTTP Code | 描述        | Schema |
| --------- | ----------- | ------ |
| 200       | 成功        | -      |
| 401       | 未授权      | -      |
| 403       | 禁止访问    | -      |
| 404       | 未找到      | -      |

### 示例（Example）

```http
DELETE /open/v1/project/{{projectId}} HTTP/1.1
Host: api.dida365.com
Authorization: Bearer {{token}}
```
