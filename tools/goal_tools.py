"""
目标管理工具 (基于滴答清单项目和任务)
"""

import re
import json
from typing import List, Dict, Optional, Any, Union, Tuple
from fastmcp import FastMCP

# 导入其他工具的逻辑函数
from .project_tools import (
    get_projects_logic,
    create_project_logic,
    update_project_logic,
    delete_project_logic
)
from .task_tools import (
    get_tasks_logic, 
    create_task_logic,
    update_task_logic,
    delete_task_logic
)
# 目标更新走 update_task_logic，无需直接HTTP调用

# 导入辅助函数
from utils.date.date_utils import is_valid_date, format_datetime, get_current_time
from utils.text.text_analysis import normalize_keywords, match_keywords, calculate_similarity

# --- 常量 --- 
GOAL_PROJECT_NAME = "🎯 目标管理"  # 存放所有目标的项目名称
GOAL_TASK_PREFIX = ""  # 目标任务的前缀
METADATA_PATTERN = re.compile(r"\[(.*?): (.*?)\]")
GOAL_TYPES = ['phase', 'permanent', 'habit'] # 目标类型保持，用于描述元数据
GOAL_STATUSES = ['active', 'completed', 'abandoned'] # 目标状态

# --- 辅助函数 ---

def _format_metadata(data: Dict[str, Any]) -> str:
    """将元数据字典格式化为任务描述字符串"""
    parts = []
    for key, value in data.items():
        if value: # 只包含有值的字段
            parts.append(f"[{key.capitalize()}: {value}]")
    return " ".join(parts)

def _parse_metadata(description: Optional[str]) -> Dict[str, Any]:
    """从任务描述字符串中解析元数据"""
    metadata = {}
    if description:
        matches = METADATA_PATTERN.findall(description)
        for key, value in matches:
            metadata[key.lower()] = value.strip()
    return metadata

def _get_goal_project() -> Optional[str]:
    """
    获取目标管理项目的ID
    先精确匹配项目名称，如果找不到，再尝试模糊匹配
    如果不存在则返回 None
    """
    projects = get_projects_logic()
    
    # 1. 精确匹配项目名称
    for project in projects:
        if project.get('name') == GOAL_PROJECT_NAME:
            return project
    
    # 2. 模糊匹配 - 查找名称中包含"目标"和"🎯"的项目
    for project in projects:
        project_name = project.get('name', '')
        if '目标' in project_name and '🎯' in project_name:
            print(f"找到类似的目标管理项目: {project_name}")
            return project
    
    # 3. 更宽松的匹配 - 只要包含"目标"
    for project in projects:
        project_name = project.get('name', '')
        if '目标' in project_name:
            print(f"找到相关的目标项目: {project_name}")
            return project
    
    return None 

def _ensure_goal_project_exists() -> str:
    """
    确保存在目标管理项目
    如果不存在则创建，返回项目ID
    """
    project = _get_goal_project()
    if project:
        return project
    
    print(f"未找到目标管理项目，创建新项目: {GOAL_PROJECT_NAME}")
    # 创建目标管理项目
    project_data = create_project_logic(name=GOAL_PROJECT_NAME)
    project = project_data.get('id')
    if not project:
        raise ValueError(f"创建目标管理项目失败，未返回项目ID。API响应: {project_data}")
    
    return project

def _enrich_goal_data(task: Dict[str, Any]) -> Dict[str, Any]:
    """将任务数据丰富为目标数据"""
    task_id = task.get('id')
    metadata = _parse_metadata(task.get('content'))
    
    goal_data = {
        "id": task_id,
        "title": task.get('title', ''),  # 直接使用任务标题，不需要移除前缀
        "description": task.get('content', ''), # 保留原始描述
        "type": metadata.get('type', 'permanent'), # 默认类型
        "status": 'completed' if task.get('status') == 2 or task.get('isCompleted') else 'active',
        "keywords": metadata.get('keywords', ''),
        "start_date": metadata.get('start_date'),
        "due_date": task.get('dueDate'),  # 使用任务本身的截止日期
        "frequency": metadata.get('frequency'),
        "created_time": task.get('createdTime'), # 使用任务创建时间
        "modified_time": task.get('modifiedTime'),
        "priority": task.get('priority', 0),  # 任务优先级
        "project_id": task.get('projectId'),  # 所属项目ID
        "raw_task_data": task # 保留原始任务数据
    }
    return {k: v for k, v in goal_data.items() if v is not None}

