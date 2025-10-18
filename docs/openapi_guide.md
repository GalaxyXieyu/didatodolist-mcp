# Dida365 Open API 指南

本文档为 Dida365 Open API 的整体指南与认证流程说明，包含入门、OAuth2 授权与请求示例，便于快速上手。

## 简介（Introduction）

欢迎阅读 Dida365 Open API 文档。Dida365 是一款强大的任务管理应用，帮助用户轻松管理与组织日常任务、截止日期与项目。通过 Dida365 Open API，开发者可以将 Dida365 的任务管理能力集成到自有应用中，为用户提供无缝的使用体验。

## 快速开始（Getting Started）

开始使用 Dida365 Open API 前，需要先在开发者中心注册应用并获取 `client_id` 与 `client_secret`。请访问 [Dida365 开发者中心](https://developer.dida365.com/manage) 进行注册。注册完成后，你将获得 `client_id` 与 `client_secret`，用于后续请求的身份认证。

## 认证（Authorization）

### 获取 Access Token（Get Access Token）

调用 Dida365 Open API 需要为目标用户获取访问令牌（access token）。Dida365 采用 OAuth2 协议颁发 access token。

#### 第一步（First Step）

将用户重定向到 Dida365 授权页：<https://dida365.com/oauth/authorize>。所需参数如下：

| 名称            | 说明                                                                 |
| --------------- | -------------------------------------------------------------------- |
| `client_id`     | 应用唯一标识（Application unique id）                                |
| `scope`         | 以空格分隔的权限范围；当前可用范围：`tasks:write tasks:read`         |
| `state`         | 原样回传到重定向 URL，用于防重放/状态保持                           |
| `redirect_uri`  | 用户在应用中配置的重定向 URL                                         |
| `response_type` | 固定为 `code`                                                        |

示例：

<https://dida365.com/oauth/authorize?scope=scope&client_id=client_id&state=state&redirect_uri=redirect_uri&response_type=code>

#### 第二步（Second Step）

用户授权通过后，Dida365 会携带授权码（authorization code）回跳至你的应用 `redirect_uri`（以查询参数方式附带）。

| 名称    | 说明                                         |
| ------- | -------------------------------------------- |
| `code`  | 用于后续换取 access token 的授权码           |
| `state` | 第一步传入的 `state` 参数，按原值返回        |

#### 第三步（Third Step）

使用第二步得到的授权码换取 access token。向 `https://dida365.com/oauth/token` 发起 POST 请求（Content-Type: `application/x-www-form-urlencoded`），参数如下：

| 名称             | 说明                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------ |
| `client_id`      | 使用 Basic Auth 放在请求 HEADER 中的用户名                                           |
| `client_secret`  | 使用 Basic Auth 放在请求 HEADER 中的密码                                             |
| `code`           | 第二步获取到的授权码                                                                 |
| `grant_type`     | 授权类型，目前仅支持 `authorization_code`                                            |
| `scope`          | 以空格分隔的权限范围；当前可用：`tasks:write`、`tasks:read`                          |
| `redirect_uri`   | 用户配置的重定向 URL                                                                  |

响应中会返回用于 OpenAPI 请求认证的 `access_token`：

```json
{
  "access_token": "access token value"
}
```

#### 调用 OpenAPI（Request OpenAPI）

在请求头中设置 `Authorization`，值为 `Bearer <access token value>`：

```
Authorization: Bearer e*****b
```
