# 目标数据结构设计

## 数据模型概述
此文档定义了目标管理功能的数据结构，包括不同类型目标的字段和存储格式。

## CSV文件结构
目标数据将存储在`goals.csv`文件中，包含以下字段:

| 字段名 | 类型 | 描述 | 是否必需 |
|-------|------|------|---------|
| id | 字符串 | 目标唯一标识符(UUID) | 是 |
| title | 字符串 | 目标标题 | 是 |
| description | 字符串 | 目标详细描述 | 否 |
| type | 字符串 | 目标类型(phase/permanent/habit) | 是 |
| status | 字符串 | 目标状态(active/completed/abandoned) | 是 |
| created_time | 日期时间 | 创建时间 | 是 |
| modified_time | 日期时间 | 最后修改时间 | 是 |
| start_date | 日期 | 开始日期 | 否 |
| due_date | 日期 | 截止日期(阶段性目标) | 否 |
| frequency | 字符串 | 重复频率(习惯性目标) | 否 |
| keywords | 字符串 | 关键词列表(逗号分隔) | 是 |
| progress | 整数 | 完成进度(0-100) | 是 |
| related_projects | 字符串 | 关联项目ID列表(逗号分隔) | 否 |
| metrics | 字符串 | 度量指标(JSON格式) | 否 |

## 目标类型定义

### 阶段性目标(phase)
有明确开始和结束日期的目标，例如"在六月底前完成项目"。
- 必须包含`due_date`
- 适合有明确截止期限的目标

### 永久性目标(permanent)
长期持续的目标，没有具体截止日期，例如"保持工作与生活平衡"。
- 没有`due_date`
- 通常用于个人长期发展方向

### 习惯性目标(habit)
需要定期执行的目标，例如"每天锻炼30分钟"。
- 必须包含`frequency`
- 频率格式: daily, weekly:1(周一), weekly:1,3,5(周一三五), monthly:1(每月1号)

## 存储实现
1. CSV文件将保存在项目根目录下的`data`文件夹中
2. 实现自动备份机制，每次写入前创建备份
3. 提供数据验证功能，确保数据完整性

## 示例数据
```csv
id,title,description,type,status,created_time,modified_time,start_date,due_date,frequency,keywords,progress,related_projects,metrics
abc123,完成项目报告,第一季度项目总结报告,phase,active,2023-05-01T10:00:00,2023-05-02T14:30:00,2023-05-01,2023-05-31,,报告,项目,总结,50,proj123,{"words":5000}
def456,保持健康生活方式,均衡饮食和适量运动,permanent,active,2023-04-15T08:00:00,2023-04-15T08:00:00,,,daily,健康,运动,饮食,100,,{"days_active":45}
ghi789,每周读书,每周阅读技术书籍,habit,active,2023-04-20T22:15:00,2023-04-20T22:15:00,,,weekly:6,7,阅读,书籍,学习,75,,{"books_read":12}
```

## 数据操作接口
将提供以下接口操作目标数据:

1. 创建目标
   ```python
   create_goal(title, type, **kwargs) -> dict
   ```

2. 获取目标列表
   ```python
   get_goals(type=None, status=None, keywords=None) -> list
   ```

3. 更新目标
   ```python
   update_goal(goal_id, **kwargs) -> dict
   ```

4. 删除目标
   ```python
   delete_goal(goal_id) -> bool
   ```

5. 获取目标详情
   ```python
   get_goal(goal_id) -> dict
   ```

## 搜索和匹配
目标与任务的匹配将基于以下字段:
- 目标的`keywords`字段
- 目标的`title`和`description`中的关键词
- 关联的`related_projects`

匹配算法将计算任务与目标之间的相似度，并返回匹配度最高的目标列表。 