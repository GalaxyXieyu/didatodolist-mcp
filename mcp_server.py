"""
滴答清单 MCP 服务器定义
"""

import os
import dotenv
from functools import wraps
from fastmcp import FastMCP
# 尝试导入可能的 AuthError，如果不存在也没关系
try:
    # 假设 fastmcp 提供了特定的认证错误类型
    from fastmcp import AuthError
except ImportError:
    # 如果没有，使用内置的 PermissionError 作为备选
    AuthError = PermissionError

# 导入工具模块
from tools.task_tools import register_task_tools
from tools.project_tools import register_project_tools
from tools.tag_tools import register_tag_tools
from tools.analytics_tools import register_analytics_tools
from tools.goal_tools import register_goal_tools
from tools.official_api import APIError, init_api

# 载入 .env（若存在）
dotenv.load_dotenv()

# --- 鉴权逻辑 ---
EXPECTED_API_KEY = os.environ.get("MCP_API_KEY", "123") # 从环境变量获取，默认'123'

def authenticate_request(context: dict):
    """
    认证回调函数，尝试检查 API Key。

    Args:
        context: 一个包含请求或会话信息的字典 (假设 fastmcp 提供)。
                 我们需要这个 context 包含访问请求头的方式。

    Returns:
        认证成功时返回会话数据 (例如用户ID)。

    Raises:
        AuthError: 如果认证失败。
    """
    # !!! 关键点：如何从 context 中获取请求头？ !!!
    # 假设 context 中有一个 'request' 对象，或者直接有 'headers'
    request_headers = context.get("headers", {}) # 这只是一个猜测！
    api_key = request_headers.get("x-api-key") # 同样是猜测！

    print(f"尝试认证，获取到的 API Key: {api_key}") # 添加日志方便调试

    if api_key != EXPECTED_API_KEY:
        print("认证失败：API Key 无效或缺失")
        # 抛出认证错误，告知客户端未授权
        # 注意：直接 raise Response 可能不行，需要用库定义的错误
        raise AuthError("Unauthorized: Invalid API Key") # 或者 PermissionError

    print("认证成功")
    # 认证成功，返回需要在会话中存储的数据
    # 这个数据可以在工具函数的 context.session 中访问
    return {
        "authenticated_user_id": "system", # 可以是任何你想存储的信息
        "auth_method": "api_key"
    }


def create_server(auth_info=None):
    """
    创建并配置MCP服务器

    Args:
        auth_info: 认证信息字典，包含token或email/password

    Returns:
        配置好的MCP服务器实例
    """
    # OAuth 优先：尝试初始化官方API（读取 oauth_config.json）。
    # 若未配置令牌，继续启动MCP，但工具调用时将提示需要先完成 OAuth 认证。
    try:
        init_api(config_path="oauth_config.json")
        print("已通过 oauth_config.json 初始化官方API 客户端")
    except Exception as e:
        print(f"警告：未能初始化官方API（可能尚未完成 OAuth 认证）：{e}")

    try:
        print(f"期望的 MCP API Key: {EXPECTED_API_KEY}") # 确认环境变量已加载
        # 创建MCP服务器，并直接传入 authenticate 回调
        server = FastMCP(
            name="didatodolist-mcp",
            instructions="滴答清单MCP服务，允许AI模型通过MCP协议操作滴答清单待办事项。",
            authenticate=authenticate_request # <--- 在这里添加认证函数
        )

        # 注册所有工具（auth_info 现已不再必须）
        register_task_tools(server, auth_info or {})
        register_project_tools(server, auth_info or {})
        register_tag_tools(server, auth_info or {})
        register_analytics_tools(server, auth_info or {})
        register_goal_tools(server, auth_info or {})

        print("滴答清单MCP服务初始化成功，并配置了认证回调。")
        return server

    except APIError as e:
        print(f"滴答清单API认证失败: {e.message}")
        raise
    except TypeError as e:
        if 'authenticate' in str(e):
             print("错误：FastMCP 的 Python 版本似乎不支持 'authenticate' 参数。")
             print("请考虑使用反向代理进行认证，或检查 fastmcp-py 的文档。")
        else:
             print(f"初始化MCP服务器时发生类型错误: {str(e)}")
        raise
    except Exception as e:
        print(f"初始化MCP服务器失败: {str(e)}")
        raise

# --- 主程序入口 (示例) ---
if __name__ == "__main__":
    # 从环境变量或配置文件加载认证信息
    dida_auth = {
        "token": os.environ.get("DIDA_TOKEN"),
        # "email": os.environ.get("DIDA_EMAIL"),
        # "password": os.environ.get("DIDA_PASSWORD"),
    }

    if not dida_auth.get("token"):
         print("错误：请设置 DIDA_TOKEN 环境变量")
         exit(1)

    if not os.environ.get("MCP_API_KEY"):
        print("警告：未设置 MCP_API_KEY 环境变量，将使用默认值 '123'")
    else:
        print(f"MCP_API_KEY 已设置为: {EXPECTED_API_KEY}")


    try:
        mcp_server = create_server(dida_auth)
        # 这里需要根据 fastmcp 的文档来正确运行服务器
        print("\n服务器对象已创建。请根据 fastmcp 文档运行服务器。")
        print("例如: python -m fastmcp serve your_module:mcp_server --port 3000")
        # import uvicorn
        # uvicorn.run(mcp_server.app, host="0.0.0.0", port=3000) # 这行可能不正确
    except Exception as e:
         print(f"启动服务器时出错: {e}")