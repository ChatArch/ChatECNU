from __future__ import annotations

import json

from click.testing import CliRunner

from chatecnu.cli import main
from chatecnu.network_auth import NetworkAuthCredentials, NetworkAuthResult
import chatecnu.ecnu.cli as ecnu_cli


class FakeNetworkAuthClient:
    def __init__(self):
        self.calls = []

    def login(self, credentials):
        self.calls.append(("login", credentials))
        return NetworkAuthResult(
            action="login",
            success=True,
            returncode=0,
            stdout="Login success\n",
            stderr="",
            redacted_command="/opt/ecnu/auth_client -u student -p <redacted> -c auth_setting",
        )

    def ensure_login(self, credentials):
        self.calls.append(("ensure_login", credentials))
        return NetworkAuthResult(
            action="ensure-login",
            success=True,
            returncode=0,
            stdout="Account student is online.\n",
            stderr="",
            redacted_command="/opt/ecnu/auth_client -c auth_setting check",
            online=True,
            skipped=True,
        )

    def check(self):
        self.calls.append(("check", None))
        return NetworkAuthResult(
            action="check",
            success=True,
            returncode=0,
            stdout="Account student is online.\n",
            stderr="",
            redacted_command="/opt/ecnu/auth_client -c auth_setting check",
            online=True,
            skipped=False,
        )


def test_auth_is_short_visible_command_and_network_auth_is_hidden_alias():
    help_result = CliRunner().invoke(main, ["--help"])
    assert help_result.exit_code == 0, help_result.output
    assert "  auth" in help_result.output
    assert "校园网登录。" in help_result.output
    assert "network-auth" not in help_result.output

    alias_result = CliRunner().invoke(main, ["network-auth", "--help"])
    assert alias_result.exit_code == 0, alias_result.output
    assert "Usage: chatecnu network-auth" in alias_result.output


def test_network_auth_check_cli_delegates_to_api_without_requiring_password(monkeypatch):
    fake = FakeNetworkAuthClient()
    monkeypatch.setattr(
        ecnu_cli,
        "make_network_auth_client",
        lambda *, auth_client_path, setting_file, allow_argv_password=False, prefer_loaded_chatenv=False: fake,
    )

    result = CliRunner().invoke(
        main,
        [
            "network-auth",
            "check",
            "--auth-client",
            "/opt/ecnu/auth_client",
            "--setting-file",
            "auth_setting",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "check"
    assert payload["success"] is True
    assert payload["online"] is True
    assert fake.calls == [("check", None)]


def test_network_auth_login_cli_delegates_to_api_without_printing_password(monkeypatch):
    fake = FakeNetworkAuthClient()
    monkeypatch.setattr(
        ecnu_cli,
        "make_network_auth_client",
        lambda *, auth_client_path, setting_file, allow_argv_password=False, prefer_loaded_chatenv=False: fake,
    )

    result = CliRunner().invoke(
        main,
        [
            "network-auth",
            "login",
            "--auth-client",
            "/opt/ecnu/auth_client",
            "--setting-file",
            "auth_setting",
            "--username",
            "student",
            "--password",
            "secret-value",
            "--allow-argv-password",
            "--json",
            "-I",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "secret-value" not in result.output
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["action"] == "login"
    assert payload["redacted_command"].endswith("-p <redacted> -c auth_setting")
    assert fake.calls == [("login", NetworkAuthCredentials(username="student", password="secret-value"))]


def test_network_auth_ensure_login_cli_replaces_periodic_shell_script(monkeypatch):
    fake = FakeNetworkAuthClient()
    monkeypatch.setattr(
        ecnu_cli,
        "make_network_auth_client",
        lambda *, auth_client_path, setting_file, allow_argv_password=False, prefer_loaded_chatenv=False: fake,
    )

    result = CliRunner().invoke(
        main,
        [
            "network-auth",
            "ensure-login",
            "--auth-client",
            "/opt/ecnu/auth_client",
            "--setting-file",
            "auth_setting",
            "--username",
            "student",
            "--password",
            "secret-value",
            "--allow-argv-password",
            "--json",
            "-I",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "secret-value" not in result.output
    payload = json.loads(result.output)
    assert payload["action"] == "ensure-login"
    assert payload["success"] is True
    assert payload["skipped"] is True
    assert fake.calls == [("ensure_login", NetworkAuthCredentials(username="student", password="secret-value"))]


def test_network_auth_cli_exits_nonzero_on_failed_auth_client_result(monkeypatch):
    class FailingNetworkAuthClient:
        def login(self, credentials):
            return NetworkAuthResult(
                action="login",
                success=False,
                returncode=127,
                stdout="debug argv: -u student -p secret-value\n",
                stderr="auth_client rejected password secret-value",
                redacted_command="/missing/auth_client -u student -p secret-value -c auth_setting",
            )

    monkeypatch.setattr(
        ecnu_cli,
        "make_network_auth_client",
        lambda *, auth_client_path, setting_file, allow_argv_password=False, prefer_loaded_chatenv=False: FailingNetworkAuthClient(),
    )

    result = CliRunner().invoke(
        main,
        [
            "network-auth",
            "login",
            "--auth-client",
            "/missing/auth_client",
            "--setting-file",
            "auth_setting",
            "--username",
            "student",
            "--password",
            "secret-value",
            "--allow-argv-password",
            "--json",
            "-I",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "secret-value" not in result.output
    payload = json.loads(result.output)
    assert payload["success"] is False
    assert payload["returncode"] == 127
    assert payload["stdout"] == "debug argv: -u student -p <redacted>\n"
    assert payload["stderr"] == "auth_client rejected password <redacted>"
    assert payload["redacted_command"].endswith("-p <redacted> -c auth_setting")


def test_network_auth_cli_refuses_argv_password_by_default_without_spawning():
    result = CliRunner().invoke(
        main,
        [
            "network-auth",
            "login",
            "--auth-client",
            "/opt/ecnu/auth_client",
            "--setting-file",
            "auth_setting",
            "--username",
            "student",
            "--password",
            "secret-value",
            "--json",
            "-I",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "secret-value" not in result.output
    payload = json.loads(result.output)
    assert payload["success"] is False
    assert payload["returncode"] == 126
    assert "argv" in payload["stderr"]
    assert payload["redacted_command"].endswith("-p <redacted> -c auth_setting")


def test_network_auth_cli_process_env_overrides_default_active_chatenv(monkeypatch, tmp_path):
    fake = FakeNetworkAuthClient()
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    monkeypatch.setenv("ECNU_USERNAME", "process-user")
    monkeypatch.setenv("ECNU_PASSWORD", "process-secret")
    env_file = tmp_path / "chatarch" / "envs" / "ECNU" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "ECNU_USERNAME='profile-user'\nECNU_PASSWORD='profile-secret'\nECNU_AUTH_CLIENT='profile-auth-client'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        ecnu_cli,
        "make_network_auth_client",
        lambda *, auth_client_path, setting_file, allow_argv_password=False, prefer_loaded_chatenv=False: fake,
    )

    result = CliRunner().invoke(
        main,
        [
            "network-auth",
            "login",
            "--allow-argv-password",
            "--json",
            "-I",
        ],
    )

    assert result.exit_code == 0, result.output
    assert fake.calls == [("login", NetworkAuthCredentials(username="process-user", password="process-secret"))]
    assert "process-secret" not in result.output
