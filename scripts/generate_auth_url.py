#!/usr/bin/env python3
"""
滴答清单OAuth授权URL生成器

使用: python scripts/generate_auth_url.py
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode


def main():
    parser = argparse.ArgumentParser(description="滴答清单OAuth授权URL生成器")
    parser.add_argument("--config", default="oauth_config.json", help="配置文件路径")
    parser.add_argument("--port", type=int, default=38000, help="回调端口")
    parser.add_argument("--scope", default="tasks:read tasks:write", help="权限范围")

    args = parser.parse_args()

    # 加载配置
    config_path = Path(args.config)
    if not config_path.exists():
        print("❌ 配置文件不存在，请先创建 oauth_config.json")
        print("\n参考 oauth_config.json.example 创建配置文件")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    client_id = config.get("client_id")
    if not client_id:
        print("❌ 配置文件缺少 client_id")
        return

    # 生成授权URL
    redirect_uri = f"http://localhost:{args.port}/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": args.scope,
        "state": "auth",
        "response_type": "code"
    }

    auth_url = f"https://dida365.com/oauth/authorize?{urlencode(params)}"

    # 显示信息
    print("\n" + "="*70)
    print("滴答清单OAuth授权URL")
    print("="*70)
    print(f"\nClient ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Scope: {args.scope}")
    print("\n" + "="*70)
    print("授权URL:")
    print("="*70)
    print(f"\n{auth_url}\n")
    print("="*70)
    print("使用步骤:")
    print("="*70)
    print("1. 复制上面的URL到浏览器")
    print("2. 登录滴答清单账号并授权")
    print(f"3. 确保本地服务器运行在端口 {args.port}\n")


if __name__ == "__main__":
    main()
