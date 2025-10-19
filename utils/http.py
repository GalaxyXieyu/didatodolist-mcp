"""
HTTP 请求工具类
"""
from typing import Optional, Dict, Any, Union
import requests

# 定义AuthenticationError异常类
class AuthenticationError(Exception):
    """认证错误"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class HttpClient:
    """HTTP请求客户端"""
    
    def __init__(self, token: str):
        """
        初始化HTTP客户端
        
        Args:
            token: API访问令牌
        """
        self.token = token
        self.base_url = "https://api.dida365.com"
        self.headers = {
            "Cookie": f"t={token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def _handle_response(self, response: requests.Response) -> Union[Dict[str, Any], bool]:
        """
        处理API响应
        
        Args:
            response: 请求响应对象
            
        Returns:
            Dict 或 bool: 响应数据或成功状态
            
        Raises:
            AuthenticationError: 认证失败
            APIError: API调用失败
        """
        if response.status_code == 401:
            raise AuthenticationError("认证失败，请检查token是否有效")
            
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"error": response.text}
            raise APIError(
                message=error_data.get("error", "未知错误"),
                status_code=response.status_code,
                response=error_data
            )
            
        if response.status_code == 204:
            return True
            
        try:
            return response.json()
        except ValueError:
            return True
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送GET请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            
        Returns:
            Dict: 响应数据
        """
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )
        return self._handle_response(response)
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送POST请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            
        Returns:
            Dict: 响应数据
        """
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=data
        )
        return self._handle_response(response)
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送PUT请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            
        Returns:
            Dict: 响应数据
        """
        response = requests.put(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=data
        )
        return self._handle_response(response)
    
    def delete(self, endpoint: str) -> bool:
        """
        发送DELETE请求
        
        Args:
            endpoint: API端点
            
        Returns:
            bool: 是否删除成功
        """
        response = requests.delete(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )
        return self._handle_response(response) 