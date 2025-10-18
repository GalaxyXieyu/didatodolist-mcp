# Dida365 Open API - 数据模型（Definitions）

汇总接口中涉及的核心数据结构，便于理解字段含义与取值范围。

## ChecklistItem（清单子项）

| 字段            | 说明                                                           | 类型                |
| --------------- | -------------------------------------------------------------- | ------------------- |
| `id`            | 子任务标识                                                     | string              |
| `title`         | 子任务标题                                                     | string              |
| `status`        | 子任务完成状态；取值：未完成 `0`，已完成 `1`                  | integer (int32)     |
| `completedTime` | 子任务完成时间 `yyyy-MM-dd'T'HH:mm:ssZ`                       | string (date-time)  |
| `isAllDay`      | 是否全天                                                       | boolean             |
| `sortOrder`     | 子任务排序值                                                   | integer (int64)     |
| `startDate`     | 子任务开始时间 `yyyy-MM-dd'T'HH:mm:ssZ`                       | string (date-time)  |
| `timeZone`      | 子任务时区，例如 `America/Los_Angeles`                         | string              |

## Task（任务）

| 字段           | 说明                                                                                  | 类型                   |
| -------------- | ------------------------------------------------------------------------------------- | ---------------------- |
| `id`           | 任务标识                                                                              | string                 |
| `projectId`    | 所属项目 ID                                                                           | string                 |
| `title`        | 任务标题                                                                              | string                 |
| `isAllDay`     | 是否全天                                                                              | boolean                |
| `completedTime`| 任务完成时间 `yyyy-MM-dd'T'HH:mm:ssZ`                                                 | string (date-time)     |
| `content`      | 任务内容                                                                              | string                 |
| `desc`         | 清单描述                                                                              | string                 |
| `dueDate`      | 任务截止时间 `yyyy-MM-dd'T'HH:mm:ssZ`                                                 | string (date-time)     |
| `items`        | 子任务列表                                                                            | `<ChecklistItem>` array|
| `priority`     | 任务优先级；取值：无 `0`，低 `1`，中 `3`，高 `5`                                      | integer (int32)        |
| `reminders`    | 提醒触发器列表，如 `["TRIGGER:P0DT9H0M0S", "TRIGGER:PT0S"]`                        | `<string>` array       |
| `repeatFlag`   | 重复规则，如 `RRULE:FREQ=DAILY;INTERVAL=1`                                            | string                 |
| `sortOrder`    | 排序值                                                                                | integer (int64)        |
| `startDate`    | 开始时间 `yyyy-MM-dd'T'HH:mm:ssZ`                                                     | string (date-time)     |
| `status`       | 完成状态；取值：未完成 `0`，已完成 `2`                                                | integer (int32)        |
| `timeZone`     | 时区，例如 `America/Los_Angeles`                                                      | string                 |
| `kind`         | 任务类型：`TEXT`、`NOTE`、`CHECKLIST`                                                 | string                 |

## Project（项目）

| 字段        | 说明                                   | 类型            |
| ----------- | -------------------------------------- | --------------- |
| `id`        | 项目标识                               | string          |
| `name`      | 项目名称                               | string          |
| `color`     | 项目颜色                               | string          |
| `sortOrder` | 排序值                                 | integer (int64) |
| `closed`    | 是否已关闭                             | boolean         |
| `groupId`   | 项目分组标识                           | string          |
| `viewMode`  | 视图模式：`list`、`kanban`、`timeline` | string          |
| `permission`| 权限：`read`、`write` 或 `comment`     | string          |
| `kind`      | 项目类型：`TASK` 或 `NOTE`             | string          |

## Column（列）

| 字段        | 说明         | 类型            |
| ----------- | ------------ | --------------- |
| `id`        | 列标识       | string          |
| `projectId` | 项目标识     | string          |
| `name`      | 列名称       | string          |
| `sortOrder` | 排序值       | integer (int64) |

## ProjectData（项目数据聚合）

| 字段       | 说明               | 类型         |
| ---------- | ------------------ | ------------ |
| `project`  | 项目信息           | `Project`    |
| `tasks`    | 项目下未完成的任务 | `<Task>` array |
| `columns`  | 项目下的列         | `<Column>` array |
