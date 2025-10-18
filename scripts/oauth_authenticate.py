#!/usr/bin/env python3
"""
滴答清单OAuth完整认证流程

功能:
1. 启动本地回调服务器
2. 生成并显示授权URL
3. 接收授权码
4. 交换访问令牌
5. 测试API调用
6. 保存配置

使用:
    python scripts/oauth_authenticate.py
    python scripts/oauth_authenticate.py --port 38000
"""

import sys
import argparse
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.oauth_auth import DidaOAuthClient


def main():
    parser = argparse.ArgumentParser(
        description="滴答清单OAuth认证"
    )

    parser.add_argument(
        "--config",
        default="oauth_config.json",
        help="配置文件路径"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=38000,
        help="回调服务器端口"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("滴答清单OAuth 2.0 认证")
    print("="*70 + "\n")

    # 加载配置
    config_path = Path(args.config)

    if not config_path.exists():
        print("❌ 配置文件不存在")
        print(f"\n请创建配置文件: {args.config}")
        print("\n示例配置:")
        print(json.dumps({
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": f"http://localhost:{args.port}/callback"
        }, indent=2))
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri", f"http://localhost:{args.port}/callback")

    if not client_id or not client_secret:
        print("❌ 配置文件缺少 client_id 或 client_secret")
        sys.exit(1)

    # 创建OAuth客户端
    oauth_client = DidaOAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri
    )

    # 执行授权流程
    print("步骤1: 启动本地回调服务器")
    print(f"端口: {args.port}\n")

    success = oauth_client.authorize(auto_open_browser=False)

    if success:
        # 保存令牌
        oauth_client.save_tokens(args.config)

        print("\n" + "="*70)
        print("✅ OAuth认证成功!")
        print("="*70)
        print(f"\n访问令牌已保存到: {args.config}")
        print(f"Access Token: {oauth_client.access_token[:30]}...")

        # 测试API
        print("\n正在测试API...")
        try:
            import requests
            headers = oauth_client.get_headers()
            response = requests.get(
                "https://api.dida365.com/open/v1/project",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                projects = response.json()
                print(f"✅ API测试成功! 找到 {len(projects)} 个项目\n")
            else:
                print(f"⚠️  API测试失败: HTTP {response.status_code}\n")

        except Exception as e:
            print(f"⚠️  API测试失败: {str(e)}\n")

    else:
        print("\n❌ OAuth认证失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
