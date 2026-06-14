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


__all__ = ["ECNUConfig"]
