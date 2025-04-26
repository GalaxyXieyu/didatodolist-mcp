"""
CSV文件处理工具
提供CSV文件的读取、写入、验证和备份功能
"""

import os
import csv
import uuid
import json
import shutil
import datetime
from typing import List, Dict, Any, Optional, Callable


class CSVHandler:
    """
    CSV文件处理类，提供读写、验证和备份功能
    """
    
    def __init__(self, file_path: str, backup_dir: str = None, required_fields: List[str] = None):
        """
        初始化CSV处理器
        
        Args:
            file_path: CSV文件路径
            backup_dir: 备份目录路径，默认为文件所在目录下的backups文件夹
            required_fields: 必填字段列表
        """
        self.file_path = file_path
        self.required_fields = required_fields or []
        
        # 设置备份目录
        if backup_dir is None:
            file_dir = os.path.dirname(os.path.abspath(file_path))
            self.backup_dir = os.path.join(file_dir, 'backups')
        else:
            self.backup_dir = backup_dir
            
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 确保文件目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
    def file_exists(self) -> bool:
        """
        检查CSV文件是否存在
        
        Returns:
            文件是否存在
        """
        return os.path.exists(self.file_path)
        
    def create_file(self, headers: List[str]) -> None:
        """
        创建CSV文件并写入表头
        
        Args:
            headers: 表头字段列表
        """
        # 确保所有必填字段都在表头中
        for field in self.required_fields:
            if field not in headers:
                raise ValueError(f"必填字段 '{field}' 不在表头中")
                
        # 创建CSV文件并写入表头
        with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
    def read_data(self) -> List[Dict[str, Any]]:
        """
        读取CSV文件数据
        
        Returns:
            字典列表，每个字典代表一行数据
        """
        if not self.file_exists():
            return []
            
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 处理可能的空字符串
                processed_row = {}
                for key, value in row.items():
                    if value == '':
                        processed_row[key] = None
                    else:
                        # 尝试解析JSON字段
                        if key in ['metrics'] and value:
                            try:
                                processed_row[key] = json.loads(value)
                            except json.JSONDecodeError:
                                processed_row[key] = value
                        else:
                            processed_row[key] = value
                data.append(processed_row)
        return data
        
    def write_data(self, data: List[Dict[str, Any]], validate: bool = True) -> None:
        """
        写入数据到CSV文件
        
        Args:
            data: 要写入的数据，字典列表
            validate: 是否验证数据
        """
        if validate:
            self._validate_data(data)
            
        # 在写入前创建备份
        self._create_backup()
        
        # 准备写入，如果文件不存在则创建
        if not data:
            return
            
        # 获取所有字段（表头）
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
        
        # 确保必填字段在表头中
        for field in self.required_fields:
            if field not in all_fields:
                raise ValueError(f"必填字段 '{field}' 缺失")
                
        headers = list(all_fields)
        
        # 写入数据
        with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for row in data:
                # 处理特殊字段
                processed_row = {}
                for key, value in row.items():
                    if value is None:
                        processed_row[key] = ''
                    elif key in ['metrics'] and isinstance(value, (dict, list)):
                        processed_row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        processed_row[key] = value
                writer.writerow(processed_row)
                
    def _validate_data(self, data: List[Dict[str, Any]]) -> None:
        """
        验证数据是否符合要求
        
        Args:
            data: 要验证的数据
        
        Raises:
            ValueError: 当数据验证失败时
        """
        for i, item in enumerate(data):
            # 检查必填字段
            for field in self.required_fields:
                if field not in item:
                    raise ValueError(f"第 {i+1} 行数据缺少必填字段 '{field}'")
                if item[field] is None or item[field] == '':
                    raise ValueError(f"第 {i+1} 行数据的必填字段 '{field}' 为空")
        
    def _create_backup(self) -> None:
        """
        创建CSV文件的备份
        """
        if not self.file_exists():
            return
            
        # 创建带时间戳的备份文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(self.file_path)
        name, ext = os.path.splitext(filename)
        backup_filename = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # 复制文件
        shutil.copy2(self.file_path, backup_path)
        
    def validate_file(self) -> bool:
        """
        验证CSV文件格式和数据是否正确
        
        Returns:
            验证是否通过
        """
        if not self.file_exists():
            return False
            
        try:
            data = self.read_data()
            self._validate_data(data)
            return True
        except Exception:
            return False
    
    def append_row(self, row: Dict[str, Any], validate: bool = True) -> None:
        """
        追加一行数据到CSV文件
        
        Args:
            row: 要追加的数据行
            validate: 是否验证数据
        """
        data = self.read_data()
        data.append(row)
        self.write_data(data, validate=validate)
    
    def update_row(self, key_field: str, key_value: str, 
                  new_data: Dict[str, Any], validate: bool = True) -> bool:
        """
        更新CSV文件中的一行数据
        
        Args:
            key_field: 用于识别行的键字段名
            key_value: 要更新的行的键字段值
            new_data: 新的数据，将合并到现有数据
            validate: 是否验证数据
            
        Returns:
            是否成功更新了数据
        """
        data = self.read_data()
        updated = False
        
        for i, row in enumerate(data):
            if row.get(key_field) == key_value:
                data[i] = {**row, **new_data}
                updated = True
                break
                
        if updated:
            self.write_data(data, validate=validate)
            
        return updated
    
    def delete_row(self, key_field: str, key_value: str, validate: bool = True) -> bool:
        """
        删除CSV文件中的一行数据
        
        Args:
            key_field: 用于识别行的键字段名
            key_value: 要删除的行的键字段值
            validate: 是否验证数据
            
        Returns:
            是否成功删除了数据
        """
        data = self.read_data()
        original_len = len(data)
        
        data = [row for row in data if row.get(key_field) != key_value]
        
        if len(data) < original_len:
            self.write_data(data, validate=validate)
            return True
        else:
            return False
    
    def find_rows(self, filter_func: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """
        使用过滤函数查找满足条件的行
        
        Args:
            filter_func: 过滤函数，接收一个字典作为参数，返回布尔值
            
        Returns:
            满足条件的行列表
        """
        data = self.read_data()
        return [row for row in data if filter_func(row)]
    
    def get_row(self, key_field: str, key_value: str) -> Optional[Dict[str, Any]]:
        """
        获取指定键值的行
        
        Args:
            key_field: 键字段名
            key_value: 键字段值
            
        Returns:
            找到的行数据，未找到则返回None
        """
        data = self.read_data()
        for row in data:
            if row.get(key_field) == key_value:
                return row
        return None


def create_default_goal_csv(file_path: str = 'data/goals.csv') -> None:
    """
    创建默认的目标CSV文件
    
    Args:
        file_path: CSV文件路径
    """
    required_fields = ['id', 'title', 'type', 'status', 'created_time', 
                      'modified_time', 'keywords', 'progress']
    
    headers = ['id', 'title', 'description', 'type', 'status', 
              'created_time', 'modified_time', 'start_date', 'due_date',
              'frequency', 'keywords', 'progress', 'related_projects', 'metrics']
    
    handler = CSVHandler(file_path, required_fields=required_fields)
    
    if not handler.file_exists():
        handler.create_file(headers)
        print(f"已创建默认目标CSV文件: {file_path}")
    else:
        print(f"目标CSV文件已存在: {file_path}")
