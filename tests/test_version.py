from chatecnu import __version__


def test_version_present():
    assert __version__ == "0.2.8"


def test_cli_version_option():
    from click.testing import CliRunner
    from chatecnu.cli import main

    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip().endswith(", version 0.2.8")


def test_shared_runtime_dependencies_and_refresh_provider_entry_point_declared():
    from pathlib import Path

    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert '"ChatNet>=0.2.4,<0.3.0"' in pyproject
    assert '"chatstyle>=0.2.0,<0.3.0"' in pyproject
    assert '"chatenv>=0.2.13,<0.3.0"' in pyproject
    assert 'ecnu = "chatecnu.cli:main"' in pyproject
    assert 'chatecnu = "chatecnu.cli:main"' in pyproject
    assert '[project.entry-points."chatenv.token_refreshers"]' in pyproject
    assert 'ECNU = "chatecnu.ecnu.session_tokens:refresh_chatenv_token"' in pyproject
