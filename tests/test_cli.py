from click.testing import CliRunner

from chatnet.config import ECNUConfig
from chatnet.cli import main
from chatnet.ecnu.cli import load_chatenv


def test_help_lists_ecnu_group():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "ecnu" in result.output


def test_ecnu_selftest_runs_without_network():
    result = CliRunner().invoke(main, ["ecnu", "selftest"])

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
