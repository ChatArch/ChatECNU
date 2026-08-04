from chatecnu import __version__


def test_version_present():
    assert __version__ == "0.2.1"


def test_cli_version_option():
    from click.testing import CliRunner
    from chatecnu.cli import main

    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "0.2.1" in result.output
