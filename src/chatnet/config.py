"""ChatEnv configuration schemas provided by ChatNet."""

from __future__ import annotations

from chatenv.fields import BaseEnvConfig, EnvField


class ECNUConfig(BaseEnvConfig):
    """ECNU self-service portal environment variables."""

    _title = "ECNU"
    _aliases = ["ecnu", "chatnet-ecnu"]
    _storage_dir = "ECNU"

    ECNU_USERNAME = EnvField("ECNU_USERNAME", desc="ECNU username.")
    ECNU_PASSWORD = EnvField("ECNU_PASSWORD", desc="ECNU password.", is_sensitive=True)
    ECNU_COOKIE = EnvField("ECNU_COOKIE", desc="Authenticated ECNU portal Cookie header.", is_sensitive=True)
    ECNU_BASE_URL = EnvField("ECNU_BASE_URL", default="https://login.ecnu.edu.cn:8800", desc="ECNU portal base URL.")
    ECNU_VISITOR_PASSWORD1 = EnvField("ECNU_VISITOR_PASSWORD1", desc="Default password for visitor account suffix m1.", is_sensitive=True)
    ECNU_VISITOR_PASSWORD2 = EnvField("ECNU_VISITOR_PASSWORD2", desc="Default password for visitor account suffix m2.", is_sensitive=True)
    ECNU_VISITOR_REMARK = EnvField("ECNU_VISITOR_REMARK", default="default", desc="Default remark used by `chatnet ecnu visitor default`.")

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
        print(f"   Cookie configured: {bool(cls.ECNU_COOKIE.value)}")


__all__ = ["ECNUConfig"]
