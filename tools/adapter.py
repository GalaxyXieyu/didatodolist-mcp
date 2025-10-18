"""
官方 OpenAPI 适配层
将工具层对滴答清单的调用统一为基于 OAuth 的 /open/v1 接口，
并提供时间/状态字段的集中映射与错误处理。

注意：端点与字段以官方文档为准：https://developer.dida365.com/docs#/openapi
若接口差异导致入参/出参变化，应在本模块集中做适配，避免修改上层业务逻辑。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import pytz

from .official_api import (
    DidaOfficialAPI,
    init_api as init_official_api,
    get_api_client,
    APIError,
)


class DidaAdapter:
    """官方 API 的轻量适配器。"""

    def __init__(self, config_path: str = "oauth_config.json"):
        self.config_path = config_path
        # 延迟初始化，首次使用时再创建

    # ---------- 公共工具：时间与状态 ----------
    @staticmethod
    def to_api_datetime(date_str: Optional[str]) -> Optional[str]:
        """
        将本地时间字符串(Asia/Shanghai)转换为官方API要求的UTC格式：
        YYYY-MM-DDTHH:mm:ss.000+0000
        """
        if not date_str:
            return None
        try:
            local_tz = pytz.timezone('Asia/Shanghai')
            # 兼容仅日期或含时分秒
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            dt = local_tz.localize(dt)
            utc_dt = dt.astimezone(pytz.UTC)
            return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
        except Exception:
            # 若无法解析，按原样返回，避免硬失败
            return date_str

    @staticmethod
    def from_api_datetime(date_str: Optional[str]) -> Optional[str]:
        """
        将官方API的UTC时间字符串转换为本地字符串：YYYY-MM-DD HH:MM:SS（Asia/Shanghai）
        """
        if not date_str:
            return None
        try:
            # 常见格式：2024-01-01T08:00:00.000+0000 或带Z
            s = date_str.replace('Z', '+0000')
            # 去掉毫秒
            if '.' in s:
                s = s.split('.')[0] + '+0000'
            dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
            local_dt = dt.astimezone(pytz.timezone('Asia/Shanghai'))
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return date_str

    @staticmethod
    def normalize_task_status(task: Dict[str, Any]) -> Dict[str, Any]:
        """统一任务完成状态字段到 status(0/2) 与 isCompleted(bool)。"""
        t = dict(task)
        is_completed = bool(t.get('isCompleted', False))
        # 有些返回只提供 completed / done 字段，做兜底
        if not is_completed:
            is_completed = str(t.get('completed', '')).lower() in ('true', '1')
        t['isCompleted'] = is_completed
        t['status'] = 2 if is_completed else 0
        return t

    @staticmethod
    def normalize_task_datetimes(task: Dict[str, Any]) -> Dict[str, Any]:
        """将任务中的日期字段统一为本地字符串。"""
        t = dict(task)
        for key in ("startDate", "dueDate", "completedTime", "createdTime", "modifiedTime"):
            if key in t:
                t[key] = DidaAdapter.from_api_datetime(t.get(key))
        # 处理子任务 items 的时间字段
        if isinstance(t.get('items'), list):
            new_items = []
            for it in t['items']:
                it = dict(it)
                for k in ("startDate", "completedTime"):
                    if k in it:
                        it[k] = DidaAdapter.from_api_datetime(it.get(k))
                new_items.append(it)
            t['items'] = new_items
        return t

    # ---------- 初始化与客户端 ----------
    def _api(self) -> DidaOfficialAPI:
        try:
            return get_api_client()
        except Exception:
            # 若尚未初始化，则尝试基于配置初始化
            return init_official_api(config_path=self.config_path)

    # ---------- Projects ----------
    def list_projects(self) -> List[Dict[str, Any]]:
        data = self._api().get("/project")
        # 保持上层期望字段：id, name, color, sortOrder, sortType, modifiedTime
        projects: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for p in data:
                projects.append({k: v for k, v in p.items() if v is not None})
        return projects

    def create_project(self, name: str, color: Optional[str] = None) -> Dict[str, Any]:
        payload = {"name": name}
        if color:
            payload["color"] = color
        return self._api().post("/project", payload)

    def update_project(self, project_id: str, name: Optional[str] = None, color: Optional[str] = None) -> Dict[str, Any]:
        """根据文档，更新项目使用 POST /open/v1/project/{projectId}"""
        payload: Dict[str, Any] = {}
        if name is not None:
            payload['name'] = name
        if color is not None:
            payload['color'] = color
        return self._api().post(f"/project/{project_id}", payload)

    def delete_project(self, project_id: str) -> Any:
        return self._api().delete(f"/project/{project_id}")

    # ---------- Tasks ----------
    def list_tasks(
        self,
        project_id: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        官方文档未提供全局任务列表，使用 /project/{id}/data 提取 tasks。
        若未指定 project_id，则遍历所有项目并汇总。
        支持基于 status/completedTime 的本地 completed 过滤。
        """
        tasks: List[Dict[str, Any]] = []
        projects: List[Dict[str, Any]]
        if project_id:
            projects = [{"id": project_id}]
        else:
            projects = self.list_projects()
        for p in projects:
            pid = p.get('id')
            if not pid:
                continue
            data = self._api().get(f"/project/{pid}/data")
            raw = []
            if isinstance(data, dict):
                raw = data.get('tasks', []) or []
            for t in raw:
                t = self.normalize_task_status(t)
                t = self.normalize_task_datetimes(t)
                tasks.append(t)
        if completed is not None:
            tasks = [t for t in tasks if bool(t.get('isCompleted', False)) == completed]
        return tasks

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        # 转换日期字段
        for k in ("startDate", "dueDate"):
            if k in payload and payload[k]:
                payload[k] = self.to_api_datetime(payload[k])
        # 规范提醒字段：兼容旧的 'reminder'，对齐官方 'reminders'
        if 'reminder' in payload and payload['reminder']:
            rv = payload.pop('reminder')
            if isinstance(rv, str):
                payload['reminders'] = [rv]
        # 子任务日期与时区处理
        if isinstance(payload.get('items'), list):
            fixed_items = []
            for it in payload['items']:
                it = dict(it)
                if it.get('startDate'):
                    it['startDate'] = self.to_api_datetime(it['startDate'])
                if it.get('completedTime'):
                    it['completedTime'] = self.to_api_datetime(it['completedTime'])
                # 若未指定，设置默认时区
                if 'timeZone' not in it and (it.get('startDate') or it.get('completedTime')):
                    it['timeZone'] = 'Asia/Shanghai'
                fixed_items.append({k: v for k, v in it.items() if v is not None})
            payload['items'] = fixed_items
        # 若传入了本地日期但未设置 timeZone，则默认 Asia/Shanghai
        if ('startDate' in payload or 'dueDate' in payload) and 'timeZone' not in payload:
            payload['timeZone'] = 'Asia/Shanghai'
        task = self._api().post("/task", payload)
        task = self.normalize_task_status(task)
        task = self.normalize_task_datetimes(task)
        return task

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        for k in ("startDate", "dueDate"):
            if k in payload and payload[k]:
                payload[k] = self.to_api_datetime(payload[k])
        # 规范提醒字段
        if 'reminder' in payload and payload['reminder']:
            rv = payload.pop('reminder')
            if isinstance(rv, str):
                payload['reminders'] = [rv]
        # 子任务日期与时区处理
        if isinstance(payload.get('items'), list):
            fixed_items = []
            for it in payload['items']:
                it = dict(it)
                if it.get('startDate'):
                    it['startDate'] = self.to_api_datetime(it['startDate'])
                if it.get('completedTime'):
                    it['completedTime'] = self.to_api_datetime(it['completedTime'])
                if 'timeZone' not in it and (it.get('startDate') or it.get('completedTime')):
                    it['timeZone'] = 'Asia/Shanghai'
                fixed_items.append({k: v for k, v in it.items() if v is not None})
            payload['items'] = fixed_items
        if ('startDate' in payload or 'dueDate' in payload) and 'timeZone' not in payload:
            payload['timeZone'] = 'Asia/Shanghai'
        # 文档：更新任务使用 POST /open/v1/task/{taskId}
        task = self._api().post(f"/task/{task_id}", payload)
        # 有些接口返回布尔；若返回为空，补回请求值
        if isinstance(task, bool) and task is True:
            # 尝试重新获取任务详情（若文档提供 /task/{id} 可用，则可实现；这里直接回填请求）
            task = {"id": task_id, **data}
        task = self.normalize_task_status(task)
        task = self.normalize_task_datetimes(task)
        return task

    def delete_task(self, project_id: str, task_id: str) -> Any:
        # 文档：DELETE /open/v1/project/{projectId}/task/{taskId}
        return self._api().delete(f"/project/{project_id}/task/{task_id}")

    def complete_task(self, project_id: str, task_id: str) -> Any:
        # 文档：POST /open/v1/project/{projectId}/task/{taskId}/complete
        return self._api().post(f"/project/{project_id}/task/{task_id}/complete", {})


# 单例适配器供工具层复用
adapter = DidaAdapter()

__all__ = [
    "DidaAdapter",
    "adapter",
    "APIError",
]
