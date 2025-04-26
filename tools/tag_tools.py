"""
标签相关MCP工具
"""

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from .base_api import APIError, init_api, get, post, put, delete

def register_tag_tools(server: FastMCP, auth_info: Dict[str, Any]):
    """
    注册标签相关工具到MCP服务器
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息字典，包含token或email/password
    """
    # 初始化API
    init_api(**auth_info)
    
    @server.tool()
    def get_tags() -> List[Dict[str, Any]]:
        """
        获取所有标签列表
        
        Returns:
            标签列表
        """
        response = get("/api/v2/batch/check/0")
        tags_data = response.get('tags', [])
        
        # 简化标签数据，不包含任务
        result = []
        for tag in tags_data:
            tag_data = tag.copy()
            result.append(tag_data)
            
        return result
    
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
        tag_data = {
            "add": [{
                "name": name,
                "label": name,
                "color": color,
                "sortOrder": 0,
                "sortType": "name",
                "parent": None,
                "type": 1
            }],
            "update": [],
            "delete": []
        }
        
        # 移除None值的字段
        tag_data["add"][0] = {k: v for k, v in tag_data["add"][0].items() if v is not None}
        
        response = post("/api/v2/batch/tag", data=tag_data)
        return tag_data["add"][0]
    
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
        # 获取当前标签信息
        tags = get_tags()
        current_tag = None
        for tag in tags:
            if tag.get('name') == tag_id_or_name:
                current_tag = tag
                break
        
        if not current_tag:
            return {
                "success": False,
                "info": f"未找到名称为 '{tag_id_or_name}' 的标签",
                "data": None
            }
        
        try:
            old_name = tag_id_or_name
            # 如果需要重命名标签
            if name and name != old_name:
                rename_data = {
                    "name": old_name,
                    "newName": name
                }
                put("/api/v2/tag/rename", data=rename_data)
                old_name = name  # 更新后续操作使用的名称
            
            # 构建更新数据
            update_data = {
                "add": [],
                "update": [{
                    "name": name or old_name,
                    "label": name or old_name,
                    "color": color if color is not None else current_tag.get('color'),
                    "sortOrder": current_tag.get('sortOrder', 0),
                    "sortType": current_tag.get('sortType', 'name'),
                    "parent": None,
                    "type": current_tag.get('type', 1)
                }],
                "delete": []
            }
            
            response = post("/api/v2/batch/tag", data=update_data)
            return {
                "success": True,
                "info": "标签更新成功",
                "data": update_data["update"][0]
            }
        except Exception as e:
            return {
                "success": False,
                "info": f"更新标签失败: {str(e)}",
                "data": None
            }
    
    @server.tool()
    def delete_tag(tag_id_or_name: str) -> Dict[str, Any]:
        """
        删除标签
        
        Args:
            tag_id_or_name: 标签ID或标签名称
            
        Returns:
            删除操作的响应
        """
        try:
            # 获取标签信息用于返回
            tags = get_tags()
            tag = None
            for t in tags:
                if t.get('name') == tag_id_or_name:
                    tag = t
                    break
                    
            if not tag:
                return {
                    "success": False,
                    "info": f"未找到名称为 '{tag_id_or_name}' 的标签",
                    "data": None
                }
            
            # 准备删除数据
            delete_data = {
                "name": tag_id_or_name
            }

            # 发送删除请求
            delete("/api/v2/tag/delete", data=delete_data)
            
            return {
                "success": True,
                "info": f"成功删除标签 '{tag_id_or_name}'",
                "data": tag
            }
        except Exception as e:
            return {
                "success": False,
                "info": f"删除标签失败: {str(e)}",
                "data": None
            }
    
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
        try:
            rename_data = {
                "name": old_name,
                "newName": new_name
            }
            
            response = put("/api/v2/tag/rename", data=rename_data)
            return {
                "success": True,
                "info": f"成功将标签从 '{old_name}' 重命名为 '{new_name}'",
                "data": {
                    "old_name": old_name,
                    "new_name": new_name
                }
            }
        except Exception as e:
            return {
                "success": False,
                "info": f"重命名标签失败: {str(e)}",
                "data": None
            }
    
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
        try:
            merge_data = {
                "fromName": source_name,
                "toName": target_name
            }
            
            response = put("/api/v2/tag/merge", data=merge_data)
            return {
                "success": True,
                "info": f"成功将标签 '{source_name}' 合并到 '{target_name}'",
                "data": {
                    "source_tag": source_name,
                    "target_tag": target_name
                }
            }
        except Exception as e:
            return {
                "success": False,
                "info": f"合并标签失败: {str(e)}",
                "data": None
            } 