"""
标签数据模型
"""
from typing import Optional, List, Dict, Any
from .base import BaseModel
from .task import Task

class Tag(BaseModel):
    """标签数据模型"""
    
    def __init__(
        self,
        name: str,
        color: str = "#FFD457",
        parent: Optional[str] = None,
        sort_order: int = -1099511693312,
        sort_type: str = "project",
        tasks: Optional[List[Task]] = None,
        **kwargs
    ):
        """
        初始化标签实例
        
        Args:
            name: 标签名称
            color: 标签颜色
            parent: 父标签ID
            sort_order: 排序顺序
            sort_type: 排序类型
            tasks: 标签下的任务列表
            **kwargs: 其他属性
        """
        self.name = name
        self.color = color
        self.parent = parent
        self.sort_order = sort_order
        self.sort_type = sort_type
        self.tasks = tasks or []
        self.label = name  # 标签显示名称与名称相同
        super().__init__(**kwargs)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """
        从API响应数据创建标签实例
        
        Args:
            data: API响应数据
            
        Returns:
            Tag: 标签实例
        """
        tasks = [
            Task.from_dict(task_data)
            for task_data in data.get('tasks', [])
        ]
        
        return cls(
            name=data.get('name', ''),
            color=data.get('color', '#FFD457'),
            tasks=tasks,
            id=data.get('id'),
            parent=data.get('parent'),
            sort_order=data.get('sortOrder', -1099511693312),
            sort_type=data.get('sortType', 'project'),
            label=data.get('label')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将标签转换为API请求数据
        
        Returns:
            Dict: API请求数据
        """
        # 只包含必要的字段，确保类型正确
        data = {
            'color': str(self.color),  # 确保是字符串
            'parent': None,  # 必须是None
            'name': str(self.name),  # 确保是字符串
            'sortOrder': int(self.sort_order),  # 确保是整数
            'label': str(self.name),  # 确保是字符串
            'sortType': str(self.sort_type)  # 确保是字符串
        }
        
        # 只在有值时添加可选字段
        if hasattr(self, 'id') and self.id:
            data['id'] = str(self.id)  # 确保是字符串
        
        return data
    
    def add_task(self, task: Task):
        """
        添加任务到标签
        
        Args:
            task: 任务实例
        """
        if self.name not in task.tags:
            task.add_tag(self.name)
        self.tasks.append(task)
    
    def remove_task(self, task_id: str):
        """
        从标签中移除任务
        
        Args:
            task_id: 任务ID
        """
        task = self.get_task(task_id)
        if task:
            task.remove_tag(self.name)
        self.tasks = [
            task for task in self.tasks 
            if getattr(task, 'id', None) != task_id
        ]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取标签中的特定任务
        
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
        获取标签中已完成的任务
        
        Returns:
            List[Task]: 已完成的任务列表
        """
        return [task for task in self.tasks if task.is_completed]
    
    def get_uncompleted_tasks(self) -> List[Task]:
        """
        获取标签中未完成的任务
        
        Returns:
            List[Task]: 未完成的任务列表
        """
        return [task for task in self.tasks if not task.is_completed] 