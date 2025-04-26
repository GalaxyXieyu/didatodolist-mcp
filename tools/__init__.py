"""
滴答清单 MCP 工具包
"""
 
__all__ = ["task_tools", "project_tools", "tag_tools", "echo_tools"] 

from typing import Dict, Any

from fastmcp import FastMCP

# 导入工具注册函数
from .goal_tools import register_goal_tools
from .analytics_tools import register_analytics_tools


def register_all_tools(server: FastMCP, auth_info: Dict[str, Any]) -> None:
    """
    注册所有工具到MCP服务器
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息
    """
    # 注册目标管理工具
    register_goal_tools(server, auth_info)
    
    # 注册数据分析工具
    register_analytics_tools(server, auth_info)
    
    print("已注册所有工具到MCP服务器") 