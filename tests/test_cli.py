from click.testing import CliRunner

from chatecnu.config import ECNUConfig
from chatecnu.cli import main
from chatecnu.ecnu.cli import format_network_auth_result, load_chatenv, redact_state
from chatecnu.network_auth import NetworkAuthResult


def test_help_lists_ecnu_commands():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "home" in result.output
    assert "net" in result.output
    assert "visitor" in result.output
    assert "status" not in result.output


def test_selftest_runs_without_network():
    result = CliRunner().invoke(main, ["selftest"])

    assert result.exit_code == 0
    assert '"ok": true' in result.output


def test_ecnu_config_loads_from_chatarch_envs(tmp_path, monkeypatch):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    env_file = tmp_path / "chatarch" / "envs" / "ECNU" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "ECNU_USERNAME='from-chatarch'\nECNU_PASSWORD='secret'\nECNU_BASE_URL='https://example.invalid'\n",
        encoding="utf-8",
    )

    load_chatenv()

    assert ECNUConfig.ECNU_USERNAME.value == "from-chatarch"
    assert ECNUConfig.ECNU_PASSWORD.value == "secret"
    assert ECNUConfig.ECNU_BASE_URL.value == "https://example.invalid"


def test_ecnu_config_test_does_not_raise(capsys):
    ECNUConfig.test()

    output = capsys.readouterr().out
    assert "Testing ECNU" in output
    assert "Config loaded" in output


def test_redact_state_masks_cookies_and_login_bootstrap_secrets():
    redacted = redact_state(
        {
            "cookies": {"PHPSESSID_8800": "secret-cookie"},
            "login_bootstrap": {"csrf_token": "secret-token", "csrf_param": "_csrf"},
        }
    )

    assert redacted["cookies"] == {"PHPSESSID_8800": "***"}
    assert redacted["login_bootstrap"]["csrf_token"] == "***"
    assert redacted["login_bootstrap"]["csrf_param"] == "***"


def test_format_network_auth_check_displays_login_info():
    result = NetworkAuthResult(
        action="check",
        success=True,
        returncode=0,
        stdout="Account 20260001 is online.\n",
        stderr='time="2026-08-05T04:11:52+08:00" level=info Online=true Username=20260001\n',
        redacted_command="auth_client check",
        online=True,
        account="20260001",
        username="20260001",
    )

    summary = format_network_auth_result(result)

    assert "auth_client OK." in summary
    assert "Online: true" in summary
    assert "Account: 20260001" in summary
    assert "Username: 20260001" in summary
