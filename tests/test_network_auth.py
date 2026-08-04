from __future__ import annotations

from dataclasses import dataclass
import subprocess

from chatecnu.network_auth import (
    ARGV_PASSWORD_DISABLED_RETURNCODE,
    NetworkAuthClient,
    NetworkAuthCredentials,
    is_online_output,
)


@dataclass
class FakeCompletedProcess:
    args: list[str]
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


def test_network_auth_login_refuses_argv_password_by_default():
    calls: list[tuple[list[str], dict[str, object]]] = []

    def runner(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        return FakeCompletedProcess(list(argv), stdout="Login success\n")

    client = NetworkAuthClient(
        auth_client_path="/opt/ecnu/auth_client",
        setting_file="/etc/ecnu/auth_setting",
        runner=runner,
    )

    result = client.login(NetworkAuthCredentials(username="student", password="secret-value"))

    assert calls == []
    assert result.success is False
    assert result.returncode == ARGV_PASSWORD_DISABLED_RETURNCODE
    assert "process argv" in result.stderr
    assert "secret-value" not in result.stderr
    assert "secret-value" not in result.redacted_command
    assert result.redacted_command.endswith("-p <redacted> -c /etc/ecnu/auth_setting")


def test_network_auth_login_uses_argv_only_when_explicitly_allowed_and_redacts_password():
    calls: list[tuple[list[str], dict[str, object]]] = []

    def runner(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        return FakeCompletedProcess(list(argv), stdout="Login success\n")

    client = NetworkAuthClient(
        auth_client_path="/opt/ecnu/auth_client",
        setting_file="/etc/ecnu/auth_setting",
        runner=runner,
        allow_argv_password=True,
    )

    result = client.login(NetworkAuthCredentials(username="student", password="pa'ss word"))

    assert result.success is True
    assert calls == [
        (
            [
                "/opt/ecnu/auth_client",
                "-u",
                "student",
                "-p",
                "pa'ss word",
                "-c",
                "/etc/ecnu/auth_setting",
            ],
            {"capture_output": True, "check": False, "shell": False, "text": True, "timeout": 20},
        )
    ]
    assert "pa'ss word" not in result.redacted_command
    assert "<redacted>" in result.redacted_command
    assert "pa'ss word" not in result.stdout
    assert "pa'ss word" not in result.stderr


def test_network_auth_redacts_password_echoed_by_auth_client_output():
    def runner(argv, **kwargs):
        return FakeCompletedProcess(
            list(argv),
            returncode=2,
            stdout="debug argv includes -p CANARY_SECRET_123\n",
            stderr="auth_client rejected password CANARY_SECRET_123\n",
        )

    client = NetworkAuthClient(
        auth_client_path="/opt/ecnu/auth_client",
        setting_file="auth_setting",
        runner=runner,
        allow_argv_password=True,
    )

    result = client.login(NetworkAuthCredentials(username="student", password="CANARY_SECRET_123"))

    assert result.success is False
    assert "CANARY_SECRET_123" not in result.stdout
    assert "CANARY_SECRET_123" not in result.stderr
    assert "<redacted>" in result.stdout
    assert "<redacted>" in result.stderr


def test_network_auth_output_parser_handles_known_offline_and_timeout_cases():
    assert is_online_output("Account 20260001 is online.") is True
    assert is_online_output("Account not_online_error is online.") is False
    assert is_online_output("context deadline exceeded (Client.Timeout exceeded while awaiting headers)") is False
    assert is_online_output("not online") is False


def test_network_auth_ensure_login_skips_existing_online_session():
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(list(argv))
        return FakeCompletedProcess(list(argv), stdout="Account 20260001 is online.\n")

    client = NetworkAuthClient(
        auth_client_path="/opt/ecnu/auth_client",
        setting_file="auth_setting",
        runner=runner,
        allow_argv_password=True,
    )

    result = client.ensure_login(NetworkAuthCredentials(username="20260001", password="secret"))

    assert result.action == "ensure-login"
    assert result.success is True
    assert result.skipped is True
    assert calls == [["/opt/ecnu/auth_client", "-c", "auth_setting", "check"]]


def test_network_auth_missing_binary_returns_structured_failure_without_leaking_password():
    def runner(argv, **kwargs):
        raise FileNotFoundError(argv[0])

    client = NetworkAuthClient(
        auth_client_path="/missing/auth_client",
        setting_file="auth_setting",
        runner=runner,
        allow_argv_password=True,
    )

    result = client.login(NetworkAuthCredentials(username="student", password="secret-value"))

    assert result.success is False
    assert result.returncode == 127
    assert "auth_client not found" in result.stderr
    assert "secret-value" not in result.stderr
    assert "secret-value" not in result.redacted_command
    assert "<redacted>" in result.redacted_command


def test_network_auth_timeout_returns_structured_failure_without_leaking_password():
    def runner(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, timeout=3, output="", stderr="")

    client = NetworkAuthClient(
        auth_client_path="/opt/ecnu/auth_client",
        setting_file="auth_setting",
        runner=runner,
        timeout=3,
        allow_argv_password=True,
    )

    result = client.login(NetworkAuthCredentials(username="student", password="secret-value"))

    assert result.success is False
    assert result.returncode == 124
    assert "timed out after 3 seconds" in result.stderr
    assert "secret-value" not in result.stderr
    assert "secret-value" not in result.redacted_command


def test_network_auth_permission_error_returns_structured_failure_without_leaking_password():
    def runner(argv, **kwargs):
        raise PermissionError("permission denied for argv password secret-value")

    client = NetworkAuthClient(
        auth_client_path="/opt/ecnu/auth_client",
        setting_file="auth_setting",
        runner=runner,
        allow_argv_password=True,
    )

    result = client.login(NetworkAuthCredentials(username="student", password="secret-value"))

    assert result.success is False
    assert result.returncode == 126
    assert "PermissionError" in result.stderr
    assert "secret-value" not in result.stderr
    assert "secret-value" not in result.redacted_command
