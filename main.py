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
from tools.official_api import init_api

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
        default="oauth_config.json"
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

def ensure_oauth_ready(config_path: str = "oauth_config.json") -> bool:
    """尝试用 oauth_config.json 初始化官方API，失败则提示先执行认证脚本。"""
    try:
        init_api(config_path=config_path)
        return True
    except Exception as e:
        print("未检测到有效的 OAuth access_token。")
        print("请先运行 OAuth 认证脚本：")
        print("  python scripts/oauth_authenticate.py --port 38000")
        print("完成后将生成 oauth_config.json，再次运行本服务即可。")
        print(f"详情: {e}")
        return False

def main():
    """主函数"""
    args = parse_args()
    if not ensure_oauth_ready(config_path=args.config):
        # 不中止运行，允许用户仅安装/查看说明
        pass

    # 创建MCP服务器
    server = create_server({})

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