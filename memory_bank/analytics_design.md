# 统计分析功能设计

## 功能概述
此文档定义了滴答清单MCP服务的统计分析功能，包括任务完成情况统计和关键词分析。

## 分析类型

### 1. 时间段任务统计
提供特定时间范围内（如本周、本月、自定义时间段）的任务完成情况统计。

#### 接口定义
```python
analyze_tasks_by_time_period(period="week", start_date=None, end_date=None) -> dict
```

#### 参数说明
- `period`: 预定义时间段（"day", "week", "month", "year"）
- `start_date`/`end_date`: 自定义时间范围（可选）

#### 返回数据结构
```json
{
  "period": "week",
  "start_date": "2023-06-01",
  "end_date": "2023-06-07",
  "total_tasks": 25,
  "completed_tasks": 18,
  "completion_rate": 72,
  "daily_stats": [
    {"date": "2023-06-01", "completed": 3, "created": 5},
    {"date": "2023-06-02", "completed": 4, "created": 2},
    // ...其它日期
  ],
  "trends": {
    "completion_trend": "increasing", // increasing, decreasing, stable
    "creation_trend": "stable"
  }
}
```

### 2. 项目任务统计
按项目分组统计任务完成情况，了解不同项目的进展。

#### 接口定义
```python
analyze_tasks_by_project(period=None, start_date=None, end_date=None) -> dict
```

#### 参数说明
- `period`: 预定义时间段（可选）
- `start_date`/`end_date`: 自定义时间范围（可选）

#### 返回数据结构
```json
{
  "period": "month",
  "start_date": "2023-06-01",
  "end_date": "2023-06-30",
  "projects": [
    {
      "project_id": "proj123",
      "project_name": "工作任务",
      "total_tasks": 15,
      "completed_tasks": 12,
      "completion_rate": 80,
      "avg_completion_time": "3.2 days"
    },
    // ...其它项目
  ],
  "top_projects": {
    "by_completion_rate": ["项目A", "项目B", "项目C"],
    "by_task_count": ["项目B", "项目A", "项目D"]
  }
}
```

### 3. 任务关键词分析
分析任务标题和内容中的关键词频率，生成词云数据。

#### 接口定义
```python
analyze_task_keywords(period=None, start_date=None, end_date=None, project_id=None, min_frequency=2) -> dict
```

#### 参数说明
- `period`: 预定义时间段（可选）
- `start_date`/`end_date`: 自定义时间范围（可选）
- `project_id`: 按项目筛选（可选）
- `min_frequency`: 最小词频（可选）

#### 返回数据结构
```json
{
  "period": "month",
  "total_tasks_analyzed": 45,
  "keywords": [
    {"word": "会议", "count": 12, "weight": 0.8},
    {"word": "报告", "count": 10, "weight": 0.7},
    {"word": "开发", "count": 8, "weight": 0.6},
    // ...更多关键词
  ],
  "wordcloud_data": {
    "会议": 12,
    "报告": 10,
    "开发": 8,
    // ...更多关键词
  },
  "categories": {
    "工作": ["会议", "报告", "客户"],
    "学习": ["开发", "学习", "读书"],
    // ...可能的分类
  }
}
```

### 4. 目标进度分析
根据已完成任务分析目标的完成进度和预计完成时间。

#### 接口定义
```python
analyze_goal_progress(goal_id=None, goal_type=None) -> dict
```

#### 参数说明
- `goal_id`: 特定目标ID（可选）
- `goal_type`: 目标类型筛选（可选）

#### 返回数据结构
```json
{
  "goals": [
    {
      "goal_id": "goal123",
      "title": "完成项目A",
      "type": "phase",
      "current_progress": 65,
      "progress_history": [
        {"date": "2023-06-01", "progress": 20},
        {"date": "2023-06-07", "progress": 45},
        {"date": "2023-06-14", "progress": 65}
      ],
      "estimated_completion": "2023-07-02",
      "related_tasks": {
        "total": 12,
        "completed": 8
      }
    },
    // ...其它目标
  ],
  "summary": {
    "total_goals": 5,
    "on_track": 3,
    "at_risk": 1,
    "behind": 1
  }
}
```

## 算法设计

### 关键词提取算法
1. **预处理**:
   - 合并所有任务标题和内容
   - 分词（使用jieba库）
   - 去除停用词
   
2. **词频统计**:
   - 计算每个词的出现频率
   - 应用TF-IDF算法增强重要词的权重
   
3. **后处理**:
   - 筛选高于最小频率阈值的词
   - 计算权重并归一化（0-1范围）
   - 生成适用于词云生成的数据格式

### 任务与目标匹配算法
1. **提取关键特征**:
   - 从任务中提取关键词
   - 从目标的keywords字段获取关键词
   
2. **计算相似度**:
   - 使用余弦相似度计算任务与目标的匹配度
   - 考虑关键词权重
   
3. **排序与输出**:
   - 按相似度降序排列
   - 返回匹配度高于阈值的目标列表

## 技术实现

### 依赖库
- **pandas**: 数据处理和分析
- **jieba**: 中文分词
- **wordcloud**: 词云生成(可选，仅提供数据)
- **numpy**: 数学计算支持
- **matplotlib**: 图表生成(可选)

### 性能优化
1. 缓存数据减少API调用
2. 增量分析避免重复计算
3. 后台预计算常用统计数据