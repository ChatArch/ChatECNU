"""ChatEnv configuration schemas provided by ChatECNU."""

from __future__ import annotations

from chatenv.fields import BaseEnvConfig, EnvField


class ECNUConfig(BaseEnvConfig):
    """ECNU self-service portal environment variables."""

    _title = "ECNU"
    _aliases = ["ecnu"]
    _storage_dir = "ECNU"

    ECNU_USERNAME = EnvField("ECNU_USERNAME", desc="ECNU 用户名。")
    ECNU_PASSWORD = EnvField("ECNU_PASSWORD", desc="ECNU 密码。", is_sensitive=True)
    ECNU_BASE_URL = EnvField("ECNU_BASE_URL", default="https://login.ecnu.edu.cn:8800", desc="ECNU 门户地址。")
    ECNU_VISITOR_PASSWORD1 = EnvField("ECNU_VISITOR_PASSWORD1", desc="默认访客账号 m1 密码。", is_sensitive=True)
    ECNU_VISITOR_PASSWORD2 = EnvField("ECNU_VISITOR_PASSWORD2", desc="默认访客账号 m2 密码。", is_sensitive=True)
    ECNU_VISITOR_REMARK = EnvField("ECNU_VISITOR_REMARK", default="default", desc="默认访客账号备注。")
    ECNU_AUTH_CLIENT = EnvField("ECNU_AUTH_CLIENT", default="auth_client", desc="auth_client 路径。")
    ECNU_AUTH_SETTING_FILE = EnvField("ECNU_AUTH_SETTING_FILE", desc="auth_client 设置文件。")

    @classmethod
    def test(cls) -> None:
        """Validate that the ECNU config schema is loadable without network access."""

        print(f"Testing {cls._title}...")
        base_url = cls.ECNU_BASE_URL.value or cls.ECNU_BASE_URL.default
        if not base_url:
            print("❌ Failed: ECNU_BASE_URL not set")
            return
        print(f"✅ Config loaded. Base URL: {base_url}")
        print(f"   Username configured: {bool(cls.ECNU_USERNAME.value)}")


__all__ = ["ECNUConfig"]
