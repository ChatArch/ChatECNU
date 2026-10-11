"""Thin adapter contracts; tests use real filesystem and EnvStore."""
from pathlib import Path
import json

from click.testing import CliRunner
from chatenv import EnvStore, get_paths
from chatecnu.cli import main
from chatecnu.config import ECNUConfig
from chatecnu import network_install as api


def isolate(tmp_path, monkeypatch, *, system='Linux'):
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('CHATARCH_HOME', str(tmp_path / 'chatarch'))
    monkeypatch.setattr(api.platform, 'system', lambda: system)
    monkeypatch.setattr(api.platform, 'machine', lambda: 'x86_64')


def test_install_visible_in_tree_and_has_no_credential_options():
    result = CliRunner().invoke(main, ['--tree'])
    assert result.exit_code == 0
    assert '│   ├── install ' in result.output
    help_result = CliRunner().invoke(main, ['net', 'install', '--help'])
    assert help_result.exit_code == 0
    for option in ['--host', '--ac-id', '--campus-url', '--campus-postfix', '--force', '--dry-run', '--json']:
        assert option in help_result.output
    assert '--password' not in help_result.output and '--username' not in help_result.output


def test_cli_json_reads_back_created_files_and_named_profile(tmp_path, monkeypatch):
    isolate(tmp_path, monkeypatch)
    store = EnvStore(get_paths().envs_dir)
    store.save_active(ECNUConfig, {'ECNU_PASSWORD': 'active-fixture'})
    store.save_profile(ECNUConfig, 'named', {'ECNU_PASSWORD': 'named-fixture'})
    active = store.active_path(ECNUConfig).read_bytes()
    result = CliRunner().invoke(main, ['-e', 'named', 'net', 'install', '--host', 'cli.invalid', '--ac-id', '5', '--json'])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data['success'] is True and data['env_profile'] == 'named'
    assert Path(data['auth_client']).is_file()
    assert Path(data['setting_file']).is_file()
    assert 'cli.invalid' in Path(data['setting_file']).read_text()
    assert store.load_profile(ECNUConfig, 'named')['ECNU_AUTH_CLIENT'] == data['auth_client']
    assert store.active_path(ECNUConfig).read_bytes() == active
    assert 'named-fixture' not in result.output and 'active-fixture' not in result.output


def test_cli_dry_run_does_not_create_home_or_profiles(tmp_path, monkeypatch):
    isolate(tmp_path, monkeypatch)
    result = CliRunner().invoke(main, ['net', 'install', '--dry-run', '--json'])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)['dry_run'] is True
    assert list(tmp_path.iterdir()) == []


def test_cli_unsupported_platform_fails_without_write_and_json_is_parseable(tmp_path, monkeypatch):
    isolate(tmp_path, monkeypatch, system='Darwin')
    result = CliRunner().invoke(main, ['net', 'install', '--json'])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data['success'] is False and 'Linux x86_64' in data['error']
    assert list(tmp_path.iterdir()) == []


def test_cli_human_output_shows_paths_not_login_success(tmp_path, monkeypatch):
    isolate(tmp_path, monkeypatch)
    result = CliRunner().invoke(main, ['net', 'install'])
    assert result.exit_code == 0, result.output
    assert str(api.state_paths().auth_client) in result.output
    assert str(api.state_paths().setting_file) in result.output
    assert 'Login success' not in result.output


def test_hidden_env_file_override_rejected_instead_of_ignored(tmp_path, monkeypatch):
    isolate(tmp_path, monkeypatch)
    result = CliRunner().invoke(main, ['--env-file', str(tmp_path / 'outside.env'), 'net', 'install', '--json'])
    assert result.exit_code != 0
    assert '--env-file' in result.output
    assert list(tmp_path.iterdir()) == []


def test_cli_invalid_ac_id_rejected_before_any_write(tmp_path, monkeypatch):
    isolate(tmp_path, monkeypatch)
    result = CliRunner().invoke(main, ['net', 'install', '--ac-id', '0'])
    assert result.exit_code != 0
    assert list(tmp_path.iterdir()) == []
