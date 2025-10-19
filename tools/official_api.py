"""
滴答清单官方API - 认证模块（.env-only）
统一使用 .env 环境变量进行配置与令牌持久化。

必需/可选环境变量：
- DIDA_CLIENT_ID, DIDA_CLIENT_SECRET（用于刷新令牌）
- DIDA_ACCESS_TOKEN, DIDA_REFRESH_TOKEN（由授权脚本写入）
"""

import os
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

        # 仅从环境变量加载（.env 由上层 dotenv 加载）
        self.load_env()

    def load_env(self) -> bool:
        """
        从环境变量加载/覆盖认证信息（.env-only）
        """
        try:
            env_client_id = os.environ.get("DIDA_CLIENT_ID")
            env_client_secret = os.environ.get("DIDA_CLIENT_SECRET")
            env_access_token = os.environ.get("DIDA_ACCESS_TOKEN")
            env_refresh_token = os.environ.get("DIDA_REFRESH_TOKEN")

            # 若环境变量存在则覆盖
            if env_client_id:
                self.client_id = env_client_id
            if env_client_secret:
                self.client_secret = env_client_secret
            if env_access_token:
                self.access_token = env_access_token
            if env_refresh_token:
                self.refresh_token = env_refresh_token

            return self.access_token is not None
        except Exception as e:
            print(f"加载环境变量失败: {str(e)}")
            return False

    # --- 持久化到 .env ---
    def _update_env_tokens(self, access_token: Optional[str], refresh_token: Optional[str]):
        """将新的令牌写入工作目录下的 .env（若存在则更新对应行）。"""
        try:
            env_path = Path(".env")
            lines = []
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()

            def upsert(key: str, value: Optional[str]):
                nonlocal lines
                lines = [ln for ln in lines if not ln.startswith(f"{key}=")]
                if value is not None:
                    lines.append(f"{key}={value}")

            if access_token:
                upsert("DIDA_ACCESS_TOKEN", access_token)
            if refresh_token is not None:
                upsert("DIDA_REFRESH_TOKEN", refresh_token)

            content = "\n".join(lines)
            if not content.endswith("\n"):
                content += "\n"
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            # 写入失败不应阻断主流程，仅记录
            print(f"写入 .env 令牌失败: {e}")

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

            # 固定回写 .env（.env-only 策略）
            self._update_env_tokens(self.access_token, self.refresh_token)
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
    )

    if not _api_client.access_token:
        raise APIError(
            "未找到有效的access_token，请先在本机运行授权脚本写入 .env"
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
