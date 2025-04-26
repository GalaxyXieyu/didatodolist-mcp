"""
初始化数据结构
创建必要的CSV文件和目录结构
"""

import os
import sys
import datetime
import csv
import uuid

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入工具模块
from utils.csv_handler import CSVHandler, create_default_goal_csv


def setup_directories():
    """
    创建必要的目录结构
    """
    directories = [
        'data',
        'data/backups'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")


def create_sample_goal():
    """
    创建示例目标数据
    """
    try:
        from tools.goal_tools import GoalManager
        
        goal_manager = GoalManager()
        
        # 检查是否已有目标数据
        existing_goals = goal_manager.get_goals()
        if existing_goals:
            print(f"已存在 {len(existing_goals)} 个目标，跳过创建示例目标")
            return
        
        # 创建示例目标
        try:
            # 阶段性目标示例
            phase_goal = goal_manager.create_goal(
                title="完成滴答清单MCP服务扩展功能",
                goal_type="phase",
                keywords="滴答清单,MCP,目标管理,统计分析",
                description="为滴答清单MCP服务添加目标管理和统计分析功能",
                start_date=datetime.date.today().strftime("%Y-%m-%d"),
                due_date=(datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                progress=0
            )
            print(f"创建示例阶段性目标: {phase_goal['title']}")
            
            # 习惯性目标示例
            habit_goal = goal_manager.create_goal(
                title="每周代码复查",
                goal_type="habit",
                keywords="代码,复查,质量",
                description="每周花时间复查代码，确保代码质量",
                frequency="weekly:1,5",  # 周一和周五
                progress=0
            )
            print(f"创建示例习惯性目标: {habit_goal['title']}")
            
            # 永久性目标示例
            permanent_goal = goal_manager.create_goal(
                title="保持代码库整洁",
                goal_type="permanent",
                keywords="代码,整洁,维护",
                description="持续保持代码库整洁，避免技术债务积累",
                progress=0
            )
            print(f"创建示例永久性目标: {permanent_goal['title']}")
            
        except Exception as e:
            print(f"创建示例目标失败: {str(e)}")
    except ImportError as e:
        print(f"导入GoalManager失败: {str(e)}")
        print("跳过创建示例目标")


def initialize_data():
    """
    初始化所有数据结构
    """
    print("开始初始化数据结构...")
    
    # 创建目录
    setup_directories()
    
    # 创建目标CSV文件
    create_default_goal_csv()
    
    # 创建示例目标
    create_sample_goal()
    
    print("数据结构初始化完成!")


if __name__ == "__main__":
    initialize_data() 