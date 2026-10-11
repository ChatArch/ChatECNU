"""Doc-first installer contracts including exact registered command tree."""
from pathlib import Path
from click.testing import CliRunner
from chatecnu.cli import main


def test_readmes_and_cli_docs_embed_the_actual_tree():
    result = CliRunner().invoke(main, ['--tree'])
    assert result.exit_code == 0
    for name in ['README.md', 'README.en.md', 'docs/cli-tree.md', 'docs/cli-tree.en.md']:
        assert result.output.strip() in Path(name).read_text(), name


def test_bilingual_setup_docs_cover_explicit_install_and_safe_boundaries():
    for name in ['README.md', 'README.en.md', 'docs/quickstart.md', 'docs/quickstart.en.md', 'docs/ecnu.md', 'docs/ecnu.en.md']:
        text = Path(name).read_text()
        for term in ['ecnu net install', '--dry-run', '--force', 'Linux x86_64', '~/.auth-setting', '~/.local/bin/auth_client']:
            assert term in text, (name, term)
    for name in ['docs/interface-tree.md', 'docs/interface-tree.en.md']:
        assert 'install_network_auth' in Path(name).read_text()
        assert 'state_paths' in Path(name).read_text()
