"""
滴答清单官方API - 认证模块
基于OAuth 2.0官方接口，替换旧的逆向接口
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path


class APIError(Exception):
    """API调用错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class DidaOfficialAPI:
    """滴答清单官方API客户端"""

    # 官方API端点
    BASE_URL = "https://api.dida365.com/open/v1"
    AUTH_URL = "https://dida365.com/oauth/authorize"
    TOKEN_URL = "https://dida365.com/oauth/token"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        config_path: str = "oauth_config.json"
    ):
        """
        初始化官方API客户端

        Args:
            client_id: OAuth Client ID
            client_secret: OAuth Client Secret
            access_token: OAuth Access Token
            config_path: 配置文件路径
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = None
        self.config_path = config_path

        # 如果提供了配置文件路径，尝试加载
        if not self.access_token:
            self.load_config()

    def load_config(self) -> bool:
        """
        从配置文件加载认证信息

        Returns:
            bool: 加载是否成功
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                return False

            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            self.client_id = config.get("client_id", self.client_id)
            self.client_secret = config.get("client_secret", self.client_secret)
            self.access_token = config.get("access_token")
            self.refresh_token = config.get("refresh_token")

            return self.access_token is not None

        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return False

    def save_config(self) -> bool:
        """
        保存认证信息到配置文件

        Returns:
            bool: 保存是否成功
        """
        if not self.access_token:
            return False

        config = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """
        获取带有认证信息的请求头

        Returns:
            Dict[str, str]: HTTP请求头
        """
        if not self.access_token:
            raise APIError("未设置access_token，请先完成OAuth认证")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def refresh_access_token(self) -> bool:
        """
        使用refresh token刷新访问令牌

        Returns:
            bool: 刷新是否成功
        """
        if not self.refresh_token:
            return False

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }

        try:
            response = requests.post(self.TOKEN_URL, data=payload, timeout=10)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")

            # 可能会返回新的refresh_token
            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token:
                self.refresh_token = new_refresh_token

            # 保存新令牌
            self.save_config()
            return True

        except Exception as e:
            print(f"刷新令牌失败: {str(e)}")
            return False

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        发送API请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点 (如 /project, /task)
            data: 请求体数据
            params: URL查询参数

        Returns:
            API响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self.get_headers()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=10
            )

            # 处理401错误 - 令牌过期
            if response.status_code == 401:
                # 尝试刷新令牌
                if self.refresh_access_token():
                    # 重新发送请求
                    headers = self.get_headers()
                    response = requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params,
                        timeout=10
                    )
                else:
                    raise APIError(
                        "访问令牌已过期且无法刷新，请重新进行OAuth认证",
                        status_code=401
                    )

            response.raise_for_status()

            # 处理空响应
            if response.status_code == 204 or not response.content:
                return True

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_message = f"API请求失败: {e}"
            try:
                error_data = e.response.json()
                error_message = error_data.get("errorMessage", error_message)
            except:
                pass

            raise APIError(
                error_message,
                status_code=e.response.status_code if hasattr(e, 'response') else None
            )

        except requests.exceptions.RequestException as e:
            raise APIError(f"网络请求失败: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET请求"""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """POST请求"""
        return self._request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """PUT请求"""
        return self._request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Any:
        """DELETE请求"""
        return self._request("DELETE", endpoint)


# 全局API客户端实例
_api_client: Optional[DidaOfficialAPI] = None


def init_api(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    access_token: Optional[str] = None,
    config_path: str = "oauth_config.json"
) -> DidaOfficialAPI:
    """
    初始化官方API客户端

    Args:
        client_id: OAuth Client ID
        client_secret: OAuth Client Secret
        access_token: OAuth Access Token
        config_path: 配置文件路径

    Returns:
        DidaOfficialAPI: API客户端实例
    """
    global _api_client

    _api_client = DidaOfficialAPI(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        config_path=config_path
    )

    if not _api_client.access_token:
        raise APIError(
            "未找到有效的access_token，请先完成OAuth认证或提供配置文件"
        )

    return _api_client


def get_api_client() -> DidaOfficialAPI:
    """
    获取全局API客户端实例

    Returns:
        DidaOfficialAPI: API客户端实例
    """
    if _api_client is None:
        raise APIError("API客户端未初始化，请先调用init_api()")

    return _api_client
