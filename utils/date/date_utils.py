"""
日期处理工具
提供日期计算、格式化和频率解析功能
"""

import re
import calendar
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, timedelta, date


def get_current_time() -> datetime:
    """
    获取当前时间
    
    Returns:
        当前时间的datetime对象
    """
    return datetime.now()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 要格式化的datetime对象
        format_str: 格式化字符串
        
    Returns:
        格式化后的字符串
    """
    return dt.strftime(format_str)


def format_date(dt: Union[datetime, date], format_str: str = "%Y-%m-%d") -> str:
    """
    格式化日期
    
    Args:
        dt: 要格式化的datetime或date对象
        format_str: 格式化字符串
        
    Returns:
        格式化后的字符串
    """
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串
        format_str: 格式化字符串
        
    Returns:
        解析后的datetime对象，如果解析失败则返回None
    """
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None


def parse_date(date_str: str) -> Optional[date]:
    """
    解析日期字符串，支持多种格式
    
    Args:
        date_str: 日期字符串
        
    Returns:
        解析后的date对象，如果解析失败则返回None
    """
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%m.%d.%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    
    return None


def is_valid_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> bool:
    """
    检查日期时间字符串是否有效
    
    Args:
        date_str: 日期时间字符串
        format_str: 格式化字符串
        
    Returns:
        是否有效
    """
    return parse_datetime(date_str, format_str) is not None


def is_valid_date(date_str: str) -> bool:
    """
    检查日期字符串是否有效
    
    Args:
        date_str: 日期字符串
        
    Returns:
        是否有效
    """
    return parse_date(date_str) is not None


def get_today() -> date:
    """
    获取今天的日期
    
    Returns:
        今天的日期对象
    """
    return date.today()


def get_tomorrow() -> date:
    """
    获取明天的日期
    
    Returns:
        明天的日期对象
    """
    return date.today() + timedelta(days=1)


def get_yesterday() -> date:
    """
    获取昨天的日期
    
    Returns:
        昨天的日期对象
    """
    return date.today() - timedelta(days=1)


def get_date_range(period: str, reference_date: Optional[date] = None) -> Tuple[date, date]:
    """
    获取指定时间段的开始和结束日期
    
    Args:
        period: 时间段类型，支持 'day', 'week', 'month', 'year'
        reference_date: 参考日期，如果未提供则使用今天
        
    Returns:
        (开始日期, 结束日期) 的元组
    """
    if reference_date is None:
        reference_date = get_today()
    
    if period == 'day':
        return reference_date, reference_date
    
    elif period == 'week':
        # 获取当前周的周一和周日
        weekday = reference_date.weekday()
        week_start = reference_date - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    elif period == 'month':
        # 获取当前月的第一天和最后一天
        month_start = date(reference_date.year, reference_date.month, 1)
        days_in_month = calendar.monthrange(reference_date.year, reference_date.month)[1]
        month_end = date(reference_date.year, reference_date.month, days_in_month)
        return month_start, month_end
    
    elif period == 'year':
        # 获取当前年的第一天和最后一天
        year_start = date(reference_date.year, 1, 1)
        year_end = date(reference_date.year, 12, 31)
        return year_start, year_end
    
    else:
        raise ValueError(f"不支持的时间段类型: {period}")


def date_diff_days(date1: date, date2: date) -> int:
    """
    计算两个日期之间相差的天数
    
    Args:
        date1: 日期1
        date2: 日期2
        
    Returns:
        date1 - date2 的天数差
    """
    return (date1 - date2).days


def is_date_in_range(check_date: date, start_date: date, end_date: date) -> bool:
    """
    检查日期是否在指定范围内
    
    Args:
        check_date: 要检查的日期
        start_date: 范围开始日期
        end_date: 范围结束日期
        
    Returns:
        日期是否在范围内
    """
    return start_date <= check_date <= end_date


def is_datetime_in_range(check_datetime: datetime, start_datetime: datetime, end_datetime: datetime) -> bool:
    """
    检查日期时间是否在指定范围内
    
    Args:
        check_datetime: 要检查的日期时间
        start_datetime: 范围开始日期时间
        end_datetime: 范围结束日期时间
        
    Returns:
        日期时间是否在范围内
    """
    return start_datetime <= check_datetime <= end_datetime


