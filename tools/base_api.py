"""
基础API功能模块
提供HTTP请求、认证和错误处理的基本功能
"""

import os
import json
import requests
from typing import Dict, Any, Optional, Union

class APIError(Exception):
    """API调用错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

# 全局变量，用于存储认证信息和请求头
BASE_URL = "https://api.dida365.com"
_token = None
_headers = {}
_debug = True  # 设置为True开启详细日志

def init_api(token: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, password: Optional[str] = None, debug: bool = False):
    """
    初始化API

    Args:
        token: 滴答清单API令牌（优先使用）
        email: 用户邮箱（当没有token时使用）
        phone: 用户手机号（当没有token和邮箱时使用）
        password: 用户密码（当没有token时使用）
        debug: 是否开启调试模式
    """
    global _token, _headers, _debug

    _debug = debug

    # 打印初始化参数信息（隐藏敏感数据）
    if _debug:
        print(f"初始化API - 使用token: {'已提供' if token else '未提供'}, email: {'已提供' if email else '未提供'}, phone: {'已提供' if phone else '未提供'}")

    # 如果没有提供token但提供了认证信息，则尝试登录获取token
    if not token:
        if phone and password:
            # 优先使用手机号登录
            token = _login(phone, password, is_phone=True)
        elif email and password:
            # 其次使用邮箱登录
            token = _login(email, password, is_phone=False)

    if not token:
        raise APIError("必须提供令牌(token)或手机号(phone)/邮箱(email)和密码(password)进行认证")

    _token = token

    # 设置请求头，完全匹配Apifox的格式
    _headers = {
        "Accept": "application/json",
        "Cookie": f"t={_token}",
        "User-Agent": "Apifox/1.0.0",
        "Content-Type": "application/json",
        "Host": "api.dida365.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    if _debug:
        print(f"API初始化完成，请求头已设置: {json.dumps(_headers, ensure_ascii=False)}")

def _login(username: str, password: str, is_phone: bool = True) -> str:
    """
    使用用户名和密码登录获取token

    Args:
        username: 用户名（手机号或邮箱）
        password: 用户密码
        is_phone: 是否使用手机号登录，True表示使用手机号，False表示使用邮箱

    Returns:
        获取到的token
    """
    # 使用api.dida365.com进行登录
    login_url = "https://api.dida365.com/api/v2/user/signon?wc=true&remember=true"

    # 根据登录类型选择不同的字段名
    if is_phone:
        login_data = {
            "password": password,
            "phone": username
        }
    else:
        login_data = {
            "password": password,
            "email": username
        }

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

    login_type = "手机号" if is_phone else "邮箱"
    if _debug:
        print(f"尝试使用{login_type}登录账号: {username}")

    try:
        # 创建会话以保持cookie
        session = requests.Session()

        # 先访问主页获取初始cookie
        session.get("https://dida365.com/")

        # 发送登录请求
        response = session.post(login_url, json=login_data, headers=headers)

        response.raise_for_status()

        # 首先尝试从cookies中获取token
        token = response.cookies.get("t")
        if token:
            if _debug:
                print(f"从cookies中获取到token: {token[:10]}...")
            return token

        # 如果cookies中没有token，则尝试从响应体中获取
        data = response.json()

        if isinstance(data, dict) and "token" in data:
            if _debug:
                print("从响应体中获取到token")
            return data["token"]
        else:
            if _debug:
                print(f"登录异常: 响应中没有token字段，完整响应: {json.dumps(data, ensure_ascii=False)}")
            raise APIError("登录成功但未返回token", response.status_code, data)

    except requests.exceptions.RequestException as e:
        if _debug:
            print(f"登录失败异常: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"错误状态码: {e.response.status_code}")
                print(f"错误响应: {e.response.text}")
        raise APIError(f"登录失败: {str(e)}")

def _request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None) -> Any:
    """
    发送API请求

    Args:
        method: HTTP方法 (GET, POST, PUT, DELETE)
        endpoint: API端点
        data: 请求体数据
        params: URL参数

    Returns:
        解析后的响应JSON
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=_headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=_headers, json=data, params=params)
        elif method == "PUT":
            response = requests.put(url, headers=_headers, json=data, params=params)
        elif method == "DELETE":
            response = requests.delete(url, headers=_headers, json=data, params=params)
        else:
            raise APIError(f"不支持的HTTP方法: {method}")

        # 检查响应状态码
        if response.status_code >= 400:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_msg += f": {json.dumps(error_data, ensure_ascii=False)}"
                else:
                    error_msg += f": {error_data}"
            except:
                error_msg += f": {response.text}"
            raise requests.exceptions.HTTPError(error_msg, response=response)

        response.raise_for_status()

        # 检查响应内容是否为JSON
        if response.text:
            return response.json()
        return {}

    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', None)
        response_text = getattr(e.response, 'text', str(e))

        if _debug:
            print(f"\n===== API错误 =====")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print(f"状态码: {status_code}")
            print(f"错误响应: {response_text}")

            # 打印请求详情
            if hasattr(e, 'request'):
                req = e.request
                print(f"\n请求详情:")
                print(f"URL: {req.url}")
                print(f"方法: {req.method}")
                print(f"请求头: {json.dumps(dict(req.headers), ensure_ascii=False)}")
                if req.body:
                    try:
                        body_str = req.body.decode('utf-8')
                        print(f"请求体: {body_str}")
                    except:
                        print(f"请求体: <无法解码>")
                else:
                    print(f"请求体: None")

        try:
            response_data = json.loads(response_text)
        except:
            response_data = response_text

        raise APIError(f"API请求失败: {str(e)}", status_code, response_data)

def get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """发送GET请求"""
    return _request("GET", endpoint, params=params)

def post(endpoint: str, data: Optional[Dict[str, Any]] = None,
         params: Optional[Dict[str, Any]] = None) -> Any:
    """发送POST请求"""
    return _request("POST", endpoint, data=data, params=params)

def put(endpoint: str, data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None) -> Any:
    """发送PUT请求"""
    return _request("PUT", endpoint, data=data, params=params)

def delete(endpoint: str, data: Optional[Dict[str, Any]] = None,
           params: Optional[Dict[str, Any]] = None) -> Any:
    """发送DELETE请求"""
    return _request("DELETE", endpoint, data=data, params=params)