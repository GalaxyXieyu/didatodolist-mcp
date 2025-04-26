"""
数据分析工具
提供任务和目标的统计分析功能
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime, timedelta, date
from collections import Counter

from fastmcp import FastMCP
from utils.csv_handler import CSVHandler
from utils.date.date_utils import (
    get_current_time, parse_date, format_date, 
    get_date_range, date_diff_days
)
from utils.text.text_analysis import (
    extract_keywords, normalize_keywords, segment_text
)

# 导入task_tools中的方法，用于获取任务数据
from tools.task_tools import get_tasks_logic as get_dida_tasks
# 导入project_tools中的方法，用于获取项目数据 (假设已重构)
try:
    from tools.project_tools import get_projects_logic
except ImportError:
    print("警告：无法从 tools.project_tools 导入 get_projects_logic。目标分析将仅依赖CSV。")
    get_projects_logic = None


class AnalyticsManager:
    """
    数据分析管理器
    负责任务和目标的统计分析
    """
    
    def __init__(self, goals_csv_path: str = 'data/goals.csv', 
                tasks_csv_path: str = 'data/tasks.csv'):
        """
        初始化数据分析管理器
        
        Args:
            goals_csv_path: 目标CSV文件路径
            tasks_csv_path: 任务CSV文件路径
        """
        self.goals_csv_path = goals_csv_path
        self.tasks_csv_path = tasks_csv_path
        
        # 创建CSV处理器
        self.goals_handler = CSVHandler(goals_csv_path)
        
        # 检查任务CSV是否存在 (这部分可能不再需要，因为我们优先用API)
        if os.path.exists(tasks_csv_path):
            self.tasks_handler = CSVHandler(tasks_csv_path) 
        else:
            self.tasks_handler = None
            
        # 缓存
        self.dida_tasks = None
        self.all_goals = None
        self.projects = None
    
    def _get_tasks_from_api(self, force_refresh=False):
        """从滴答清单API获取任务数据 (优先使用API)"""
        if self.dida_tasks is None or force_refresh:
            try:
                self.dida_tasks = get_dida_tasks(mode="all")
                print(f"从滴答清单API获取到 {len(self.dida_tasks)} 个任务")
            except Exception as e:
                print(f"从滴答清单API获取任务失败: {str(e)}")
                self.dida_tasks = [] # API失败则返回空列表
                    
        return self.dida_tasks

    def _get_projects_from_api(self, force_refresh=False):
        """从滴答清单API获取项目数据"""
        if self.projects is None or force_refresh:
            if get_projects_logic:
                try:
                    self.projects = get_projects_logic()
                    print(f"从滴答清单API获取到 {len(self.projects)} 个项目")
                except Exception as e:
                    print(f"从滴答清单API获取项目失败: {str(e)}")
                    self.projects = []
            else:
                print("无法获取项目数据，get_projects_logic 不可用")
                self.projects = []
        return self.projects

    def _map_project_to_goal(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """将项目数据映射到目标数据结构"""
        # 定义映射规则 (需要根据实际项目结构调整)
        # 假设：项目名包含 "[目标]" 或 "[Goal]"
        # 假设：项目进度用某种方式存储在项目数据中，或通过关联任务计算
        # 假设：目标类型需要根据项目名或其他特征判断
        
        # 示例映射 (非常简化)
        goal_data = {
            "id": project.get('id'),
            "title": project.get('name', '未知目标'),
            "description": project.get('description', ''), # 可能需要从项目描述或关联任务获取
            "type": "project_based", # 或根据项目名/标签判断
            "status": 'active' if not project.get('isArchived') else 'archived', # 简化状态
            "progress": project.get('progress', 0), # 需要定义如何计算项目进度
            "keywords": project.get('name', '').split(), # 简化关键词提取
            "created_time": project.get('createdTime', ''),
            "modified_time": project.get('modifiedTime', ''),
            "start_date": project.get('startDate', ''), # 需要项目有开始日期
            "due_date": project.get('dueDate', '')    # 需要项目有截止日期
        }
        # 移除None值
        return {k: v for k, v in goal_data.items() if v is not None}

    def _get_all_goals(self, force_refresh=False) -> List[Dict[str, Any]]:
        """
        获取所有目标数据。
        优先从项目中查找带特定关键词的项目，如果找不到则从CSV读取。
        """
        if self.all_goals is None or force_refresh:
            goal_projects = []
            if get_projects_logic:
                projects = self._get_projects_from_api(force_refresh=force_refresh)
                goal_keywords = ["目标", "Goal", "[目标]", "[Goal]"]
                for proj in projects:
                    name = proj.get('name', '')
                    if any(keyword in name for keyword in goal_keywords):
                         goal_projects.append(self._map_project_to_goal(proj))
                
                if goal_projects:
                    print(f"发现 {len(goal_projects)} 个目标项目，将使用项目数据作为目标源。")
                    self.all_goals = goal_projects
                else:
                    print("未发现目标项目，将从 goals.csv 读取目标数据。")
                    self.all_goals = self.goals_handler.read_data()
            else:
                 print("无法检查项目，将从 goals.csv 读取目标数据。")
                 self.all_goals = self.goals_handler.read_data()
                 
        return self.all_goals
    
    def get_goal_statistics(self, force_refresh=False) -> Dict[str, Any]:
        """
        获取目标统计信息
        (优先使用项目作为目标源，否则使用CSV)
        """
        goals = self._get_all_goals(force_refresh=force_refresh)
        
        if not goals:
            return {
                "total": 0,
                "by_type": {},
                "by_status": {},
                "completion_rate": 0,
                "avg_progress": 0
            }
        
        # 统计总数
        total = len(goals)
        
        # 按类型统计
        by_type = {}
        for goal in goals:
            goal_type = goal.get('type', 'unknown')
            by_type[goal_type] = by_type.get(goal_type, 0) + 1
        
        # 按状态统计
        by_status = {}
        for goal in goals:
            status = goal.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        # 计算完成率 (需要定义项目/CSV目标的完成状态)
        completed = by_status.get('completed', by_status.get('archived', 0)) # 假设 archived 算完成
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        # 计算平均进度
        progress_values = [int(goal.get('progress', 0)) for goal in goals]
        avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
        
        return {
            "total": total,
            "by_type": by_type,
            "by_status": by_status,
            "completion_rate": round(completion_rate, 2),
            "avg_progress": round(avg_progress, 2)
        }
    
    def get_goal_progress_over_time(self, goal_id: str) -> List[Dict[str, Any]]:
        """
        获取目标进度随时间的变化
        (目前仅支持从CSV及其备份获取历史进度)
        """
        # TODO: 未来可以考虑如何从项目历史记录中获取进度
        print("警告：获取目标进度历史目前仅支持CSV源。")
        
        progress_data = []
        
        # 检查当前目标 (从缓存的 all_goals 或 CSV 读取)
        current_goals = self._get_all_goals() # 使用缓存或读取
        current_goal = next((g for g in current_goals if g.get('id') == goal_id), None)
        
        if current_goal:
             # 如果目标源是CSV，尝试从CSV获取历史
             if not get_projects_logic or not any(p['id'] == goal_id for p in self.projects if self.projects):
                 # 添加最新的进度数据
                 progress_data.append({
                     "date": current_goal.get('modified_time', ''),
                     "progress": int(current_goal.get('progress', 0))
                 })
                 
                 # 从备份文件中提取历史数据 (仅对CSV源有效)
                 backup_dir = os.path.join(os.path.dirname(self.goals_csv_path), 'backups')
                 if os.path.exists(backup_dir):
                     backup_files = sorted([f for f in os.listdir(backup_dir) if f.startswith('goals_')])
                     for backup_file in backup_files:
                         file_path = os.path.join(backup_dir, backup_file)
                         timestamp = backup_file.split('_')[1].split('.')[0]
                         try:
                             backup_handler = CSVHandler(file_path)
                             backup_goals = backup_handler.read_data()
                             backup_goal = next((g for g in backup_goals if g.get('id') == goal_id), None)
                             
                             if backup_goal:
                                 date_str = backup_goal.get('modified_time', timestamp)
                                 progress = int(backup_goal.get('progress', 0))
                                 if not any(d['date'] == date_str for d in progress_data):
                                     progress_data.append({"date": date_str, "progress": progress})
                         except Exception:
                             continue
             else:
                 print(f"目标 {goal_id} 是项目源，暂不支持历史进度查询。")
        
        # 按日期排序
        progress_data.sort(key=lambda x: x['date'])
        return progress_data
    
    def get_task_statistics(self, days: int = 30, force_refresh=False) -> Dict[str, Any]:
        """
        获取任务统计信息
        (使用API获取任务数据)
        """
        tasks = self._get_tasks_from_api(force_refresh=force_refresh)
        
        if not tasks:
            # ... [返回空统计数据，代码不变] ...
            return {
                "total": 0,
                "completed": 0,
                "completion_rate": 0,
                "avg_completion_time": 0,
                "by_day": {}
            }

        # ... [统计计算逻辑不变] ...
        # 计算日期范围
        today = date.today()
        start_date = today - timedelta(days=days-1)
        
        # 筛选日期范围内的任务
        filtered_tasks = []
        for task in tasks:
            task_date_str = task.get('createdTime', task.get('created', task.get('createTime', '')))
            if not task_date_str:
                continue
                
            try:
                task_date = parse_date(task_date_str.split(' ')[0])
                if task_date and task_date >= start_date:
                    filtered_tasks.append(task)
            except:
                continue
        
        # 统计总数
        total = len(filtered_tasks)
        
        # 统计完成任务
        completed = sum(1 for task in filtered_tasks if task.get('status') == 2 or 
                        task.get('isCompleted') == True or 
                        str(task.get('completed')).lower() == 'true')
        
        # 计算完成率
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        # 计算平均完成时间
        completion_times = []
        for task in filtered_tasks:
            created_str = task.get('createdTime', task.get('created', task.get('createTime', '')))
            completed_str = task.get('completedTime', '')
            
            is_completed = (task.get('status') == 2 or 
                           task.get('isCompleted') == True or 
                           str(task.get('completed')).lower() == 'true')
            
            if created_str and completed_str and is_completed:
                try:
                    created_date = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
                    completed_date = datetime.strptime(completed_str, "%Y-%m-%d %H:%M:%S")
                    diff = (completed_date - created_date).total_seconds() / 3600  # 小时
                    completion_times.append(diff)
                except:
                    continue
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # 按天统计
        by_day = {}
        for i in range(days):
            curr_date = start_date + timedelta(days=i)
            date_str = format_date(curr_date)
            by_day[date_str] = {
                "total": 0,
                "completed": 0
            }
        
        for task in filtered_tasks:
            task_date_str = task.get('createdTime', task.get('created', task.get('createTime', '')))
            if not task_date_str:
                continue
                
            try:
                task_date = parse_date(task_date_str.split(' ')[0])
                date_str = format_date(task_date)
                
                if date_str in by_day:
                    by_day[date_str]["total"] += 1
                    
                    is_completed = (task.get('status') == 2 or 
                                  task.get('isCompleted') == True or 
                                  str(task.get('completed')).lower() == 'true')
                    
                    if is_completed:
                        by_day[date_str]["completed"] += 1
            except:
                continue
                
        return {
            "total": total,
            "completed": completed,
            "completion_rate": round(completion_rate, 2),
            "avg_completion_time": round(avg_completion_time, 2),
            "by_day": by_day
        }
    
    def extract_task_keywords(self, limit: int = 20, force_refresh=False) -> Dict[str, int]:
        """
        从任务中提取关键词
        (使用API获取任务数据)
        """
        tasks = self._get_tasks_from_api(force_refresh=force_refresh)
        
        if not tasks:
             # ... [返回空字典，代码不变] ...
            return {}

        # ... [关键词提取逻辑不变] ...
        # 合并所有任务文本
        all_text = ""
        for task in tasks:
            title = task.get('title', task.get('content', ''))
            content = task.get('content', task.get('note', ''))
            all_text += f"{title} {content} "
        
        # 分词
        words = segment_text(all_text)
        
        # 计算词频
        word_counts = Counter(words)
        
        # 返回前N个高频词
        return dict(word_counts.most_common(limit))
    
    def get_goal_completion_prediction(self, goal_id: str, force_refresh=False) -> Dict[str, Any]:
        """
        预测目标完成情况
        (优先使用项目作为目标源，否则使用CSV)
        (目前仅对CSV中的阶段性目标或有日期的项目目标进行预测)
        """
        goals = self._get_all_goals(force_refresh=force_refresh)
        goal = next((g for g in goals if g.get('id') == goal_id), None)
        
        if not goal:
            # ... [返回 not_found，代码不变] ...
             return {
                "status": "not_found",
                "message": "目标不存在"
            }

        # 获取目标类型 (可能是 project_based 或 CSV 中的类型)
        goal_type = goal.get('type', '')
        is_project_based = goal_type == 'project_based'

        # 获取目标开始和截止日期
        start_date_str = goal.get('start_date', '')
        due_date_str = goal.get('due_date', '')

        # 只有当目标是阶段性目标(CSV) 或者 是项目且有起止日期时才进行预测
        can_predict = (goal_type == 'phase' and not is_project_based) or \
                      (is_project_based and start_date_str and due_date_str)

        if not can_predict:
             # ... [返回 not_applicable 或 missing_dates，代码不变] ...
            if not start_date_str or not due_date_str:
                 return {
                    "status": "missing_dates",
                    "message": "目标缺少开始日期或截止日期，无法预测"
                }
            else:
                return {
                    "status": "not_applicable",
                    "message": f"目标类型 '{goal_type}' 不支持预测，或缺少必要日期信息"
                }

        # ... [日期解析和预测逻辑不变] ...
        start_date = parse_date(start_date_str)
        due_date = parse_date(due_date_str)
        today = date.today()
        
        if not start_date or not due_date:
            return {
                "status": "invalid_dates",
                "message": "目标日期格式无效"
            }
            
        # 计算总天数
        total_days = date_diff_days(due_date, start_date)
        if total_days < 0: total_days = 0 # 处理日期反转的情况

        # 计算已过天数
        elapsed_days = date_diff_days(today, start_date)
        if elapsed_days < 0: elapsed_days = 0 # 如果今天还没到开始日期

        # 计算剩余天数
        remaining_days = date_diff_days(due_date, today)
        if remaining_days < 0: remaining_days = 0 # 如果已经逾期

        # 获取当前进度
        current_progress = int(goal.get('progress', 0))

        # 检查目标是否已经截止
        if today > due_date:
            status = "overdue"
            completion_date = None
            message = "目标已逾期"
            expected_progress = 100
        else:
            # 计算理想进度
            if total_days > 0:
                expected_progress = min(100, round((elapsed_days / total_days) * 100))
            else: # 如果总天数为0或负数（开始=截止或开始>截止）
                 expected_progress = 100 if elapsed_days >= 0 else 0 # 开始当天或之后，期望100%
            
            # 计算进度差
            progress_diff = current_progress - expected_progress
            
            # 计算预计完成日期
            completion_date = None
            if current_progress > 0 and current_progress < 100:
                if elapsed_days > 0:
                    # 根据当前进度估算每天进度
                    daily_progress = current_progress / elapsed_days
                    # 预估剩余天数
                    if daily_progress > 0:
                        remaining_progress = 100 - current_progress
                        estimated_remaining_days = remaining_progress / daily_progress
                        # 确保预测日期不早于今天
                        predicted_completion_date = today + timedelta(days=round(estimated_remaining_days))
                        completion_date = max(predicted_completion_date, today) 
                    # else: daily_progress is 0, cannot predict completion date
                # else: elapsed_days is 0, cannot calculate daily progress yet
            elif current_progress >= 100:
                 completion_date = today # Already completed or over 100%

            # 确定状态
            if progress_diff >= 10:
                status = "ahead"
                message = "进度超前"
            elif progress_diff <= -20:
                status = "behind"
                message = "进度滞后"
            else:
                status = "on_track"
                message = "进度正常"
        
        return {
            "status": status,
            "message": message,
            "current_progress": current_progress,
            "expected_progress": expected_progress,
            "total_days": total_days,
            "elapsed_days": elapsed_days,
            "remaining_days": remaining_days,
            "completion_date": format_date(completion_date) if completion_date else None
        }
    
    def generate_goal_report(self, goal_id: str, force_refresh=False) -> Dict[str, Any]:
        """
        生成目标报告
        (优先使用项目作为目标源，否则使用CSV)
        """
        goals = self._get_all_goals(force_refresh=force_refresh)
        goal = next((g for g in goals if g.get('id') == goal_id), None)
        
        if not goal:
             # ... [返回 error，代码不变] ...
            return {
                "status": "error",
                "message": "目标不存在"
            }
            
        # 获取目标基本信息 (已包含在 goal 字典中)
        goal_info = goal 
        
        # 获取目标进度历史 (目前仅CSV)
        progress_history = self.get_goal_progress_over_time(goal_id)
        
        # 获取目标完成预测
        completion_prediction = self.get_goal_completion_prediction(goal_id, force_refresh=False) # 使用缓存数据
        
        # --- 收集相关任务信息 ---
        related_tasks = []
        tasks = self._get_tasks_from_api(force_refresh=force_refresh) # 获取最新任务
        
        # 确定关联逻辑：
        # 1. 如果目标是项目，则关联该项目下的所有任务
        # 2. 如果目标是CSV，则关联标题/内容中包含目标关键词的任务
        
        is_project_based = goal.get('type') == 'project_based'
        
        if is_project_based:
             # 关联项目下的任务
             project_id = goal.get('id')
             for task in tasks:
                 if task.get('projectId') == project_id:
                     related_tasks.append({
                         "id": task.get('id', ''),
                         "title": task.get('title', ''),
                         "status": task.get('status'),
                         "isCompleted": task.get('isCompleted'),
                         "createdTime": task.get('createdTime', '')
                     })
        else:
             # 关联包含关键词的任务 (来自CSV的目标)
             goal_keywords = normalize_keywords(goal.get('keywords', goal.get('title',''))) # 使用目标标题作为关键词
             goal_keywords_set = set(k for k in goal_keywords.split() if len(k) > 1) # 简单过滤

             if goal_keywords_set:
                 for task in tasks:
                     title = task.get('title', '')
                     content = task.get('content', '')
                     task_text = f"{title} {content}".lower()
                     
                     # 检查任务文本是否包含任何目标关键词
                     if any(keyword.lower() in task_text for keyword in goal_keywords_set):
                         related_tasks.append({
                             "id": task.get('id', ''),
                             "title": title,
                             "status": task.get('status'),
                             "isCompleted": task.get('isCompleted'),
                             "createdTime": task.get('createdTime', '')
                         })
        
        return {
            "status": "success",
            "goal": goal_info,
            "progress_history": progress_history,
            "prediction": completion_prediction,
            "related_tasks": related_tasks[:50] # 限制返回的任务数量
        }
    
    def generate_weekly_summary(self, force_refresh=False) -> Dict[str, Any]:
        """
        生成每周总结
        (合并项目目标和CSV目标的数据)
        """
        # 获取本周日期范围
        start_date, end_date = get_date_range('week')
        
        # --- 目标完成情况 ---
        all_goals = self._get_all_goals(force_refresh=force_refresh)
        
        # 筛选本周更新的目标
        weekly_goals_updated = []
        for goal in all_goals:
            modified_str = goal.get('modified_time', '')
            if modified_str:
                try:
                    modified_date = parse_date(modified_str.split(' ')[0])
                    if modified_date and start_date <= modified_date <= end_date:
                        weekly_goals_updated.append(goal)
                except:
                    continue
        
        # 统计目标完成情况
        completed_goals = sum(1 for g in weekly_goals_updated if g.get('status') == 'completed' or g.get('status') == 'archived')
        active_goals = sum(1 for g in weekly_goals_updated if g.get('status') == 'active')
        
        # 平均目标进度
        progress_values = [int(g.get('progress', 0)) for g in weekly_goals_updated]
        avg_progress = sum(progress_values) / len(weekly_goals_updated) if weekly_goals_updated else 0
        
        # --- 任务完成情况 ---
        tasks = self._get_tasks_from_api(force_refresh=force_refresh)
        tasks_stats = {}
        
        # 筛选本周创建的任务
        weekly_tasks_created = []
        for task in tasks:
            created_str = task.get('createdTime', task.get('created', task.get('createTime', '')))
            if created_str:
                try:
                    created_date = parse_date(created_str.split(' ')[0])
                    if created_date and start_date <= created_date <= end_date:
                        weekly_tasks_created.append(task)
                except:
                    continue
        
        # 统计任务完成情况
        completed_tasks = sum(1 for t in weekly_tasks_created if t.get('status') == 2 or t.get('isCompleted') == True)
        total_tasks = len(weekly_tasks_created)
        
        tasks_stats = {
            "total": total_tasks,
            "completed": completed_tasks,
            "completion_rate": round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0
        }
        
        return {
            "period": {
                "start_date": format_date(start_date),
                "end_date": format_date(end_date)
            },
            "goals": {
                "total_updated": len(weekly_goals_updated), # 改为显示本周更新的目标数
                "completed": completed_goals,
                "active": active_goals,
                "avg_progress": round(avg_progress, 2)
            },
            "tasks": tasks_stats # 显示本周创建的任务统计
        }


# --- MCP 工具注册 ---
# (注册函数保持不变，它们调用的是AnalyticsManager的方法)
def register_analytics_tools(server: FastMCP, auth_info: Dict[str, Any]):
    """
    注册数据分析工具到MCP服务器
    
    Args:
        server: MCP服务器实例
        auth_info: 认证信息
    """
    # 确保在 AnalyticsManager 实例化时传递必要的 auth_info 或 API 客户端
    # (当前 AnalyticsManager 内部直接调用导入的 _logic 函数，这些函数依赖 base_api 初始化)
    # 这里我们假设 base_api 已经在 task_tools 或 project_tools 注册时被初始化了
    
    # 创建 AnalyticsManager 实例
    # 可以考虑传递 auth_info 或 api_client 进去，如果 Manager 需要直接调用 API
    analytics_manager = AnalyticsManager() 
    
    @server.tool()
    def get_goal_statistics(force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取目标统计信息 (优先项目，后CSV)
        Args:
            force_refresh: 是否强制刷新缓存数据 (默认为 False)
        Returns: 目标统计数据
        """
        try:
            # 调用 manager 的方法
            return analytics_manager.get_goal_statistics(force_refresh=force_refresh)
        except Exception as e:
            raise ValueError(f"获取目标统计信息失败: {str(e)}")
    
    @server.tool()
    def get_goal_progress(goal_id: str) -> List[Dict[str, Any]]:
        """
        获取目标进度历史 (目前仅支持CSV源)
        Args: goal_id: 目标ID
        Returns: 目标进度历史数据
        """
        try:
             # 调用 manager 的方法
            return analytics_manager.get_goal_progress_over_time(goal_id)
        except Exception as e:
            raise ValueError(f"获取目标进度历史失败: {str(e)}")
    
    @server.tool()
    def get_task_statistics(days: int = 30, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取任务统计信息 (来自API)
        Args: 
            days: 统计的天数范围 (默认30)
            force_refresh: 是否强制刷新缓存数据 (默认为 False)
        Returns: 任务统计数据
        """
        try:
             # 调用 manager 的方法
            return analytics_manager.get_task_statistics(days=days, force_refresh=force_refresh)
        except Exception as e:
            raise ValueError(f"获取任务统计信息失败: {str(e)}")
    
    @server.tool()
    def extract_task_keywords(limit: int = 20, force_refresh: bool = False) -> Dict[str, int]:
        """
        从任务中提取关键词 (来自API)
        Args: 
            limit: 返回的关键词数量 (默认20)
            force_refresh: 是否强制刷新缓存数据 (默认为 False)
        Returns: 关键词频率字典
        """
        try:
             # 调用 manager 的方法
            return analytics_manager.extract_task_keywords(limit=limit, force_refresh=force_refresh)
        except Exception as e:
            raise ValueError(f"提取任务关键词失败: {str(e)}")
    
    @server.tool()
    def predict_goal_completion(goal_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        预测目标完成情况 (优先项目，后CSV；目前仅支持带日期的目标)
        Args: 
            goal_id: 目标ID
            force_refresh: 是否强制刷新缓存数据 (默认为 False)
        Returns: 预测数据
        """
        try:
             # 调用 manager 的方法
            return analytics_manager.get_goal_completion_prediction(goal_id=goal_id, force_refresh=force_refresh)
        except Exception as e:
            raise ValueError(f"预测目标完成情况失败: {str(e)}")
    
    @server.tool()
    def generate_goal_report(goal_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        生成目标报告 (优先项目，后CSV)
        Args: 
            goal_id: 目标ID
            force_refresh: 是否强制刷新缓存数据 (默认为 False)
        Returns: 目标报告数据
        """
        try:
             # 调用 manager 的方法
            return analytics_manager.generate_goal_report(goal_id=goal_id, force_refresh=force_refresh)
        except Exception as e:
            raise ValueError(f"生成目标报告失败: {str(e)}")
    
    @server.tool()
    def generate_weekly_summary(force_refresh: bool = False) -> Dict[str, Any]:
        """
        生成每周总结 (合并项目目标和CSV目标)
        Args: 
            force_refresh: 是否强制刷新缓存数据 (默认为 False)
        Returns: 每周总结数据
        """
        try:
             # 调用 manager 的方法
            return analytics_manager.generate_weekly_summary(force_refresh=force_refresh)
        except Exception as e:
            raise ValueError(f"生成每周总结失败: {str(e)}")
