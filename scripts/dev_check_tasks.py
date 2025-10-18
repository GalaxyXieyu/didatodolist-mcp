#!/usr/bin/env python3
"""
开发辅助脚本：快速拉取任务并筛选今日未完成任务，打印前若干条。

用法：
    python scripts/dev_check_tasks.py
"""

from __future__ import annotations

from dotenv import load_dotenv
from tools.official_api import init_api
from tools.adapter import adapter


def main() -> int:
    load_dotenv()
    try:
        init_api(config_path="oauth_config.json")
    except Exception:
        # 允许仅使用 .env 的 token 覆盖
        pass

    tasks = adapter.list_tasks()
    print(f"All tasks: {len(tasks)}")
    # 过滤：未完成
    inc = [t for t in tasks if not t.get('isCompleted')]
    print(f"Incomplete: {len(inc)}")
    for t in inc[:10]:
        print(f"- {t.get('title')} | project={t.get('projectName')} | due={t.get('dueDate')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
