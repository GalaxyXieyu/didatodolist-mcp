"""
基础数据模型
"""
from typing import Dict, Any, TypeVar, Type, Optional
from datetime import datetime
import json

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """所有数据模型的基类"""
    
    def __init__(self, **kwargs):
        """
        初始化模型实例
        
        Args:
            **kwargs: 模型属性
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建模型实例
        
        Args:
            data: 数据字典
            
        Returns:
            模型实例
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典
        
        Returns:
            Dict: 模型数据字典
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    def __str__(self) -> str:
        """返回模型的字符串表示"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def __repr__(self) -> str:
        """返回模型的开发者字符串表示"""
        return f"{self.__class__.__name__}({self.to_dict()})"
    
    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        Args:
            value: ISO格式的日期时间字符串
            
        Returns:
            datetime: 日期时间对象
        """
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None 