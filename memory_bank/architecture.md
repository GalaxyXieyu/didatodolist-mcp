# 系统架构设计

## 总体架构
新功能将遵循现有MCP服务的模块化设计，添加两个新的工具模块：目标管理和统计分析。

```
滴答清单MCP服务
├── 主服务器 (mcp_server.py)
├── 工具模块
│   ├── task_tools.py (现有)
│   ├── project_tools.py (现有)
│   ├── tag_tools.py (现有)
│   ├── goal_tools.py (新增)
│   └── analytics_tools.py (新增)
├── 数据存储
│   ├── 滴答清单API (远程)
│   └── 本地数据 (goals.csv)
└── 辅助模块
    ├── base_api.py (现有)
    └── utils/ (扩展)
```

## 模块详细设计

### 1. 目标管理模块 (goal_tools.py)
负责目标的CRUD操作和与任务的匹配。

#### 主要组件
- **GoalManager**: 核心类，管理目标数据
- **GoalDataStorage**: 处理CSV文件读写
- **GoalMatcher**: 实现目标与任务匹配算法

#### 主要函数
- **create_goal()**: 创建新目标
- **get_goals()**: 获取目标列表
- **update_goal()**: 更新目标
- **delete_goal()**: 删除目标
- **match_tasks_with_goals()**: 匹配任务与目标

### 2. 统计分析模块 (analytics_tools.py)
负责任务统计和关键词分析。

#### 主要组件
- **TaskAnalyzer**: 核心分析引擎
- **TimeAnalyzer**: 处理时间相关统计
- **ProjectAnalyzer**: 处理项目相关统计
- **KeywordExtractor**: 关键词提取和分析
- **GoalProgressAnalyzer**: 目标进度分析

#### 主要函数
- **analyze_tasks_by_time_period()**: 时间段任务统计
- **analyze_tasks_by_project()**: 项目任务统计
- **analyze_task_keywords()**: 任务关键词分析
- **analyze_goal_progress()**: 目标进度分析

### 3. 辅助工具 (utils/)
提供通用功能支持。

#### 新增组件
- **text_analysis.py**: 文本处理和分析工具
  - 分词
  - 关键词提取
  - 相似度计算
- **date_utils.py**: 日期处理工具
  - 时间段计算
  - 频率解析
- **csv_handler.py**: CSV文件处理工具
  - 读写操作
  - 数据验证
  - 备份机制

## 数据流程

### 目标管理数据流
1. 用户通过MCP调用目标管理工具
2. 工具函数调用GoalManager执行相应操作
3. GoalManager通过GoalDataStorage读写CSV文件
4. 结果通过MCP返回给用户

### 统计分析数据流
1. 用户通过MCP调用统计分析工具
2. 工具函数调用相应的分析器组件
3. 分析器从滴答清单API获取任务数据
4. 对于目标相关分析，还会从本地CSV读取目标数据
5. 分析结果通过MCP返回给用户

## 集成策略

### MCP服务集成
1. 在mcp_server.py中导入新模块:
```python
from tools.goal_tools import register_goal_tools
from tools.analytics_tools import register_analytics_tools
```

2. 注册新工具到MCP服务器:
```python
def create_server(auth_info):
    # 现有代码...
    
    # 注册工具
    register_task_tools(server, auth_info)
    register_project_tools(server, auth_info)
    register_tag_tools(server, auth_info)
    
    # 新增工具注册
    register_goal_tools(server, auth_info)
    register_analytics_tools(server, auth_info)
    
    # 现有代码...
    return server
```

### 依赖管理
在requirements.txt中添加新依赖:
```
pandas>=1.3.0
jieba>=0.42.1
numpy>=1.20.0
wordcloud>=1.8.1
matplotlib>=3.4.0
scikit-learn>=0.24.0
```

## 扩展性考虑

1. **插件式设计**: 所有分析器和工具都采用模块化设计，便于后续扩展

2. **数据存储抽象**: GoalDataStorage接口允许将来支持其他存储方式(如SQLite)

3. **算法可替换**: 关键词提取和匹配算法设计为可替换组件

4. **缓存机制**: 预留缓存接口，便于后续优化性能

## 安全考虑

1. **数据保护**: 目标数据存储在本地，不上传到远程服务器

2. **备份机制**: CSV文件修改前自动创建备份

3. **输入验证**: 所有用户输入经过严格验证后再处理

4. **错误处理**: 完善的异常处理，防止数据损坏 