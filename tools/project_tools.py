"""
项目相关MCP工具
"""

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from .base_api import APIError, init_api, get, post, put, delete

# --- 模块级核心逻辑函数 ---

def get_projects_logic() -> List[Dict[str, Any]]:
    """
    获取所有项目列表 (逻辑部分)
    
    Returns:
        项目列表 (包含 id, name, color, sortOrder, sortType, modifiedTime)
    """
    response = get("/api/v2/batch/check/0")
    projects_data = response.get('projectProfiles', [])
    
    # 转换为更有用的格式
    result = []
    for project in projects_data:
        project_data = {
            "id": project.get("id"),
            "name": project.get("name"),
            "color": project.get("color"),
            "sortOrder": project.get("sortOrder"),
            "sortType": project.get("sortType"),
            "modifiedTime": project.get("modifiedTime"),
            # 考虑是否需要添加 'description' 或 'isArchived' 等字段
            "description": project.get("description", None), # 假设 API 可能返回描述
            "isArchived": project.get("isArchived", False) # 假设 API 可能返回归档状态
        }
        # 移除值为 None 的键，以保持一致性
        result.append({k: v for k, v in project_data.items() if v is not None})
        
    return result

def create_project_logic(
    name: str,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建新项目 (逻辑部分)
    
    Args:
        name: 项目名称
        color: 项目颜色，如 "#FF0000" 表示红色
        
    Returns:
        创建的项目信息 (API 原始响应)
    """
    project_data = {
        "name": name,
        "color": color,
        "inAll": True # 滴答清单 API 通常需要此字段
    }
    
    # 移除None值的字段
    project_data = {k: v for k, v in project_data.items() if v is not None}
    
    response = post("/api/v2/project", data=project_data)
    return response # 返回 API 的原始响应，可能包含更完整的项目信息

def update_project_logic(
    project_id_or_name: str,
    name: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """
    更新项目信息 (逻辑部分)
    
    Args:
        project_id_or_name: 项目ID或项目名称
        name: 新项目名称
        color: 新项目颜色
        
    Returns:
        更新操作的结果字典 (包含 success, info, data)
    """
    # 获取项目信息
    projects = get_projects_logic()
    
    # 查找项目
    project = None
    project_id = None
    # 先尝试按ID查找
    for p in projects:
        if p.get('id') == project_id_or_name:
            project = p
            project_id = p.get('id')
            break
            
    # 如果没找到，按名称查找
    if not project:
        for p in projects:
            if p.get('name') == project_id_or_name:
                project = p
                project_id = p.get('id')
                break
    
    if not project or not project_id:
        return {
            "success": False,
            "info": f"未找到ID或名称为 '{project_id_or_name}' 的项目",
            "data": None
        }
        
    try:
        # 准备更新数据
        update_data = {
            "id": project_id,
            "name": name if name is not None else project.get('name'),
            "color": color if color is not None else project.get('color')
        }
        # 移除 name 和 color 为 None 的情况，避免 API 报错
        update_data = {k:v for k,v in update_data.items() if v is not None}
        
        # 发送更新请求
        response = put(f"/api/v2/project/{project_id}", data=update_data)
        
        # 尝试从响应中获取更新后的数据，如果API不返回，则使用发送的数据
        updated_project_data = response if isinstance(response, dict) else update_data
        updated_project_data['id'] = project_id # 确保 ID 在返回数据中
        
        return {
            "success": True,
            "info": "项目更新成功",
            "data": updated_project_data
        }
    except Exception as e:
        print(f"更新项目失败: {str(e)}") # 打印错误信息
        return {
            "success": False,
            "info": f"更新项目失败: {str(e)}",
            "data": None
        }

def delete_project_logic(project_id_or_name: str) -> Dict[str, Any]:
    """
    删除项目 (逻辑部分)
    
    Args:
        project_id_or_name: 项目ID或项目名称
        
    Returns:
        删除操作的响应字典 (包含 success, info, data)
    """
    # 获取项目信息
    projects = get_projects_logic()
    
    # 查找项目
    project = None
    project_id = None
    # 先尝试按ID查找
    for p in projects:
        if p.get('id') == project_id_or_name:
            project = p
            project_id = p.get('id')
            break
            
    # 如果没找到，按名称查找
    if not project:
        for p in projects:
            if p.get('name') == project_id_or_name:
                project = p
                project_id = p.get('id')
                break
    
    if not project or not project_id:
        return {
            "success": False,
            "info": f"未找到ID或名称为 '{project_id_or_name}' 的项目",
            "data": None
        }
        
    try:
        # 发送删除请求
        # 滴答清单删除项目通常不需要请求体，直接调用DELETE方法
        delete(f"/api/v2/project/{project_id}")
        
        return {
            "success": True,
            "info": f"成功删除项目 '{project.get('name')}'",
            "data": project # 返回被删除项目的信息
        }
    except Exception as e:
        print(f"删除项目失败: {str(e)}") # 打印错误信息
        return {
            "success": False,
            "info": f"删除项目失败: {str(e)}",
            "data": None
        }


# --- MCP工具注册 ---

def register_project_tools(server: FastMCP, auth_info: Dict[str, Any]):
    """
    注册项目相关工具到MCP服务器
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息字典，包含token或email/password
    """
    # 初始化API (如果其他模块未初始化)
    # 可以添加一个检查，避免重复初始化
    if not getattr(server, '_api_initialized', False):
        try:
            init_api(**auth_info)
            server._api_initialized = True # 标记已初始化
        except Exception as e:
            print(f"API 初始化失败 (project_tools): {e}")
            # 可能需要决定是否继续注册工具

    @server.tool()
    def get_projects() -> List[Dict[str, Any]]:
        """
        获取所有项目列表
        (调用模块级逻辑函数)
        
        Returns:
            项目列表
        """
        return get_projects_logic()
    
    @server.tool()
    def create_project(
        name: str,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建新项目
        (调用模块级逻辑函数)
        
        Args:
            name: 项目名称
            color: 项目颜色，如 "#FF0000" 表示红色
            
        Returns:
            创建的项目信息 (API 原始响应)
        """
        return create_project_logic(name=name, color=color)
    
    @server.tool()
    def update_project(
        project_id_or_name: str,
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新项目信息
        (调用模块级逻辑函数)
        
        Args:
            project_id_or_name: 项目ID或项目名称
            name: 新项目名称
            color: 新项目颜色
            
        Returns:
            更新操作的结果字典 (包含 success, info, data)
        """
        return update_project_logic(project_id_or_name=project_id_or_name, name=name, color=color)
    
    @server.tool()
    def delete_project(project_id_or_name: str) -> Dict[str, Any]:
        """
        删除项目
        (调用模块级逻辑函数)
        
        Args:
            project_id_or_name: 项目ID或项目名称
            
        Returns:
            删除操作的响应字典 (包含 success, info, data)
        """
        return delete_project_logic(project_id_or_name=project_id_or_name)

# 导出可供外部引用的函数
__all__ = [
    'get_projects_logic',
    'create_project_logic',
    'update_project_logic',
    'delete_project_logic',
    'register_project_tools'
] 