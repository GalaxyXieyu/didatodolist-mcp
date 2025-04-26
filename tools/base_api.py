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

def init_api(token: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None, debug: bool = False):
    """
    初始化API
    
    Args:
        token: 滴答清单API令牌（优先使用）
        email: 用户邮箱（当没有token时使用）
        password: 用户密码（当没有token时使用）
        debug: 是否开启调试模式
    """
    global _token, _headers, _debug
    
    _debug = debug
    
    # 打印初始化参数信息（隐藏敏感数据）
    if _debug:
        print(f"初始化API - 使用token: {'已提供' if token else '未提供'}, email: {'已提供' if email else '未提供'}")
    
    # 如果没有提供token但提供了邮箱和密码，则尝试登录获取token
    if not token and email and password:
        token = _login(email, password)
        
    if not token:
        raise APIError("必须提供令牌(token)或邮箱(email)和密码(password)进行认证")
    
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

def _login(email: str, password: str) -> str:
    """
    使用邮箱和密码登录获取token
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        获取到的token
    """
    # 使用dida365.com而不是api.dida365.com进行登录，以获取cookie中的token
    login_url = "https://dida365.com/api/v2/user/signon?wc=true&remember=true"
    login_data = {
        "username": email,
        "password": password
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    if _debug:
        print(f"尝试登录账号: {email}")
    
    try:
        response = requests.post(login_url, json=login_data, headers=headers)
        if _debug:
            print(f"登录请求状态码: {response.status_code}")
            print(f"登录响应cookies: {response.cookies}")
            
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
    
    if _debug:
        print(f"\n===== API请求 =====")
        print(f"方法: {method}")
        print(f"URL: {url}")
        print(f"参数: {json.dumps(params, ensure_ascii=False) if params else 'None'}")
        print(f"数据: {json.dumps(data, ensure_ascii=False)[:1000] if data else 'None'}")
        print(f"请求头: {json.dumps(_headers, ensure_ascii=False)}")
    
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
        
        if _debug:
            print(f"\n===== API响应 =====")
            print(f"状态码: {response.status_code}")
            print(f"响应头: {json.dumps(dict(response.headers), ensure_ascii=False)}")
            print(f"响应内容: {response.text[:1000]}...")
        
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