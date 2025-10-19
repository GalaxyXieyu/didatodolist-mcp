"""
滴答清单官方OAuth 2.0认证模块
基于官方API文档: https://developer.dida365.com/docs#/openapi
"""

import requests
import json
import webbrowser
from typing import Optional, Dict, Tuple
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import os


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuth回调处理器"""

    authorization_code = None

    def do_GET(self):
        """处理OAuth回调请求"""
        # 解析查询参数
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            # 保存授权码
            OAuthCallbackHandler.authorization_code = params['code'][0]

            # 返回成功页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            success_html = """
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                    <h1>Authorization Success!</h1>
                    <p>You can close this window and return to terminal.</p>
                    <script>window.close();</script>
                </body>
                </html>
            """
            self.wfile.write(success_html.encode('utf-8'))
        else:
            # 返回错误页面
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            error_html = """
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                    <h1>Authorization Failed!</h1>
                    <p>No authorization code received. Please retry.</p>
                </body>
                </html>
            """
            self.wfile.write(error_html.encode('utf-8'))

    def log_message(self, format, *args):
        """禁用日志输出"""
        pass


class DidaOAuthClient:
    """滴答清单OAuth 2.0客户端"""

    # 官方API端点
    BASE_URL = "https://api.dida365.com/open/v1"
    AUTH_URL = "https://dida365.com/oauth/authorize"
    TOKEN_URL = "https://dida365.com/oauth/token"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://localhost:38000/callback"):
        """
        初始化OAuth客户端

        Args:
            client_id: 应用Client ID
            client_secret: 应用Client Secret
            redirect_uri: OAuth回调地址(默认: http://localhost:8000/callback)
        """
        # 允许使用环境变量覆盖（.env 支持）
        self.client_id = client_id or os.environ.get("DIDA_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("DIDA_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("DIDA_REDIRECT_URI", redirect_uri)
        self.access_token = None
        self.refresh_token = None

    def get_authorization_url(self, scope: str = "tasks:read tasks:write") -> str:
        """
        生成OAuth授权URL

        Args:
            scope: 请求的权限范围(默认: tasks:read tasks:write)

        Returns:
            str: 授权URL
        """
        params = {
            "client_id": self.client_id,
            "scope": scope,
            "state": "random_state",  # 建议使用随机字符串
            "redirect_uri": self.redirect_uri,
            "response_type": "code"
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query_string}"

    def start_callback_server(self, port: int = 38000) -> Optional[str]:
        """
        启动本地回调服务器并等待授权码

        Args:
            port: 服务器端口(默认: 8000)

        Returns:
            Optional[str]: 授权码,失败返回None
        """
        # 重置授权码
        OAuthCallbackHandler.authorization_code = None

        # 创建HTTP服务器
        server = HTTPServer(('localhost', port), OAuthCallbackHandler)

        print(f"本地回调服务器已启动: http://localhost:{port}/callback")
        print("等待授权...")

        # 在新线程中运行服务器
        def run_server():
            while OAuthCallbackHandler.authorization_code is None:
                server.handle_request()

        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        # 等待授权码
        server_thread.join(timeout=300)  # 5分钟超时

        return OAuthCallbackHandler.authorization_code

    def authorize(self, auto_open_browser: bool = True) -> bool:
        """
        执行完整的OAuth授权流程

        Args:
            auto_open_browser: 是否自动打开浏览器(默认: True)

        Returns:
            bool: 授权是否成功
        """
        # 生成授权URL
        auth_url = self.get_authorization_url()

        print("\n=== 滴答清单OAuth授权 ===")
        print(f"授权URL: {auth_url}\n")

        if auto_open_browser:
            print("正在打开浏览器进行授权...")
            webbrowser.open(auth_url)
        else:
            print("请在浏览器中打开上述URL进行授权")

        # 根据 redirect_uri 自动选择监听端口
        try:
            parsed = urlparse(self.redirect_uri)
            listen_port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        except Exception:
            listen_port = 38000

        # 启动回调服务器（端口与 redirect_uri 对齐）
        authorization_code = self.start_callback_server(port=listen_port)

        if not authorization_code:
            print("❌ 授权失败: 未收到授权码")
            return False

        print(f"✅ 收到授权码: {authorization_code[:10]}...")

        # 交换访问令牌
        return self.exchange_token(authorization_code)

    def exchange_token(self, authorization_code: str) -> bool:
        """
        使用授权码交换访问令牌

        Args:
            authorization_code: OAuth授权码

        Returns:
            bool: 交换是否成功
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        try:
            print("正在交换访问令牌...")
            response = requests.post(self.TOKEN_URL, data=payload)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")

            if self.access_token:
                print("✅ 成功获取访问令牌!")
                return True
            else:
                print("❌ 令牌交换失败: 响应中无access_token")
                return False

        except requests.exceptions.HTTPError as e:
            print(f"❌ 令牌交换失败: HTTP {e.response.status_code}")
            try:
                error_data = e.response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"错误详情: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ 令牌交换失败: {str(e)}")
            return False

    def refresh_access_token(self) -> bool:
        """
        使用refresh token刷新访问令牌

        Returns:
            bool: 刷新是否成功
        """
        if not self.refresh_token:
            print("❌ 无refresh_token,无法刷新")
            return False

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }

        try:
            response = requests.post(self.TOKEN_URL, data=payload)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")

            # 可能会返回新的refresh_token
            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token:
                self.refresh_token = new_refresh_token

            print("✅ 访问令牌已刷新!")
            return True

        except Exception as e:
            print(f"❌ 刷新令牌失败: {str(e)}")
            return False

    def save_tokens(self, config_path: str = "oauth_config.json") -> bool:
        """
        保存令牌到配置文件

        Args:
            config_path: 配置文件路径(默认: oauth_config.json)

        Returns:
            bool: 保存是否成功
        """
        if not self.access_token:
            print("❌ 无访问令牌可保存")
            return False

        config = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token
        }

        try:
            config_file = Path(config_path)
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"✅ 令牌已保存到: {config_path}")
            return True
        except Exception as e:
            print(f"❌ 保存令牌失败: {str(e)}")
            return False

    def load_tokens(self, config_path: str = "oauth_config.json") -> bool:
        """
        从配置文件加载令牌

        Args:
            config_path: 配置文件路径(默认: oauth_config.json)

        Returns:
            bool: 加载是否成功
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                print(f"⚠️  配置文件不存在: {config_path}")
                return False

            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            self.client_id = config.get("client_id", self.client_id)
            self.client_secret = config.get("client_secret", self.client_secret)
            self.redirect_uri = config.get("redirect_uri", self.redirect_uri)
            self.access_token = config.get("access_token")
            self.refresh_token = config.get("refresh_token")

            if self.access_token:
                print(f"✅ 令牌已从配置文件加载: {config_path}")
                return True
            else:
                print("⚠️  配置文件中无访问令牌")
                return False

        except Exception as e:
            print(f"❌ 加载令牌失败: {str(e)}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """
        获取带有认证信息的请求头

        Returns:
            Dict[str, str]: HTTP请求头
        """
        if not self.access_token:
            raise ValueError("未设置access_token")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }


def test_oauth_flow(client_id: str, client_secret: str):
    """
    测试完整的OAuth流程

    Args:
        client_id: 应用Client ID
        client_secret: 应用Client Secret
    """
    print("\n" + "="*50)
    print("滴答清单官方OAuth 2.0测试")
    print("="*50 + "\n")

    # 创建OAuth客户端
    oauth_client = DidaOAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8000/callback"
    )

    # 尝试加载已保存的令牌
    if oauth_client.load_tokens():
        print("使用已保存的令牌")
    else:
        # 执行授权流程
        if oauth_client.authorize():
            # 保存令牌
            oauth_client.save_tokens()
        else:
            print("❌ OAuth授权失败")
            return

    # 测试API调用
    try:
        headers = oauth_client.get_headers()
        print(f"\n✅ 请求头已生成:")
        print(f"Authorization: Bearer {oauth_client.access_token[:20]}...")

        # 测试获取项目列表
        print("\n正在测试API调用: 获取项目列表...")
        response = requests.get(
            f"{DidaOAuthClient.BASE_URL}/project",
            headers=headers
        )

        if response.status_code == 200:
            projects = response.json()
            print(f"✅ API调用成功! 找到 {len(projects)} 个项目")
            for i, project in enumerate(projects[:3], 1):
                print(f"  {i}. {project.get('name', 'Unnamed')}")
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"❌ API测试失败: {str(e)}")


if __name__ == "__main__":
    # 测试示例
    CLIENT_ID = "2EBu78R95UzRewO4Fh"
    CLIENT_SECRET = "2EBu78R95UzRewO4Fh"

    test_oauth_flow(CLIENT_ID, CLIENT_SECRET)
