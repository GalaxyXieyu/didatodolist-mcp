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
import os


def write_env_tokens(env_path: Path, access_token: str, refresh_token: str | None):
    """将令牌写入 .env（若存在则更新相关行）。"""
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    def upsert(key: str, value: str | None):
        nonlocal lines
        # 删除旧行
        lines = [ln for ln in lines if not ln.startswith(f"{key}=")]
        if value is not None:
            lines.append(f"{key}={value}")

    upsert("DIDA_ACCESS_TOKEN", access_token)
    upsert("DIDA_REFRESH_TOKEN", refresh_token or "")

    content = "\n".join(lines) + ("\n" if not content_endswith_newline(lines) else "")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)


def content_endswith_newline(lines: list[str]) -> bool:
    if not lines:
        return False
    return lines[-1].endswith("\n")


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

    use_env_only = False
    config = {}
    if not config_path.exists():
        # 支持使用环境变量模式（无配置文件）
        use_env_only = True
        client_id = os.environ.get("DIDA_CLIENT_ID")
        client_secret = os.environ.get("DIDA_CLIENT_SECRET")
        redirect_uri = os.environ.get("DIDA_REDIRECT_URI", f"http://localhost:{args.port}/callback")
        if not client_id or not client_secret:
            print("❌ 配置文件不存在，且未检测到环境变量 DIDA_CLIENT_ID / DIDA_CLIENT_SECRET")
            print(f"\n可选择：\n1) 创建配置文件: {args.config}\n2) 或在 .env 中设置 DIDA_CLIENT_ID / DIDA_CLIENT_SECRET / DIDA_REDIRECT_URI")
            print("\n示例配置:")
            print(json.dumps({
                "client_id": "YOUR_CLIENT_ID",
                "client_secret": "YOUR_CLIENT_SECRET",
                "redirect_uri": f"http://localhost:{args.port}/callback"
            }, indent=2))
            sys.exit(1)
    else:
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
        if use_env_only:
            # 直接写入 .env（不会加入版本控制）
            env_path = Path(".env")
            write_env_tokens(env_path, oauth_client.access_token, oauth_client.refresh_token)
            print(f"\n已写入 .env: DIDA_ACCESS_TOKEN / DIDA_REFRESH_TOKEN")
        else:
            oauth_client.save_tokens(args.config)

        print("\n" + "="*70)
        print("✅ OAuth认证成功!")
        print("="*70)
        if not use_env_only:
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
