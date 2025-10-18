"""
任务相关MCP工具
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pytz
from fastmcp import FastMCP
from .adapter import adapter, APIError

# --- 模块级辅助函数 ---

_completed_columns = set()

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期字符串为datetime对象，将UTC时间转换为北京时间"""
    if not date_str:
        return None
        
    local_tz = pytz.timezone('Asia/Shanghai')
    
    try:
        # 处理ISO格式
        if 'T' in date_str:
            base_time = date_str.split('.')[0]
            if date_str.endswith('Z') or '+0000' in date_str:
                # UTC时间，需要转换
                dt = datetime.strptime(base_time.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                dt = pytz.UTC.localize(dt)
                return dt.astimezone(local_tz)
            else:
                # 尝试使用fromisoformat
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.astimezone(local_tz)
                except ValueError:
                    # 假定为本地时间
                    dt = datetime.strptime(base_time.replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                    return local_tz.localize(dt)
    except ValueError:
        pass
        
    try:
        # 标准格式 (假定为本地时间)
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return local_tz.localize(dt)
    except ValueError:
        # 尝试其他可能的格式
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return local_tz.localize(dt)
        except ValueError:
            return None
            
def _format_date_for_api(date_str: Optional[str]) -> Optional[str]:
    """
    将'YYYY-MM-DD HH:MM:SS'格式的日期转换为API所需的'YYYY-MM-DDThh:mm:ss.000+0000'格式
    
    Args:
        date_str: 'YYYY-MM-DD HH:MM:SS'格式的日期字符串
        
    Returns:
        转换后的API格式日期字符串
    """
    if not date_str:
        return None
        
    try:
        # 解析输入的日期字符串为datetime对象（假设为本地时间）
        local_tz = pytz.timezone('Asia/Shanghai')
        
        # 尝试解析不同格式
        try:
            # 带时间的完整格式
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # 仅日期格式
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # 如果已经是ISO格式，直接返回
                if 'T' in date_str:
                    return date_str
                # 其他格式无法解析
                return date_str
        
        # 将解析的datetime转换为本地时区的datetime
        dt = local_tz.localize(dt)
        
        # 转换为UTC时间
        utc_dt = dt.astimezone(pytz.UTC)
        
        # 格式化为API需要的格式：YYYY-MM-DDThh:mm:ss.000+0000
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
    except Exception as e:
        print(f"日期格式转换错误: {str(e)}")
        return date_str
            
def _simplify_task_data(task_data: Dict[str, Any], projects_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """简化任务数据，保留重要字段并格式化日期"""
    # 格式化日期函数
    def format_date(date_str, is_due_date=False):
        if not date_str:
            return None
            
        dt = _parse_date(date_str)
        if not dt:
            return date_str
            
        # 如果是截止日期且时间是0点，考虑添加一天
        if is_due_date and dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            dt = dt + timedelta(days=1)
            
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 如果提供了项目数据列表，且当前任务只有projectId但没有projectName，则匹配项目名称
    if projects_data and task_data.get('projectId') and not task_data.get('projectName'):
        task_data = _merge_project_info_logic(task_data, projects_data)
    
    # 处理子任务
    children = []
    if task_data.get('items'):
        for item in task_data['items']:
            # 递归调用，同时传递项目数据
            child_task = _simplify_task_data(item, projects_data)
            children.append(child_task)
    # 创建基础任务数据
    simplified = {
        "id": task_data.get("id"),
        "title": task_data.get("title"),
        "content": task_data.get("content"),
        "priority": task_data.get("priority"),
        "status": task_data.get("status"),
        "completed": task_data.get("isCompleted", False),
        "projectId": task_data.get("projectId"),
        "projectName": task_data.get("projectName", "默认清单"),
        "projectKind": task_data.get("projectKind"),
        "columnId": task_data.get("columnId"),
        "tags": task_data.get("tags", []),
        "tagDetails": task_data.get("tagDetails", []),
        "startDate": format_date(task_data.get("startDate")),
        "dueDate": format_date(task_data.get("dueDate"), is_due_date=True),
        "completedTime": format_date(task_data.get("completedTime")),
        "createdTime": format_date(task_data.get("createdTime")),
        "modifiedTime": format_date(task_data.get("modifiedTime")),
        "isAllDay": task_data.get("isAllDay", False),
        "reminder": task_data.get("reminder"),
        "progress": task_data.get("progress", 0),
        "kind": task_data.get("kind"),
        "isCompleted": task_data.get("isCompleted", False),
        "items": children,
        "timeZone": "Asia/Shanghai",
        "reminders": task_data.get("reminders", []),
        "creator": task_data.get("creator"),
        "sortOrder": task_data.get("sortOrder", 0),
        "parentId": task_data.get("parentId"),
        "children": children
    }
    
    # 移除None值
    simplified = {k: v for k, v in simplified.items() if v is not None}
    return simplified

def _get_completed_tasks_info_logic() -> Dict[str, Any]:
    """(已废弃路径) 兼容占位：官方API不提供旧批量接口，返回空。"""
    return {}

def _update_column_info_logic(projects: List[Dict[str, Any]], completed_columns_set: set):
    """更新栏目信息，识别已完成状态的栏目 (逻辑部分)"""
    for project in projects:
        if 'columns' in project:
            for column in project.get('columns', []):
                # 检查栏目是否为已完成状态
                if column.get('type') == 'COMPLETED':
                    completed_columns_set.add(column.get('id'))

def _merge_project_info_logic(task_data: Dict[str, Any], projects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """将项目信息合并到任务数据中 (逻辑部分)"""
    if not task_data.get('projectId'):
        return task_data
    for project in projects:
        if project.get('id') == task_data['projectId']:
            task_data['projectName'] = project.get('name')
            task_data['projectKind'] = project.get('kind')
            break
    return task_data

def _merge_tag_info_logic(task_data: Dict[str, Any], tags: List[Dict[str, Any]]) -> Dict[str, Any]:
    """将标签详细信息合并到任务数据中 (逻辑部分)"""
    if not task_data.get('tags'):
        return task_data
    tag_details = []
    for tag_name in task_data['tags']:
        for tag in tags:
            if tag.get('name') == tag_name:
                tag_details.append({
                    'name': tag.get('name'),
                    'label': tag.get('label')
                })
                break
    task_data['tagDetails'] = tag_details
    return task_data

def _get_all_tasks_logic() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """获取所有任务，包括已完成和未完成的任务，并合并相关信息 (逻辑部分)"""
    global _completed_columns
    # 使用官方接口获取项目与任务
    projects_data = []
    try:
        projects_data = adapter.list_projects()
    except Exception:
        projects_data = []

    # 官方任务接口通常需要分别获取未完成/已完成，视文档具体筛选实现
    tasks_data: List[Dict[str, Any]] = []
    tags_data: List[Dict[str, Any]] = []  # 若官方没有标签API，则保留空集合
    try:
        # 遍历项目聚合任务（官方无全局列表端点）
        incomplete = adapter.list_tasks(completed=False)
        complete = adapter.list_tasks(completed=True)
        tasks_data = (incomplete or []) + (complete or [])
    except Exception as e:
        print(f"获取任务列表失败: {e}")
        tasks_data = []
    
    # 更新栏目信息 (使用全局变量)
    _update_column_info_logic(projects_data, _completed_columns)
    
    # 旧逻辑依赖批量端点合并“已完成”，现在已通过 adapter 分开获取，这里置空
    completed_tasks_info = {}
    
    # 处理所有任务（未完成+已完成）
    all_tasks = []
    
    # 处理未完成任务
    for task in tasks_data:
        # 只处理文本类型的任务
        if task.get('kind') != 'TEXT':
            continue
        
        # 合并项目和标签信息
        task = _merge_project_info_logic(task, projects_data)
        task = _merge_tag_info_logic(task, tags_data)
        
        # 检查是否在已完成任务列表中
        key = f"{task.get('creator')}_{task.get('title')}"
        # adapter.normalize_task_status 已处理 isCompleted/status，这里不再强制覆盖
        
        all_tasks.append(task)
    
    # 不再需要从已完成任务列表补充，adapter 已统一返回
    
    return all_tasks, projects_data, tags_data

# --- 模块级核心逻辑函数 ---

def get_tasks_logic(
    mode: Optional[str] = "all",
    keyword: Optional[str] = None,
    priority: Optional[int] = None,
    project_name: Optional[str] = None,
    completed: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    获取任务列表 (逻辑部分)
    
    Args:
        mode: 任务模式，支持 'all'(所有), 'today'(今天), 'yesterday'(昨天), 'recent_7_days'(最近7天)
        keyword: 关键词筛选
        priority: 优先级筛选 (0-最低, 1-低, 3-中, 5-高)
        project_name: 项目名称筛选
        completed: 是否已完成，True表示已完成，False表示未完成，None表示全部
        
    Returns:
        符合条件的任务列表
    """
    try:
        # 如果是查询今天的任务，默认只显示未完成的任务
        if mode == "today" and completed is None:
            completed = False
            
        # 获取所有任务
        all_tasks, projects_data, tags_data = _get_all_tasks_logic()
        
        # 确保所有任务都有正确的project_name (在过滤之前)
        for task in all_tasks:
            if task.get('projectId') and not task.get('projectName'):
                _merge_project_info_logic(task, projects_data)
        
        def is_today(task):
            # 检查任务是否为今天
            local_tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(local_tz)
            today = now.date()
            
            # 解析日期并获取日期部分
            start_date = _parse_date(task.get('startDate'))
            due_date = _parse_date(task.get('dueDate'))
            
            # 简化判断逻辑：使用截止日期或开始日期判断
            task_date = due_date or start_date
            
            # 判断日期是否为今天
            if task_date and task_date.date() == today:
                return True
                
            # 如果任务跨越今天(开始日期在今天之前，截止日期在今天之后或无截止日期)
            if start_date and start_date.date() < today:
                if not due_date or due_date.date() >= today:
                    return True
                    
            return False
            
        def is_yesterday(task):
            # 检查任务是否为昨天
            local_tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(local_tz)
            yesterday = (now - timedelta(days=1)).date()
            
            # 解析日期
            start_date = _parse_date(task.get('startDate'))
            due_date = _parse_date(task.get('dueDate'))
            
            # 简化判断逻辑：使用截止日期或开始日期判断
            task_date = due_date or start_date
            
            return task_date and task_date.date() == yesterday
            
        def is_recent_7_days(task):
            # 检查任务是否属于最近7天
            local_tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(local_tz)
            seven_days_ago = (now - timedelta(days=7))
            
            # 解析日期
            start_date = _parse_date(task.get('startDate'))
            due_date = _parse_date(task.get('dueDate'))
            
            # 简化判断逻辑：使用截止日期或开始日期判断
            task_date = due_date or start_date
            
            # 最近7天的任务
            if task_date and task_date >= seven_days_ago:
                return True
                
            # 跨越这7天的任务
            if start_date and start_date < seven_days_ago:
                if due_date and due_date >= seven_days_ago:
                    return True
                    
            return False
            
        # 过滤任务
        result = []
        for task in all_tasks:
            # 根据完成状态筛选
            if completed is not None:
                is_task_completed = task.get('isCompleted', False)
                if is_task_completed != completed:
                    continue
                
            # 根据模式筛选
            if mode == "today" and not is_today(task):
                continue
            elif mode == "yesterday" and not is_yesterday(task):
                continue
            elif mode == "recent_7_days" and not is_recent_7_days(task):
                continue
                
            # 根据其他条件筛选
            if keyword and keyword.lower() not in task.get('title', '').lower() and keyword.lower() not in task.get('content', '').lower():
                continue
                
            if priority is not None and task.get('priority') != priority:
                continue
            
                

            # 根据项目名称筛选 (现在任务已经有了正确的project_name)
            if project_name and project_name not in task.get('projectName', ''):
                continue
            # 保留简化后的任务数据，传递项目数据
            simplified_task = _simplify_task_data(task, projects_data)
            result.append(simplified_task)
        
        return result
    except Exception as e:
        print(f"获取任务列表时发生错误: {str(e)}")
        return []

def create_task_logic(
    title: Optional[str] = None,
    content: Optional[str] = None,
    priority: Optional[int] = None,
    project_name: Optional[str] = None,
    tag_names: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    is_all_day: Optional[bool] = None,
    reminder: Optional[str] = None,
    kind: Optional[str] = None,
    # 官方字段（新增）
    project_id: Optional[str] = None,
    desc: Optional[str] = None,
    time_zone: Optional[str] = None,
    reminders: Optional[List[str]] = None,
    repeat_flag: Optional[str] = None,
    sort_order: Optional[int] = None,
    items: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    创建新任务 (逻辑部分)
    
    Args:
        title: 任务标题
        content: 任务内容
        priority: 优先级 (0-最低, 1-低, 3-中, 5-高)
        project_name: 项目名称
        tag_names: 标签名称列表
        start_date: 开始日期，格式 'YYYY-MM-DD HH:MM:SS'
        due_date: 截止日期，格式 'YYYY-MM-DD HH:MM:SS'
        is_all_day: 是否为全天任务
        reminder: 提醒选项，如 "0"(准时), "-5M"(提前5分钟), "-1H"(提前1小时), "-1D"(提前1天)
        
    Returns:
        创建的任务信息
    """
    resolved_project_id = project_id
    projects_data = adapter.list_projects()
    
    if not resolved_project_id and project_name:
        # 尝试精确匹配
        for project in projects_data:
            if project.get('name') == project_name:
                resolved_project_id = project.get('id')
                break
                
        # 如果精确匹配失败，尝试不区分大小写的匹配
        if not resolved_project_id and project_name:
            project_name_lower = project_name.lower()
            for project in projects_data:
                if project.get('name', '').lower() == project_name_lower:
                    print("不区分大小写匹配到项目：", project.get('name'))
                    resolved_project_id = project.get('id')
                    break
        
        # 如果仍然失败，尝试部分匹配
        if not resolved_project_id and project_name:
            for project in projects_data:
                if project_name.lower() in project.get('name', '').lower() or project.get('name', '').lower() in project_name.lower():
                    print("部分匹配到项目：", project.get('name'))
                    resolved_project_id = project.get('id')
                    break
    
    # 准备任务数据
    task_data = {
        "title": title,
        "content": content,
        "priority": priority,
        "projectId": resolved_project_id,
        # 官方任务未公开 tags 字段，保留为兼容逻辑但不强制发送
        # "tags": tag_names or [],
        "isAllDay": is_all_day,
        "reminder": reminder,
        "status": 0,
        "kind": kind,
        # 官方字段
        "desc": desc,
        "timeZone": time_zone,
        "reminders": reminders,
        "repeatFlag": repeat_flag,
        "sortOrder": sort_order,
        "items": items,
    }
    
    # 处理日期和提醒
    if start_date:
        # 转换为API所需的格式
        task_data["startDate"] = _format_date_for_api(start_date)
        
    if due_date:
        # 转换为API所需的格式
        task_data["dueDate"] = _format_date_for_api(due_date)
        
    if reminder:
        task_data["reminder"] = reminder
        
    # 移除None值的字段
    task_data = {k: v for k, v in task_data.items() if v is not None}
    print(task_data)
    
    # 发送创建请求
    response = adapter.create_task(task_data)
    
    # 返回简化后的响应，同时传递项目数据
    return _simplify_task_data(response, projects_data)

def update_task_logic(
    task_id_or_title: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    priority: Optional[int] = None,
    project_name: Optional[str] = None,
    tag_names: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    is_all_day: Optional[bool] = None,
    reminder: Optional[str] = None,
    status: Optional[int] = None,
    # 官方字段（新增）
    project_id: Optional[str] = None,
    desc: Optional[str] = None,
    time_zone: Optional[str] = None,
    reminders: Optional[List[str]] = None,
    repeat_flag: Optional[str] = None,
    sort_order: Optional[int] = None,
    items: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    更新任务 (逻辑部分)
    
    Args:
        task_id_or_title: 任务ID或任务标题
        title: 新任务标题
        content: 新任务内容
        priority: 新优先级 (0-最低, 1-低, 3-中, 5-高)
        project_name: 新项目名称
        tag_names: 新标签名称列表
        start_date: 新开始日期，格式 'YYYY-MM-DD HH:MM:SS'
        due_date: 新截止日期，格式 'YYYY-MM-DD HH:MM:SS'
        is_all_day: 是否为全天任务
        reminder: 新提醒选项
        status: 新状态，0表示未完成，2表示已完成
        
    Returns:
        更新后的任务信息字典 (包含 success, info, data)
    """
    try:
        # 获取所有任务
        all_tasks, projects_data, _ = _get_all_tasks_logic()
        
        # 查找任务
        task = None
        # 先尝试按ID查找
        for t in all_tasks:
            if t.get('id') == task_id_or_title:
                task = t
                break
        
        # 如果没找到，按标题查找
        if not task:
            for t in all_tasks:
                if t.get('title') == task_id_or_title:
                    task = t
                    break
        
        if not task:
            return {
                "success": False,
                "info": f"未找到ID或标题为 '{task_id_or_title}' 的任务",
                "data": None
            }
        
        task_id = task.get('id')
        
        # 查找项目ID（如果指定了项目名称）
        project_id = project_id or task.get('projectId')
        if project_name and not project_id:
            for project in projects_data:
                if project.get('name') == project_name:
                    project_id = project.get('id')
                    break
                    
        # 准备更新数据
        update_data = {
            "id": task_id,
            "title": title if title is not None else task.get('title'),
            "content": content if content is not None else task.get('content'),
            "priority": priority if priority is not None else task.get('priority'),
            "projectId": project_id,
            # 官方未公开 tags 写入，去除发送
            "isAllDay": is_all_day if is_all_day is not None else task.get('isAllDay'),
            "status": status if status is not None else task.get('status'),
            # 官方字段
            "desc": desc if desc is not None else task.get('desc'),
            "timeZone": time_zone if time_zone is not None else task.get('timeZone'),
            "reminders": reminders if reminders is not None else task.get('reminders'),
            "repeatFlag": repeat_flag if repeat_flag is not None else task.get('repeatFlag'),
            "sortOrder": sort_order if sort_order is not None else task.get('sortOrder'),
            "items": items if items is not None else task.get('items'),
        }
        
        # 处理日期和提醒
        if start_date is not None:
            # 转换为API所需的格式
            update_data["startDate"] = _format_date_for_api(start_date)
        elif 'startDate' in task:
            update_data["startDate"] = task['startDate']
            
        if due_date is not None:
            # 转换为API所需的格式
            update_data["dueDate"] = _format_date_for_api(due_date)
        elif 'dueDate' in task:
            update_data["dueDate"] = task['dueDate']
            
        if reminder is not None:
            update_data["reminder"] = reminder
        elif 'reminder' in task:
            update_data["reminder"] = task['reminder']
            
        # 移除None值的字段
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # 状态变更：对齐官方逻辑（仅支持完成）
        if status is not None:
            if status == 2:
                if not project_id:
                    return {
                        "success": False,
                        "info": "完成任务失败：缺少 projectId",
                        "data": None
                    }
                try:
                    adapter.complete_task(project_id, task_id)
                    # 完成后刷新一次该项目任务，返回最新数据
                    refreshed = adapter.list_tasks(project_id=project_id)
                    fresh = next((t for t in refreshed if t.get('id') == task_id), None)
                    if fresh:
                        return {
                            "success": True,
                            "info": "任务已完成",
                            "data": _simplify_task_data(fresh, projects_data)
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "info": f"完成任务失败: {e}",
                        "data": None
                    }
                # 若无法刷新，基于原任务构造完成态返回
                task_after = dict(task)
                task_after['status'] = 2
                task_after['isCompleted'] = True
                return {
                    "success": True,
                    "info": "任务已完成",
                    "data": _simplify_task_data(task_after, projects_data)
                }
            elif status == 0:
                return {
                    "success": False,
                    "info": "取消完成未在官方开放API中提供，暂不支持",
                    "data": None
                }

        # 非状态变更：走常规更新
        print(f"更新数据: {update_data}")
        response = adapter.update_task(task_id, update_data)
        
        # 返回更新结果
        return {
            "success": True,
            "info": "任务更新成功",
            "data": _simplify_task_data(response, projects_data)
        }
    except Exception as e:
        print(f"更新任务失败: {str(e)}")
        return {
            "success": False,
            "info": f"更新任务失败: {str(e)}",
            "data": None
        }

def delete_task_logic(task_id_or_title: str) -> Dict[str, Any]:
    """
    删除任务 (逻辑部分)
    
    Args:
        task_id_or_title: 任务ID或任务标题
        
    Returns:
        删除操作的响应字典 (包含 success, info, data)
    """
    try:
        # 获取所有任务
        all_tasks, projects_data, _ = _get_all_tasks_logic()
        
        task = None
        # 先尝试按ID查找
        for t in all_tasks:
            if t.get('id') == task_id_or_title:
                task = t
                break
                
        # 如果没找到，按标题查找
        if not task:
            for t in all_tasks:
                if t.get('title') == task_id_or_title:
                    task = t
                    break
        
        if not task:
            return {
                "success": False,
                "info": f"未找到ID或标题为 '{task_id_or_title}' 的任务",
                "data": None
            }
        
        task_id = task.get('id')
        project_id = task.get('projectId')
        
        # 发送删除请求
        # 官方删除需要 projectId
        adapter.delete_task(project_id, task_id)
        
        # 返回删除结果
        return {
            "success": True,
            "info": f"成功删除任务 '{task.get('title')}'",
            "data": _simplify_task_data(task, projects_data)
        }
        
    except Exception as e:
        print(f"删除任务失败: {str(e)}")
        return {
            "success": False,
            "info": f"删除任务失败: {str(e)}",
            "data": None
        }


def complete_task_logic(task_id_or_title: str) -> Dict[str, Any]:
    """
    完成任务（调用官方 complete 接口）
    
    Args:
        task_id_or_title: 任务ID或任务标题
    Returns:
        操作结果字典
    """
    try:
        all_tasks, projects_data, _ = _get_all_tasks_logic()
        task = None
        for t in all_tasks:
            if t.get('id') == task_id_or_title or t.get('title') == task_id_or_title:
                task = t
                break
        if not task:
            return {
                "success": False,
                "info": f"未找到ID或标题为 '{task_id_or_title}' 的任务",
                "data": None
            }
        task_id = task.get('id')
        project_id = task.get('projectId')
        if not project_id:
            return {
                "success": False,
                "info": "完成任务失败：缺少 projectId",
                "data": None
            }
        adapter.complete_task(project_id, task_id)
        # 刷新该项目任务，返回最新数据
        refreshed = adapter.list_tasks(project_id=project_id)
        fresh = next((t for t in refreshed if t.get('id') == task_id), None)
        if fresh:
            return {
                "success": True,
                "info": "任务已完成",
                "data": _simplify_task_data(fresh, projects_data)
            }
        # 无法刷新则回退构造
        task_after = dict(task)
        task_after['status'] = 2
        task_after['isCompleted'] = True
        return {
            "success": True,
            "info": "任务已完成",
            "data": _simplify_task_data(task_after, projects_data)
        }
    except Exception as e:
        return {
            "success": False,
            "info": f"完成任务失败: {e}",
            "data": None
        }


# --- MCP工具注册 ---

def register_task_tools(server: FastMCP, auth_info: Dict[str, Any]):
    """
    注册任务相关工具到MCP服务器
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息字典，包含token或email/password
    """
    # 适配层按需初始化，无需在此显式初始化
    
    @server.tool()
    def get_tasks(
        mode: Optional[str] = "all",
        keyword: Optional[str] = None,
        priority: Optional[int] = None,
        project_name: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        获取任务列表
        (调用模块级逻辑函数)
        
        Args:
            mode: 任务模式，支持 'all'(所有), 'today'(今天), 'yesterday'(昨天), 'recent_7_days'(最近7天)
            keyword: 关键词筛选
            priority: 优先级筛选 (0-最低, 1-低, 3-中, 5-高)
            project_name: 项目名称筛选
            completed: 是否已完成，True表示已完成，False表示未完成，None表示全部
            
        Returns:
            符合条件的任务列表
        """
        return get_tasks_logic(mode=mode, keyword=keyword, priority=priority, project_name=project_name, completed=completed)
    
    @server.tool()
    def create_task(
        title: Optional[str] = None,
        content: Optional[str] = None,
        priority: Optional[int] = None,
        project_name: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        is_all_day: Optional[bool] = None,
        reminder: Optional[str] = None,
        # 官方字段（新增）
        project_id: Optional[str] = None,
        desc: Optional[str] = None,
        time_zone: Optional[str] = None,
        reminders: Optional[List[str]] = None,
        repeat_flag: Optional[str] = None,
        sort_order: Optional[int] = None,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        创建新任务
        (调用模块级逻辑函数)
        
        Args:
            title: 任务标题
            content: 任务内容
            priority: 优先级 (0-最低, 1-低, 3-中, 5-高)
            project_name: 项目名称
            tag_names: 标签名称列表
            start_date: 开始日期，格式 'YYYY-MM-DD HH:MM:SS'，会自动转换为API所需的时区和格式
            due_date: 截止日期，格式 'YYYY-MM-DD HH:MM:SS'，会自动转换为API所需的时区和格式
            is_all_day: 是否为全天任务
            reminder: 提醒选项，如 "0"(准时), "-5M"(提前5分钟), "-1H"(提前1小时), "-1D"(提前1天)
            
        Returns:
            创建的任务信息
        """
        return create_task_logic(title=title, content=content, priority=priority, project_name=project_name, tag_names=tag_names, start_date=start_date, due_date=due_date, is_all_day=is_all_day, reminder=reminder, project_id=project_id, desc=desc, time_zone=time_zone, reminders=reminders, repeat_flag=repeat_flag, sort_order=sort_order, items=items)
    
    @server.tool()
    def update_task(
        task_id_or_title: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        priority: Optional[int] = None,
        project_name: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        is_all_day: Optional[bool] = None,
        reminder: Optional[str] = None,
        status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        更新任务
        (调用模块级逻辑函数)
        
        Args:
            task_id_or_title: 任务ID或任务标题
            title: 新任务标题
            content: 新任务内容
            priority: 新优先级 (0-最低, 1-低, 3-中, 5-高)
            project_name: 新项目名称
            tag_names: 新标签名称列表
            start_date: 新开始日期，格式 'YYYY-MM-DD HH:MM:SS'，会自动转换为API所需的时区和格式
            due_date: 新截止日期，格式 'YYYY-MM-DD HH:MM:SS'，会自动转换为API所需的时区和格式
            is_all_day: 是否为全天任务
            reminder: 新提醒选项
            status: 新状态，0表示未完成，2表示已完成
            
        Returns:
            更新后的任务信息
        """
        return update_task_logic(task_id_or_title=task_id_or_title, title=title, content=content, priority=priority, project_name=project_name, tag_names=tag_names, start_date=start_date, due_date=due_date, is_all_day=is_all_day, reminder=reminder, status=status)
    
    @server.tool()
    def delete_task(task_id_or_title: str) -> Dict[str, Any]:
        """
        删除任务
        (调用模块级逻辑函数)
        
        Args:
            task_id_or_title: 任务ID或任务标题
            
        Returns:
            删除操作的响应
        """
        return delete_task_logic(task_id_or_title=task_id_or_title)

    @server.tool()
    def complete_task(task_id_or_title: str) -> Dict[str, Any]:
        """
        完成任务（官方：POST /open/v1/project/{projectId}/task/{taskId}/complete）
        Args:
            task_id_or_title: 任务ID或任务标题
        Returns:
            操作结果
        """
        return complete_task_logic(task_id_or_title)

# 导出可供外部引用的函数
__all__ = [
    'get_tasks_logic', 
    'create_task_logic', 
    'update_task_logic', 
    'delete_task_logic', 
    'complete_task_logic',
    'register_task_tools',
    '_get_all_tasks_logic' # 如果需要外部访问
] 