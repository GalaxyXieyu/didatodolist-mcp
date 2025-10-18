"""
标签相关MCP工具
"""

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from .adapter import adapter, APIError

def register_tag_tools(server: FastMCP, auth_info: Dict[str, Any]):
    """
    注册标签相关工具到MCP服务器
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息字典，包含token或email/password
    """
    # 适配层初始化在首次调用时自动进行
    
    @server.tool()
    def get_tags() -> List[Dict[str, Any]]:
        """
        获取所有标签列表
        
        Returns:
            标签列表
        """
        # 官方文档若无标签API，这里通过任务聚合推断标签（只读）
        try:
            tasks = adapter.list_tasks()
        except Exception:
            tasks = []
        agg: dict[str, dict] = {}
        for t in tasks or []:
            for name in t.get('tags', []) or []:
                if name not in agg:
                    agg[name] = {"name": name, "label": name}
        return list(agg.values())
    
    @server.tool()
    def create_tag(
        name: str,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建新标签
        
        Args:
            name: 标签名称
            color: 标签颜色，如 "#FF0000" 表示红色
            
        Returns:
            创建的标签信息
        """
        raise ValueError("标签创建在官方开放API中不可用或未开放：仅支持只读标签视图")
    
    @server.tool()
    def update_tag(
        tag_id_or_name: str,
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新标签信息
        
        Args:
            tag_id_or_name: 标签ID或标签名称
            name: 新标签名称
            color: 新标签颜色
            
        Returns:
            更新后的标签信息
        """
        raise ValueError("标签更新/重命名/颜色在官方开放API中不可用或未开放：仅支持只读标签视图")
    
    @server.tool()
    def delete_tag(tag_id_or_name: str) -> Dict[str, Any]:
        """
        删除标签
        
        Args:
            tag_id_or_name: 标签ID或标签名称
            
        Returns:
            删除操作的响应
        """
        raise ValueError("标签删除在官方开放API中不可用或未开放：仅支持只读标签视图")
    
    @server.tool()
    def rename_tag(old_name: str, new_name: str) -> Dict[str, Any]:
        """
        重命名标签
        
        Args:
            old_name: 旧标签名称
            new_name: 新标签名称
            
        Returns:
            操作响应
        """
        raise ValueError("标签重命名在官方开放API中不可用或未开放：仅支持只读标签视图")
    
    @server.tool()
    def merge_tags(source_name: str, target_name: str) -> Dict[str, Any]:
        """
        合并标签
        
        Args:
            source_name: 源标签名称（将被合并的标签）
            target_name: 目标标签名称（合并到的标签）
            
        Returns:
            操作响应
        """
        raise ValueError("标签合并在官方开放API中不可用或未开放：仅支持只读标签视图")