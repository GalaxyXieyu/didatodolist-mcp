#!/usr/bin/env python
"""
滴答清单 MCP 服务入口点
允许AI模型通过MCP协议访问和操作滴答清单待办事项
"""

import os
import sys
import argparse
import json
from pathlib import Path
import dotenv
from fastmcp import FastMCP
from mcp_server import create_server
from utils.auth_utils import get_auth_info_with_login

# 加载环境变量
dotenv.load_dotenv()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="滴答清单 MCP 服务"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="安装到Claude Desktop或其他MCP客户端"
    )
    parser.add_argument(
        "--token",
        help="滴答清单访问令牌"
    )
    parser.add_argument(
        "--email",
        help="滴答清单账户邮箱"
    )
    parser.add_argument(
        "--phone",
        help="滴答清单账户手机号"
    )
    parser.add_argument(
        "--password",
        help="滴答清单账户密码"
    )
    parser.add_argument(
        "--config",
        help="配置文件路径",
        default="config.json"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="服务器端口号（用于SSE传输方式）"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="服务器主机（用于SSE传输方式）"
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="使用SSE传输方式而不是stdio"
    )

    return parser.parse_args()

def get_auth_info(args):
    """
    获取认证信息，优先使用token，如果有邮箱密码但没有token，则尝试登录并保存token

    Args:
        args: 命令行参数

    Returns:
        Dict[str, str]: 认证信息
    """
    # 分别获取手机号和邮箱
    phone = args.phone
    email = args.email

    # 使用新的认证工具函数获取认证信息
    auth_info, is_new_token = get_auth_info_with_login(
        args_token=args.token,
        args_phone=phone,
        args_email=email,
        args_password=args.password,
        env_token=os.environ.get("DIDA_TOKEN"),
        env_phone=os.environ.get("DIDA_PHONE"),
        env_email=os.environ.get("DIDA_EMAIL"),
        env_password=os.environ.get("DIDA_PASSWORD"),
        config_path=args.config
    )

    if not auth_info:
        print("错误: 未找到认证信息。请通过命令行参数、环境变量或配置文件提供滴答清单的访问令牌或邮箱密码。")
        sys.exit(1)

    # 如果是新获取的token，额外打印信息
    if is_new_token:
        # 判断使用的是手机号还是邮箱
        if "phone" in auth_info:
            login_type = "手机号"
        else:
            login_type = "邮箱"
        print(f"已使用{login_type}密码成功获取新token并保存至配置文件。")
        print("今后启动程序时将自动使用保存的token进行认证，无需重复登录。")
        print("即使传入相同的账号密码参数，也会优先使用已保存的token，避免频繁登录触发风控。")

    return auth_info

def main():
    """主函数"""
    args = parse_args()
    auth_info = get_auth_info(args)

    # 显示认证方式
    if "token" in auth_info:
        print("使用token认证")
    elif "phone" in auth_info:
        print("使用手机号密码认证")
    else:
        print("使用邮箱密码认证")

    # 创建MCP服务器
    server = create_server(auth_info)

    # 启动服务器
    if args.install:
        # 安装到Claude Desktop
        print("正在安装到MCP客户端...")
        os.system("fastmcp install")
    else:
        # 直接运行
        print("启动滴答清单MCP服务器...")
        if args.sse:
            # 使用SSE传输方式
            server.run(transport="sse", host=args.host, port=args.port)
        else:
            # 使用默认stdio传输方式
            print("使用stdio传输方式")
            server.run()

if __name__ == "__main__":
    main()