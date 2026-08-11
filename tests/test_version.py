from chatecnu import __version__


def test_version_present():
    assert __version__ == "0.2.4"


def test_cli_version_option():
    from click.testing import CliRunner
    from chatecnu.cli import main

    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "0.2.4" in result.output


def test_chatenv_dependency_and_refresh_provider_entry_point_declared():
    from pathlib import Path

    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert '"chatenv>=0.2.7,<0.3.0"' in pyproject
    assert '[project.entry-points."chatenv.token_refreshers"]' in pyproject
    assert 'ECNU = "chatecnu.ecnu.session_tokens:refresh_chatenv_token"' in pyproject
