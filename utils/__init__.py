"""
滴答清单工具包初始化（精简版）

为避免导入包时意外加载已废弃模块（如旧鉴权/逆向接口），此处不做任何包级导入。
按需从子模块显式导入，例如：
    from utils.oauth_auth import DidaOAuthClient
"""

__all__: list[str] = []
