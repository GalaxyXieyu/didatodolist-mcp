"""
滴答清单认证工具函数
"""

import requests
import json
from pathlib import Path
from typing import Optional, Dict, Tuple

def get_ticktick_token(username: str, password: str, is_phone: bool = True) -> Optional[str]:
    """
    获取滴答清单的访问令牌

    Args:
        username: 用户名（手机号或邮箱）
        password: 用户密码
        is_phone: 是否使用手机号登录，True表示使用手机号，False表示使用邮箱

    Returns:
        str: 访问令牌。如果登录失败返回None

    Raises:
        requests.exceptions.RequestException: 当网络请求失败时
        ValueError: 当账号密码错误时
    """
    login_url = "https://api.dida365.com/api/v2/user/signon?wc=true&remember=true"

    # 使用更完整的请求头
    headers = {
        "authority": "api.dida365.com",
        "method": "POST",
        "path": "/api/v2/user/signon?wc=true&remember=true",
        "scheme": "https",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json",
        "Origin": "https://dida365.com",
        "Referer": "https://dida365.com/",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Device": "{\"platform\":\"web\",\"os\":\"Windows 10\",\"device\":\"Chrome 135.0.0.0\",\"name\":\"\",\"version\":\"6261\",\"id\":\"680f7e374d24b35f0c761d9e\",\"channel\":\"website\",\"campaign\":\"\",\"websocket\":\"\"}",
        "X-Requested-With": "XMLHttpRequest"
    }

    # 根据登录类型选择不同的字段名
    if is_phone:
        payload = {
            "password": password,
            "phone": username
        }
    else:
        payload = {
            "password": password,
            "email": username
        }

    try:
        # 创建会话以保持cookie
        session = requests.Session()

        # 先访问主页获取初始cookie
        session.get("https://dida365.com/")

        # 发送登录请求
        response = session.post(login_url, json=payload, headers=headers)
        response.raise_for_status()  # 抛出非200响应的异常

        # 从cookies中获取token
        token = response.cookies.get("t")
        if not token:
            # 如果cookies中没有token，尝试从响应体中获取
            try:
                data = response.json()
                if isinstance(data, dict) and "token" in data:
                    token = data["token"]
                    if token:
                        return token
            except:
                pass

            if not token:
                raise ValueError("登录成功但未获取到token")

        return token

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            raise ValueError("账号或密码错误")
        elif e.response.status_code == 500:
            # 尝试解析错误信息
            try:
                error_data = e.response.json()
                error_message = error_data.get("errorMessage", str(e))
                raise ValueError(f"服务器错误: {error_message}")
            except:
                raise ValueError(f"服务器错误: {str(e)}")
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
                             args_phone: Optional[str] = None,
                             args_email: Optional[str] = None,
                             args_password: Optional[str] = None,
                             env_token: Optional[str] = None,
                             env_phone: Optional[str] = None,
                             env_email: Optional[str] = None,
                             env_password: Optional[str] = None,
                             config_path: str = "config.json") -> Tuple[Dict[str, str], bool]:
    """
    获取认证信息，优先使用token，如果没有token但有用户名密码，则尝试登录并保存token

    Args:
        args_token: 命令行参数中的token
        args_phone: 命令行参数中的手机号
        args_email: 命令行参数中的邮箱
        args_password: 命令行参数中的密码
        env_token: 环境变量中的token
        env_phone: 环境变量中的手机号
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

    # 如果有token，检查是否需要使用它
    if token:
        # 检查传入的账号密码是否与配置文件中的一致
        # 如果一致或者没有传入账号密码，就直接使用token
        config_phone = config.get("phone")
        config_email = config.get("email")
        config_password = config.get("password")

        # 检查是否传入了账号密码
        has_input_credentials = (args_phone or args_email) and args_password

        # 如果没有传入账号密码，直接使用token
        if not has_input_credentials:
            print("使用配置文件中的token进行鉴权")
            return {"token": token}, False

        # 如果传入的是手机号和密码
        if args_phone and args_password:
            # 检查是否与配置文件中的一致
            if args_phone == config_phone and args_password == config_password:
                print("传入的手机号密码与配置文件一致，使用已保存的token")
                return {"token": token}, False

        # 如果传入的是邮箱和密码
        if args_email and args_password:
            # 检查是否与配置文件中的一致
            if args_email == config_email and args_password == config_password:
                print("传入的邮箱密码与配置文件一致，使用已保存的token")
                return {"token": token}, False

        # 如果传入的账号密码与配置文件不一致，说明用户想使用新的账号登录
        print("传入的账号密码与配置文件不一致，将尝试使用新账号登录")

    # 获取手机号和邮箱（优先级：命令行参数 > 环境变量 > 配置文件）
    phone = args_phone or env_phone or config.get("phone")
    email = args_email or env_email or config.get("email")
    password = args_password or env_password or config.get("password")

    # 优先使用手机号登录
    if phone and password:
        try:
            print(f"正在使用手机号 {phone} 登录滴答清单...")
            new_token = get_ticktick_token(phone, password, is_phone=True)
            if new_token:
                # 更新配置信息
                config["token"] = new_token  # 保存token
                config["phone"] = phone      # 保存手机号
                config["password"] = password # 保存密码

                # 如果之前有保存邮箱，但现在使用手机号登录，保留邮箱信息
                if not config.get("email") and email:
                    config["email"] = email

                # 写回配置文件
                try:
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2)
                    print("已成功获取token并保存到配置文件")
                except Exception as e:
                    print(f"警告: 保存配置文件失败: {str(e)}")

                return {"token": new_token}, True
        except Exception as e:
            print(f"使用手机号密码登录失败: {str(e)}")
            # 登录失败，继续尝试使用邮箱

    # 如果手机号登录失败或没有手机号，尝试使用邮箱登录
    if email and password:
        try:
            print(f"正在使用邮箱 {email} 登录滴答清单...")
            new_token = get_ticktick_token(email, password, is_phone=False)
            if new_token:
                # 更新配置信息
                config["token"] = new_token  # 保存token
                config["email"] = email      # 保存邮箱
                config["password"] = password # 保存密码

                # 如果之前有保存手机号，但现在使用邮箱登录，保留手机号信息
                if not config.get("phone") and phone:
                    config["phone"] = phone

                # 写回配置文件
                try:
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2)
                    print("已成功获取token并保存到配置文件")
                except Exception as e:
                    print(f"警告: 保存配置文件失败: {str(e)}")

                return {"token": new_token}, True
        except Exception as e:
            print(f"使用邮箱密码登录失败: {str(e)}")
            # 登录失败，继续尝试使用原始认证信息

    # 如果登录失败，返回原始认证信息
    if phone and password:
        return {"phone": phone, "password": password}, False
    elif email and password:
        return {"email": email, "password": password}, False

    # 如果什么都没有，返回空字典
    return {}, False