# --- 模块级核心逻辑函数 ---

def create_goal_logic(
    title: str,
    type: str,
    keywords: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    start_date: Optional[str] = None,
    frequency: Optional[str] = None,
    related_projects: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    创建新目标 (作为任务存放在目标管理项目中)
    
    Args:
        title: 目标标题
        type: 目标类型(phase/permanent/habit)
        keywords: 关键词，以逗号分隔
        description: 目标描述 (会附加元数据)
        due_date: 截止日期 (YYYY-MM-DD)
        start_date: 开始日期 (YYYY-MM-DD)
        frequency: 频率 (用于习惯目标)
        related_projects: 相关项目IDs (保留参数，当前版本不使用)
        
    Returns:
        创建的目标信息 (丰富后的数据)
    """
    # 验证类型
    if type not in GOAL_TYPES:
        raise ValueError(f"无效的目标类型: {type}，应为 {GOAL_TYPES} 之一")

    # 验证日期格式
    if due_date and not is_valid_date(due_date):
        raise ValueError(f"无效的截止日期格式: {due_date}，应为YYYY-MM-DD")
    if start_date and not is_valid_date(start_date):
        raise ValueError(f"无效的开始日期格式: {start_date}，应为YYYY-MM-DD")
        
    # 验证特定类型的字段
    if type == 'phase' and not due_date:
        raise ValueError("阶段性目标必须指定截止日期(due_date)")
    if type == 'habit' and not frequency:
        raise ValueError("习惯性目标必须指定频率(frequency)")
    
    try:
        # 1. 确保目标管理项目存在
        project_id = _ensure_goal_project_exists()
        
        # 2. 准备任务标题 - 直接使用传入的标题，不添加前缀
        task_title = title
        
        # 3. 准备元数据
        metadata = {
            'type': type,
            'keywords': normalize_keywords(keywords),
            'start_date': start_date,
            'frequency': frequency
            # due_date 将直接用于任务的dueDate字段
        }
        metadata_str = _format_metadata(metadata)
        
        # 4. 组合任务内容
        full_content = f"{description}\n\n--- Metadata ---\n{metadata_str}" if description else f"--- Metadata ---\n{metadata_str}"
        
        # 5. 创建任务 - 使用正确的参数名称
        # 注意：task_tools.create_task_logic 期望 project_name 而不是 projectId
        created_task = create_task_logic(
            title=task_title,
            content=full_content,
            project_name=GOAL_PROJECT_NAME,  # 使用项目名称而不是ID
            due_date=due_date,
            start_date=start_date,
            priority=3  # 默认设置为中等优先级
        )
        
        # 6. 返回丰富的目标数据
        return _enrich_goal_data(created_task)
    
    except Exception as e:
        raise ValueError(f"创建目标失败: {e}")

def get_goals_logic(
    type: Optional[str] = None,
    status: Optional[str] = None,
    keywords: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取目标列表 (基于任务)
    
    Args:
        type: 目标类型筛选
        status: 目标状态筛选 (active/completed)
        keywords: 关键词筛选 (匹配目标标题或元数据中的关键词)
        
    Returns:
        目标列表
    """
    project = _get_goal_project()
    if not project:
        print("未找到目标管理项目，返回空列表")
        return []  # 如果目标管理项目不存在，直接返回空列表
    # 2. 确定完成状态参数
    completed = None
    if status == 'completed':
        completed = True
    elif status == 'active':
        completed = False
    
    try:
        # 3. 获取项目下的所有任务 
        # 使用项目名称，而不是ID，以匹配task_tools的API设计
        all_tasks = get_tasks_logic(
            mode='all', 
            completed=completed,
            project_name=project.get('name')
        )

        # 如果返回的是None或空值，返回空列表
        if not all_tasks:
            print("项目下未找到任务，返回空列表")
            return []
            
        # 4. 过滤得到目标任务
        goal_list = []
        
        # 处理关键词
        search_keywords = keywords or ""
        if not isinstance(search_keywords, str):
            search_keywords = ""
            
        search_keywords_set = set(normalize_keywords(search_keywords).split(',')) if search_keywords else set()
        
        for task in all_tasks:
            # 由于GOAL_TASK_PREFIX为空，不用startswith判断，而是看任务是否属于目标项目
            if task and isinstance(task, dict):
                try:
                    goal_data = _enrich_goal_data(task)
                    
                    # 类型筛选
                    if type and goal_data.get('type') != type:
                        continue
                    
                    # 关键词筛选
                    if search_keywords_set:
                        goal_title_lower = goal_data.get('title', '').lower()
                        goal_meta_keywords = set(k for k in goal_data.get('keywords', '').split(',') if k)
                        # 检查标题或元数据关键词是否包含任何搜索关键词
                        if not any(sk in goal_title_lower for sk in search_keywords_set) and \
                           not search_keywords_set.intersection(goal_meta_keywords):
                            continue
                    
                    goal_list.append(goal_data)
                except Exception as e:
                    print(f"处理任务时出错，跳过: {e}")
                    continue
        
        return goal_list
        
    except Exception as e:
        print(f"获取目标列表时出错: {e}")
        return []  # 出错时返回空列表而不是抛出异常

def get_goal_logic(goal_id: str) -> Optional[Dict[str, Any]]:
    """
    获取目标详情 (基于任务ID)
    
    Args:
        goal_id: 目标ID (即任务ID)
        
    Returns:
        目标详情，如果不是目标任务或未找到则返回None
    """
    # 尝试直接获取任务详情
    try:
        # 获取目标项目
        goal_project = _get_goal_project()
        if not goal_project:
            return None
            
        project_id = goal_project.get('id')
        
        # 获取所有任务
        tasks = get_tasks_logic(mode="all")
        task = None
        for t in tasks:
            if t.get('id') == goal_id:
                task = t
                break
                
        if not task:
            return None
        
        # 验证是否属于目标项目
        if task.get('projectId') != project_id:
            return None
        
        return _enrich_goal_data(task)
    except Exception as e:
        print(f"获取目标详情时出错: {e}")
        return None

def update_goal_logic(
    goal_id: str,
    title: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    keywords: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    start_date: Optional[str] = None,
    frequency: Optional[str] = None,
    progress: Optional[int] = None,
    related_projects: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    更新目标 (基于任务)
    
    Args:
        goal_id: 目标ID (任务ID)
        title: 新标题 (不含前缀)
        type: 新类型
        status: 新状态 (active/completed)
        keywords: 新关键词 (逗号分隔)
        description: 新的基础描述 (元数据会自动附加)
        due_date: 新截止日期
        start_date: 新开始日期
        frequency: 新频率
        progress: 进度 (忽略)
        related_projects: 相关项目 (忽略)
        
    Returns:
        更新后的目标数据
    """
    try:
        # 1. 获取当前目标任务
        current_goal = get_goal_logic(goal_id)
        if not current_goal:
            raise ValueError(f"未找到目标任务: {goal_id}")
        
        # 2. 处理任务状态
        task_status = None
        if status is not None:
            if status == 'completed':
                task_status = 2  # 已完成
            elif status == 'active':
                task_status = 0  # 未开始/进行中
        
        # 3. 处理元数据更新
        new_content = None
        if any(param is not None for param in [type, keywords, frequency, description]):
            # 获取当前任务数据和元数据
            raw_task_data = current_goal.get("raw_task_data", {})
            current_content = raw_task_data.get('content', '')
            current_metadata = _parse_metadata(current_content)
            
            # 分割描述和元数据部分
            content_parts = current_content.split("\n\n--- Metadata ---\n")
            current_desc = content_parts[0] if len(content_parts) > 1 else ""
            
            # 更新元数据
            if type is not None:
                if type not in GOAL_TYPES:
                    raise ValueError(f"无效类型: {type}")
                current_metadata['type'] = type
                
            if keywords is not None:
                current_metadata['keywords'] = normalize_keywords(keywords)
                
            if start_date is not None and is_valid_date(start_date):
                current_metadata['start_date'] = start_date
                
            if frequency is not None:
                current_metadata['frequency'] = frequency
            
            # 更新描述
            new_desc = description if description is not None else current_desc
            
            # 构建新内容
            metadata_str = _format_metadata(current_metadata)
            new_content = f"{new_desc}\n\n--- Metadata ---\n{metadata_str}" if new_desc else f"--- Metadata ---\n{metadata_str}"
        
        # 4. 直接调用update_task_logic更新任务
        result = update_task_logic(
            task_id_or_title=goal_id,
            title=title,
            content=new_content,
            status=task_status,
            due_date=due_date,
            start_date=start_date
        )
        
        # 5. 检查结果并返回
        if not result.get('success'):
            raise ValueError(result.get('info', '更新失败，无详细错误信息'))
        
        updated_task = result.get('data')
        return _enrich_goal_data(updated_task)
        
    except Exception as e:
        raise ValueError(f"更新目标 {goal_id} 失败: {e}")

def delete_goal_logic(goal_id: str) -> Dict[str, Any]:
    """
    删除目标 (基于任务)
    
    Args:
        goal_id: 目标ID (任务ID)
        
    Returns:
        删除操作结果
    """
    # 先确认是目标任务
    goal_data = get_goal_logic(goal_id)
    if not goal_data:
        raise ValueError(f"未找到目标任务: {goal_id}，无法删除")
    
    # 调用任务删除逻辑 - task_id_or_title而不是task_id
    return delete_task_logic(task_id_or_title=goal_id)

def match_task_with_goals_logic(
    task_title: str,
    task_content: Optional[str] = None,
    project_id: Optional[str] = None,
    min_score: float = 0.3
) -> List[Dict[str, Any]]:
    """
    匹配任务与目标 (基于内容相似度和关键词)
    
    Args:
        task_title: 任务标题
        task_content: 任务内容
        project_id: 任务所属项目ID (不再用于直接匹配，因为所有目标都在目标管理项目下)
        min_score: 最小匹配分数
        
    Returns:
        匹配的目标列表，按匹配度降序排序
    """
    active_goals = get_goals_logic(status='active')
    task_text = f"{task_title} {task_content or ''}".lower()
    
    matches = []
    for goal in active_goals:
        match_score = 0.0
        
        # 1. 关键词和文本相似度匹配
        goal_keywords_str = goal.get('keywords', '')
        goal_keywords_set = set(k for k in goal_keywords_str.split(',') if k)
        goal_title = goal.get('title', '')
        goal_desc = goal.get('description', '').split("\n\n--- Metadata ---\n")[0] # 只用基础描述
        goal_text_match = f"{goal_title} {goal_desc}".lower()
        
        keyword_score = 0.0
        similarity_score = 0.0
        
        if goal_keywords_set:
            # 简单的关键词包含匹配
            if any(kw.lower() in task_text for kw in goal_keywords_set):
                keyword_score = 0.7 # 基础分
        
        if goal_text_match:
            similarity_score = calculate_similarity(task_text, goal_text_match) * 0.3 # 相似度占比较低
        
        match_score = keyword_score + similarity_score
   
        # 添加到结果如果分数达标
        if match_score >= min_score:
            matches.append({
                'goal': goal,
                'score': round(match_score, 3)
            })
       
    # 按分数排序
    matches.sort(key=lambda x: x['score'], reverse=True)
    return [match['goal'] for match in matches]

# --- MCP工具注册 ---

def register_goal_tools(server: FastMCP, auth_info: Dict[str, Any]):
    """
    注册目标管理工具到MCP服务器 (基于任务)
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息 (用于初始化API，如果需要)
    """
    
    @server.tool()
    def create_goal(
        title: str,
        type: str,
        keywords: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        start_date: Optional[str] = None,
        frequency: Optional[str] = None,
        related_projects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建新目标 (作为任务存放在目标管理项目中)
        
        Args:
            title: 目标标题
            type: 目标类型 (phase/permanent/habit)
            keywords: 关键词，以逗号分隔
            description: 目标的基础描述 (可选)
            due_date: 截止日期 (YYYY-MM-DD) (阶段性目标必填)
            start_date: 开始日期 (YYYY-MM-DD) (可选)
            frequency: 频率 (daily, weekly:1,3,5 等) (习惯目标必填)
            related_projects: 相关项目IDs (可选)
            
        Returns:
            创建的目标信息
        """
        # 直接调用逻辑函数，逻辑函数应能处理Optional参数
        try:
            return create_goal_logic(title, type, keywords, description, due_date, start_date, frequency)
        except (ValueError, NotImplementedError) as e:
            raise e
        except Exception as e:
            print(f"调用 create_goal 时发生意外错误: {e}")
            raise ValueError(f"创建目标时发生内部错误: {e}")

    @server.tool()
    def get_goals(
        type: Optional[str] = None,
        status: Optional[str] = None,
        keywords: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取目标列表
        
        Args:
            type: 目标类型筛选 (phase/permanent/habit)
            status: 目标状态筛选 (active/completed)
            keywords: 关键词筛选 (匹配目标标题或关键词) - 字符串形式
            
        Returns:
            目标列表
        """
        # 直接调用逻辑函数
        try:
            return get_goals_logic(type=type, status=status, keywords=keywords)
        except Exception as e:
            print(f"调用 get_goals 时发生意外错误: {e}")
            raise ValueError(f"获取目标列表时发生内部错误: {e}")

    @server.tool()
    def get_goal(goal_id: str) -> Dict[str, Any]:
        """
        获取目标详情
        
        Args:
            goal_id: 目标ID (任务ID)
            
        Returns:
            目标详情
        """
        try:
            goal = get_goal_logic(goal_id)
            if not goal:
                raise ValueError(f"未找到ID为 '{goal_id}' 的目标")
            return goal
        except Exception as e:
            print(f"调用 get_goal 时发生意外错误: {e}")
            raise ValueError(f"获取目标 '{goal_id}' 时发生内部错误: {e}")

    @server.tool()
    def update_goal(
        goal_id: str,
        title: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        keywords: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        start_date: Optional[str] = None,
        frequency: Optional[str] = None,
        progress: Optional[int] = None,
        related_projects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        更新目标
        
        Args:
            goal_id: 目标ID (任务ID)
            title: 新标题 (可选)
            type: 新类型 (phase/permanent/habit) (可选)
            status: 新状态 (active/completed) (可选)
            keywords: 新关键词 (逗号分隔) (可选)
            description: 新的基础描述 (可选)
            due_date: 新截止日期 (YYYY-MM-DD) (可选)
            start_date: 新开始日期 (YYYY-MM-DD) (可选)
            frequency: 新频率 (可选)
            progress: 进度 (忽略)
            related_projects: 相关项目 (忽略)
            
        Returns:
            更新后的目标数据
        """
        # 直接调用逻辑函数
        try:
            return update_goal_logic(goal_id, title, type, status, keywords, description, due_date, start_date, frequency)
        except (ValueError, NotImplementedError) as e:
            raise e
        except Exception as e:
            print(f"调用 update_goal 时发生意外错误: {e}")
            raise ValueError(f"更新目标 '{goal_id}' 时发生内部错误: {e}")

    @server.tool()
    def delete_goal(goal_id: str) -> Dict[str, Any]:
        """
        删除目标
        
        Args:
            goal_id: 目标ID (任务ID)
            
        Returns:
            删除操作的结果
        """
        try:
            return delete_goal_logic(goal_id)
        except (ValueError, NotImplementedError) as e:
            raise e
        except Exception as e:
            print(f"调用 delete_goal 时发生意外错误: {e}")
            raise ValueError(f"删除目标 '{goal_id}' 时发生内部错误: {e}")

    @server.tool()
    def match_task_with_goals(
        task_title: str,
        task_content: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        匹配任务与目标
        
        Args:
            task_title: 任务标题
            task_content: 任务内容 (可选)
            project_id: 任务所属项目ID (可选)
            
        Returns:
            匹配的目标列表 (按匹配度排序)
        """
        # 直接调用逻辑函数
        try:
            return match_task_with_goals_logic(task_title, task_content, project_id)
        except Exception as e:
            print(f"调用 match_task_with_goals 时发生意外错误: {e}")
            raise ValueError(f"匹配任务与目标时发生内部错误: {e}")

# 导出
__all__ = [
    'create_goal_logic',
    'get_goals_logic',
    'get_goal_logic',
    'update_goal_logic',
    'delete_goal_logic',
    'match_task_with_goals_logic',
    'register_goal_tools'
]
