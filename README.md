# 滴答清单 MCP 服务

滴答清单MCP（Memory-Context-Planning）服务是一个基于Python的后端服务，为用户提供目标管理、任务统计分析、关键词提取和任务-目标匹配等功能。该服务作为滴答清单主应用的辅助功能，帮助用户更好地规划和跟踪个人及团队目标完成情况。

> 最新更新：已从逆向接口切换到官方 OAuth 2.0 + Open API。详见 `docs/openapi_oauth_guide.md`。

> 重要：本项目已全面对齐滴答清单开放平台（/open/v1）端点。
> - 项目：GET/POST/POST(id)/DELETE /open/v1/project
> - 任务：POST /open/v1/task，POST /open/v1/task/{taskId}，POST 完成 /open/v1/project/{projectId}/task/{taskId}/complete，DELETE /open/v1/project/{projectId}/task/{taskId}
> - 汇总任务：官方无全局任务列表，使用 GET /open/v1/project/{projectId}/data 聚合
> - 标签：暂无写接口，当前工具仅提供只读聚合视图

## 主要功能

- **目标管理**：创建、查询、更新和删除个人目标
- **任务统计分析**：生成任务完成情况统计报告
- **关键词提取**：基于任务内容提取关键词（基于jieba分词）
- **任务与目标匹配**：智能匹配任务与相关目标
- **目标完成进度计算**：分析并可视化目标完成进度

## 安装要求

- Python 3.8+
- 滴答清单账号（支持通过token、手机号或邮箱进行认证）

## 快速开始

1) 克隆项目

```bash
git clone https://github.com/GalaxyXieyu/didatodolist-mcp.git
cd didatodolist-mcp
```

2) 安装依赖

```bash
pip install -r requirements.txt
```

3) 配置与认证

推荐使用 OAuth 2.0：

- 方式 A（配置文件）：复制 `oauth_config.json.example` 为 `oauth_config.json`，填入开放平台的 `client_id`、`client_secret`；执行 `python scripts/oauth_authenticate.py --port 38000` 完成一次性授权并写入 `access_token`。
- 方式 B（环境变量配合 .env）：在 `.env` 中配置 `MCP_API_KEY=...`、可选的 `DIDA_CLIENT_ID`、`DIDA_CLIENT_SECRET`、`DIDA_ACCESS_TOKEN`、`DIDA_REFRESH_TOKEN`（会覆盖配置文件）；客户端通过请求头 `x-api-key` 连接。

最小可用步骤（两种任选其一）：

```bash
# A) 配置文件方式
cp oauth_config.json.example oauth_config.json
# 编辑 oauth_config.json，填入 client_id/client_secret
python scripts/oauth_authenticate.py --port 38000  # 生成 access_token 到 oauth_config.json

# B) 仅用 .env 方式
cp .env.example .env
# 编辑 .env，至少填写 MCP_API_KEY、DIDA_CLIENT_ID、DIDA_CLIENT_SECRET
python scripts/oauth_authenticate.py --port 38000  # 成功后写入 DIDA_ACCESS_TOKEN/DIDA_REFRESH_TOKEN 到 .env

# 启动服务（两种方式任何一种完成后即可）
export MCP_API_KEY=your-strong-key  # 或直接在 .env 中配置
python main.py --sse --host 127.0.0.1 --port 3000
# 客户端请求头需带：x-api-key: your-strong-key
```

可选的 `.env` 示例：

```
MCP_API_KEY=your-strong-key
# 以下为覆盖 oauth_config.json 的可选变量
# DIDA_CLIENT_ID=...
# DIDA_CLIENT_SECRET=...
# DIDA_ACCESS_TOKEN=...
# DIDA_REFRESH_TOKEN=...
# OAUTH_CONFIG_PATH=oauth_config.json
```

更多文档：
- 统一 OAuth 指南：`docs/openapi_oauth_guide.md`
- 文档索引：`docs/openapi_index.md`
- 项目接口：`docs/openapi_project.md`
- 任务接口：`docs/openapi_task.md`
- 数据模型定义：`docs/openapi_definitions.md`
- 本地调试（Inspector/mcp-cli）：`docs/dev_debug_inspector.md`

---

## 使用方法

### 启动（stdio）

```bash
python main.py
```

### 启动（SSE，推荐调试）

```bash
python main.py --sse --host 127.0.0.1 --port 3000
```

### 指定配置文件路径（使用 oauth_config.json 时）

```bash
python main.py --config "oauth_config.json"
```

### 安装到 MCP 客户端

```bash
python main.py --install
```

## 端口与鉴权

- 回调端口（一次性授权）：`38000`
  - 与 `oauth_config.json` 的 `redirect_uri` 对齐，例如 `http://localhost:38000/callback`
  - 仅在运行 `scripts/oauth_authenticate.py` 进行 OAuth 授权时临时监听

- MCP 服务端口（SSE）：`3000`
  - 通过 `python main.py --sse --host 127.0.0.1 --port 3000` 启动
  - 客户端连接 MCP 时请在请求头携带 `x-api-key`

示例：

```bash
export MCP_API_KEY="your-strong-key"
python main.py --sse --host 127.0.0.1 --port 3000
# 客户端请求头：x-api-key: your-strong-key
```

## 端口与鉴权（摘要）

- 回调端口：38000（OAuth 回调一次性使用，与 `redirect_uri` 对齐）
- 服务端口：3000（SSE 连接 MCP 服务）
- 鉴权：客户端连接时需携带 `x-api-key`，服务端校验 `MCP_API_KEY`

## 认证机制

系统采用智能认证机制：

1. 优先使用提供的token进行认证
2. 如果没有token但提供了手机号/邮箱和密码，系统会自动登录获取token
3. 获取的token会与账号信息一起保存到配置文件，后续运行时自动使用保存的token
4. 即使用户传入相同的账号密码参数，也会优先使用已保存的token，避免频繁登录触发风控
5. 只有当传入的账号密码与配置文件中的不一致时，才会尝试使用新账号登录

## 功能模块

### 目标管理

目标管理功能允许用户创建、跟踪和管理不同类型的目标：

- **阶段性目标**：有明确截止日期的短期目标
- **常规目标**：长期持续的目标
- **习惯性目标**：需要定期执行的行为习惯

### 统计分析

统计分析功能提供多维度的任务完成情况分析：

- **时间维度**：按日/周/月分析任务完成情况
- **项目维度**：按项目分类统计任务完成率
- **标签维度**：按标签分析任务分布

### 关键词提取

基于jieba分词库，从任务内容中提取关键词，支持生成词云和热度分析。

### 任务-目标匹配

使用内容相似度和关键词匹配算法，智能关联任务与目标，帮助用户将日常任务与长期目标对齐。

## 开发历程

本项目采用了系统化的开发方法，遵循以下开发阶段：

1. **规划阶段**：定义了项目范围、功能要求和技术规范
2. **架构设计**：完成核心数据结构的设计
3. **基础功能开发**：实现核心API和数据访问层
4. **高级功能实现**：开发统计分析和目标匹配算法
5. **优化与测试**：改进性能和用户体验

## 贡献

欢迎提交问题和改进建议！请fork本仓库并创建pull request。

## 许可证

[MIT许可证](LICENSE)