def parse_frequency(frequency: str) -> Dict[str, Union[str, List[int]]]:
    """
    解析频率字符串
    
    Args:
        frequency: 频率字符串，例如 'daily', 'weekly:1,3,5', 'monthly:1,15'
        
    Returns:
        包含频率类型和具体日期的字典
        例如 {'type': 'weekly', 'days': [1, 3, 5]}
    """
    if not frequency:
        return {'type': None, 'days': []}
    
    # 处理daily
    if frequency.lower() == 'daily':
        return {'type': 'daily', 'days': list(range(7))}
    
    # 处理weekly或monthly
    match = re.match(r'(weekly|monthly):(.+)', frequency.lower())
    if match:
        freq_type = match.group(1)
        days_str = match.group(2)
        
        try:
            # 解析天数为整数列表
            days = [int(day.strip()) for day in days_str.split(',')]
            
            # 验证天数是否有效
            if freq_type == 'weekly' and not all(1 <= day <= 7 for day in days):
                raise ValueError("周几必须在 1-7 范围内")
            elif freq_type == 'monthly' and not all(1 <= day <= 31 for day in days):
                raise ValueError("日期必须在 1-31 范围内")
                
            return {'type': freq_type, 'days': days}
        except ValueError:
            raise ValueError(f"无效的频率格式: {frequency}")
    
    raise ValueError(f"无效的频率格式: {frequency}")


def matches_frequency(check_date: date, frequency: str) -> bool:
    """
    检查日期是否匹配指定频率
    
    Args:
        check_date: 要检查的日期
        frequency: 频率字符串，例如 'daily', 'weekly:1,3,5', 'monthly:1,15'
        
    Returns:
        日期是否匹配频率
    """
    if not frequency:
        return False
    
    try:
        freq_info = parse_frequency(frequency)
    except ValueError:
        return False
    
    freq_type = freq_info['type']
    days = freq_info['days']
    
    if freq_type == 'daily':
        return True
    
    elif freq_type == 'weekly':
        # 周一是1，周日是7
        # 但datetime的weekday()返回0-6，其中周一是0，周日是6
        weekday = check_date.isoweekday()  # 使用isoweekday获取1-7的值
        return weekday in days
    
    elif freq_type == 'monthly':
        return check_date.day in days
    
    return False


def get_next_occurrence(reference_date: date, frequency: str) -> Optional[date]:
    """
    计算给定频率下的下一次出现日期
    
    Args:
        reference_date: 参考日期
        frequency: 频率字符串，例如 'daily', 'weekly:1,3,5', 'monthly:1,15'
        
    Returns:
        下一次出现的日期，如果频率无效则返回None
    """
    try:
        freq_info = parse_frequency(frequency)
    except ValueError:
        return None
    
    freq_type = freq_info['type']
    days = freq_info['days']
    
    if not days:
        return None
    
    if freq_type == 'daily':
        return reference_date + timedelta(days=1)
    
    elif freq_type == 'weekly':
        # 计算下一个匹配的周几
        current_weekday = reference_date.isoweekday()  # 1-7
        
        # 找出下一个大于当前周几的日期
        next_weekdays = [day for day in days if day > current_weekday]
        
        if next_weekdays:
            # 本周内有下一次
            days_ahead = next_weekdays[0] - current_weekday
        else:
            # 下周才有下一次
            days_ahead = 7 - current_weekday + days[0]
        
        return reference_date + timedelta(days=days_ahead)
    
    elif freq_type == 'monthly':
        # 计算本月或下月的下一个匹配日期
        current_day = reference_date.day
        
        # 找出本月内大于当前日期的天
        next_days = [day for day in days if day > current_day]
        
        if next_days:
            # 本月内有下一次
            target_day = next_days[0]
            # 确保日期有效（考虑月底）
            max_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
            target_day = min(target_day, max_day)
            
            return date(reference_date.year, reference_date.month, target_day)
        else:
            # 下月才有下一次
            # 计算下个月的年和月
            if reference_date.month == 12:
                next_year = reference_date.year + 1
                next_month = 1
            else:
                next_year = reference_date.year
                next_month = reference_date.month + 1
            
            # 确保日期有效（考虑月底）
            target_day = days[0]
            max_day = calendar.monthrange(next_year, next_month)[1]
            target_day = min(target_day, max_day)
            
            return date(next_year, next_month, target_day)
    
    return None
