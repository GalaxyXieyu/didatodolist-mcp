"""
滴答清单认证工具函数
"""

import requests
import json
from pathlib import Path
from typing import Optional, Dict, Tuple

def get_ticktick_token(email: str, password: str) -> Optional[str]:
    """
    获取滴答清单的访问令牌
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        str: 访问令牌。如果登录失败返回None
        
    Raises:
        requests.exceptions.RequestException: 当网络请求失败时
        ValueError: 当账号密码错误时
    """
    login_url = "https://dida365.com/api/v2/user/signon?wc=true&remember=true"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    payload = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=payload, headers=headers)
        response.raise_for_status()  # 抛出非200响应的异常
        
        token = response.cookies.get("t")
        if not token:
            raise ValueError("登录成功但未获取到token")
        return token
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            raise ValueError("账号或密码错误")
        raise
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")

def save_token_to_config(token: str, config_path: str = "config.json") -> bool:
    """
    将token保存到配置文件
    
    Args:
        token: 访问令牌
        config_path: 配置文件路径
        
    Returns:
        bool: 保存成功返回True，否则返回False
    """
    try:
        # 读取现有配置(如果存在)
        config = {}
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    # 如果JSON无效，使用空配置
                    config = {}
        
        # 更新token
        config["token"] = token
        
        # 写回配置文件
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"保存token到配置文件失败: {str(e)}")
        return False

def get_auth_info_with_login(args_token: Optional[str] = None, 
                             args_email: Optional[str] = None, 
                             args_password: Optional[str] = None,
                             env_token: Optional[str] = None,
                             env_email: Optional[str] = None,
                             env_password: Optional[str] = None,
                             config_path: str = "config.json") -> Tuple[Dict[str, str], bool]:
    """
    获取认证信息，优先使用token，如果没有token但有邮箱密码，则尝试登录并保存token
    
    Args:
        args_token: 命令行参数中的token
        args_email: 命令行参数中的邮箱
        args_password: 命令行参数中的密码
        env_token: 环境变量中的token
        env_email: 环境变量中的邮箱
        env_password: 环境变量中的密码
        config_path: 配置文件路径
        
    Returns:
        Tuple[Dict[str, str], bool]: 包含auth_info和是否为新获取的token的标志
    """
    # 优先使用可用的token
    token = args_token or env_token
    
    # 读取配置文件
    config = {}
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    
    # 如果没有传入token，尝试使用配置文件中的token
    if not token and "token" in config:
        token = config["token"]
        
    # 如果有token，直接返回
    if token:
        return {"token": token}, False
    
    # 如果没有token但有邮箱密码，尝试登录
    email = args_email or env_email or config.get("email")
    password = args_password or env_password or config.get("password")
    
    if email and password:
        try:
            print(f"正在使用邮箱 {email} 登录滴答清单...")
            new_token = get_ticktick_token(email, password)
            if new_token:
                # 保存token到配置文件
                save_success = save_token_to_config(new_token, config_path)
                if save_success:
                    print("已成功获取token并保存到配置文件")
                else:
                    print("警告: token已获取但保存失败")
                
                # 同时保存邮箱密码，方便token过期后自动重新获取
                config["email"] = email
                config["password"] = password
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                
                return {"token": new_token}, True
        except Exception as e:
            print(f"使用邮箱密码登录失败: {str(e)}")
            # 登录失败，继续尝试使用邮箱密码认证
    
    # 如果登录失败或没有邮箱密码，返回原始认证信息
    if email and password:
        return {"email": email, "password": password}, False
    
    # 如果什么都没有，返回空字典
    return {}, False 