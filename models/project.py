"""
项目数据模型
"""
from typing import Optional, List, Dict, Any
from .base import BaseModel
from .task import Task

class Project(BaseModel):
    """项目数据模型"""
    
    def __init__(
        self,
        name: str,
        color: str = "#FFD324",
        group_id: Optional[str] = None,
        tasks: Optional[List[Task]] = None,
        in_all: bool = True,
        kind: str = "TASK",
        view_mode: str = "list",
        **kwargs
    ):
        """
        初始化项目实例
        
        Args:
            name: 项目名称
            color: 项目颜色
            group_id: 所属分组ID
            tasks: 项目下的任务列表
            in_all: 是否显示在所有项目中
            kind: 项目类型
            view_mode: 视图模式
            **kwargs: 其他属性
        """
        self.name = name
        self.color = color
        self.group_id = group_id
        self.tasks = tasks or []
        self.in_all = in_all
        self.kind = kind
        self.view_mode = view_mode
        super().__init__(**kwargs)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        从API响应数据创建项目实例
        
        Args:
            data: API响应数据
            
        Returns:
            Project: 项目实例
        """
        # 处理布尔值响应
        if isinstance(data, bool):
            return None
        
        # 处理任务列表
        tasks = []
        if isinstance(data.get('tasks'), list):
            tasks = [
                Task.from_dict(task_data)
                for task_data in data['tasks']
            ]
        
        return cls(
            name=data.get('name', ''),
            color=data.get('color', '#FFD324'),
            group_id=data.get('groupId'),
            tasks=tasks,
            id=data.get('id'),
            view_mode=data.get('viewMode', 'list'),
            sort_order=data.get('sortOrder'),
            sort_type=data.get('sortType'),
            in_all=data.get('inAll', True),
            kind=data.get('kind', 'TASK')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将项目转换为API请求数据
        
        Returns:
            Dict: API请求数据
        """
        # 只包含必要的字段
        data = {
            'name': self.name,
            'color': self.color,
            'inAll': self.in_all,
            'kind': self.kind,
            'viewMode': self.view_mode
        }
        
        # 只在有值时添加可选字段
        if self.group_id:
            data['groupId'] = self.group_id
        if hasattr(self, 'id') and self.id:
            data['id'] = self.id
        if hasattr(self, 'sortOrder'):
            data['sortOrder'] = self.sortOrder
        
        return data
    
    def add_task(self, task: Task):
        """
        添加任务到项目
        
        Args:
            task: 任务实例
        """
        task.project_id = getattr(self, 'id', None)
        self.tasks.append(task)
    
    def remove_task(self, task_id: str):
        """
        从项目中移除任务
        
        Args:
            task_id: 任务ID
        """
        self.tasks = [
            task for task in self.tasks 
            if getattr(task, 'id', None) != task_id
        ]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取项目中的特定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务实例，如果未找到则返回None
        """
        for task in self.tasks:
            if getattr(task, 'id', None) == task_id:
                return task
        return None
    
    def get_completed_tasks(self) -> List[Task]:
        """
        获取项目中已完成的任务
        
        Returns:
            List[Task]: 已完成的任务列表
        """
        return [task for task in self.tasks if task.is_completed]
    
    def get_uncompleted_tasks(self) -> List[Task]:
        """
        获取项目中未完成的任务
        
        Returns:
            List[Task]: 未完成的任务列表
        """
        return [task for task in self.tasks if not task.is_completed] 