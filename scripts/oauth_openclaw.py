#!/usr/bin/env python3
"""
滴答清单 OAuth 本地授权并写入 OpenClaw 配置

用途:
1) 启动本地回调服务器
2) 生成授权 URL
3) 交换 access_token / refresh_token
4) 写回 ~/.openclaw/openclaw.json (默认插件 id: dida-openapi)

用法示例:
  python3 scripts/oauth_openclaw.py
  python3 scripts/oauth_openclaw.py --open-browser
  python3 scripts/oauth_openclaw.py --config ~/.openclaw/openclaw.json --plugin-id dida-openapi
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from utils.oauth_auth import DidaOAuthClient


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_config(path: Path, data: dict) -> Path:
    backup = path.with_suffix(".json.bak." + datetime.now().strftime("%Y%m%d-%H%M%S"))
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description="滴答清单 OAuth 授权并写入 OpenClaw 配置")
    parser.add_argument("--config", default=str(Path.home() / ".openclaw" / "openclaw.json"))
    parser.add_argument("--plugin-id", default="dida-openapi")
    parser.add_argument("--open-browser", action="store_true", help="自动打开浏览器授权")
    parser.add_argument("--client-id", default=None)
    parser.add_argument("--client-secret", default=None)
    parser.add_argument("--redirect-uri", default=None)
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    config = load_config(config_path)

    plugins = config.setdefault("plugins", {})
    plugins.setdefault("enabled", True)
    entries = plugins.setdefault("entries", {})
    entry = entries.setdefault(args.plugin_id, {})
    entry.setdefault("enabled", True)
    plugin_config = entry.setdefault("config", {})

    client_id = args.client_id or plugin_config.get("clientId")
    client_secret = args.client_secret or plugin_config.get("clientSecret")
    redirect_uri = args.redirect_uri or plugin_config.get("redirectUri", "http://localhost:38000/callback")

    if not client_id or not client_secret:
        print("❌ 缺少 clientId/clientSecret，请先写入 openclaw.json 或通过参数传入")
        return 1

    oauth = DidaOAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    print("\n=== 滴答清单 OAuth 授权 (OpenClaw) ===\n")
    success = oauth.authorize(auto_open_browser=args.open_browser)

    if not success:
        print("\n❌ OAuth 授权失败")
        return 1

    plugin_config["clientId"] = client_id
    plugin_config["clientSecret"] = client_secret
    plugin_config["redirectUri"] = redirect_uri
    plugin_config.setdefault("timeoutMs", 15000)
    plugin_config.setdefault("autoRefresh", True)
    plugin_config["accessToken"] = oauth.access_token
    if oauth.refresh_token is not None:
        plugin_config["refreshToken"] = oauth.refresh_token
    else:
        plugin_config.pop("refreshToken", None)

    tools = config.setdefault("tools", {})
    allow = tools.get("allow")
    if allow is None:
        tools["allow"] = [args.plugin_id]
    elif isinstance(allow, list):
        if args.plugin_id not in allow:
            allow.append(args.plugin_id)

    backup = write_config(config_path, config)
    print("\n✅ 已写入 OpenClaw 配置:")
    print(f"- config: {config_path}")
    print(f"- backup: {backup}")
    print("\n请重启 OpenClaw Gateway 以加载最新 token。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
