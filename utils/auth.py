"""
认证相关工具类
"""
import requests
from typing import Optional
from utils.http import AuthenticationError

def get_token(email: str, password: str) -> str:
    """
    通过邮箱和密码获取访问令牌
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        str: 访问令牌
        
    Raises:
        AuthenticationError: 认证失败
    """
    login_url = "https://dida365.com/api/v2/user/signon?wc=true&remember=true"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=payload, headers=headers)
        if response.status_code == 200:
            token = response.cookies.get("t")
            if token:
                return token
            raise AuthenticationError("登录成功但未获取到token")
        else:
            raise AuthenticationError("登录失败，请检查账号密码")
    except requests.RequestException as e:
        raise AuthenticationError(f"请求失败: {str(e)}")

class TokenManager:
    """Token管理器"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化Token管理器
        
        Args:
            token: 可选的访问令牌
        """
        self._token = token
    
    @property
    def token(self) -> Optional[str]:
        """获取当前token"""
        return self._token
    
    @token.setter
    def token(self, value: str):
        """设置新的token"""
        self._token = value
    
    def login(self, email: str, password: str) -> str:
        """
        登录并获取新token
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            str: 新的访问令牌
        """
        self._token = get_token(email, password)
        return self._token
    
    def is_valid(self) -> bool:
        """
        检查当前token是否有效
        
        Returns:
            bool: token是否有效
        """
        if not self._token:
            return False
            
        # 这里可以添加token验证逻辑
        return True 