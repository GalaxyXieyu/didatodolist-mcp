#!/usr/bin/env python3
"""
最小验证脚本：基于官方 /open/v1 端点，跑通创建→更新→完成→删除 闭环。

前置：已完成 OAuth 认证，存在 oauth_config.json。

步骤：
1) 创建临时项目
2) 在项目下创建任务（含 desc、reminders、items、timeZone/日期）
3) 更新任务（修改 desc/priority/reminders）
4) 完成任务
5) 删除任务
6) 删除临时项目
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta

from tools.official_api import init_api, APIError
from tools.adapter import adapter


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    print(f"[{ts()}] 初始化 OAuth 客户端…")
    try:
        init_api(config_path="oauth_config.json")
    except Exception as e:
        print("初始化失败：请先运行 `python scripts/oauth_authenticate.py --port 38000` 完成认证。")
        print(f"详情: {e}")
        return 1

    # 1) 创建临时项目
    demo_name = f"MCP Demo {int(time.time())}"
    print(f"[{ts()}] 创建演示项目: {demo_name}")
    project = adapter.create_project(name=demo_name, color="#F18181")
    project_id = project.get("id")
    if not project_id:
        print("创建项目失败：未返回 id")
        return 1
    print(f"[{ts()}] 项目ID: {project_id}")

    try:
        # 2) 创建任务
        start_local = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        due_local = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts()}] 创建任务…")
        task = adapter.create_task({
            "title": "Demo Task",
            "projectId": project_id,
            "content": "Demo content",
            "desc": "Checklist description",
            "isAllDay": False,
            "startDate": start_local,
            "dueDate": due_local,
            "timeZone": "Asia/Shanghai",
            "reminders": ["TRIGGER:PT0S"],
            "repeatFlag": "RRULE:FREQ=DAILY;INTERVAL=1",
            "priority": 1,
            "sortOrder": 12345,
            "items": [
                {
                    "title": "Subtask A",
                    "isAllDay": False,
                    "startDate": start_local,
                    "sortOrder": 1
                }
            ]
        })
        task_id = task.get("id")
        if not task_id:
            print("创建任务失败：未返回 id")
            return 1
        print(f"[{ts()}] 任务ID: {task_id}")

        # 3) 更新任务
        print(f"[{ts()}] 更新任务…")
        task = adapter.update_task(task_id, {
            "projectId": project_id,
            "desc": "Checklist description (updated)",
            "priority": 3,
            "reminders": ["TRIGGER:P0DT9H0M0S"],
        })
        print(f"[{ts()}] 更新后 priority={task.get('priority')} reminders={task.get('reminders')}")

        # 4) 完成任务
        print(f"[{ts()}] 完成任务…")
        adapter.complete_task(project_id, task_id)
        tasks_after = adapter.list_tasks(project_id=project_id, completed=True)
        done = next((t for t in tasks_after if t.get('id') == task_id), None)
        print(f"[{ts()}] 完成校验 isCompleted={done.get('isCompleted') if done else None}")

        # 5) 删除任务
        print(f"[{ts()}] 删除任务…")
        adapter.delete_task(project_id, task_id)
        print(f"[{ts()}] 任务已删除")
    finally:
        # 6) 清理项目
        print(f"[{ts()}] 删除项目…")
        try:
            adapter.delete_project(project_id)
            print(f"[{ts()}] 项目已删除")
        except APIError as e:
            print(f"删除项目失败（可忽略）：{e}")

    print(f"[{ts()}] 演示完毕 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
