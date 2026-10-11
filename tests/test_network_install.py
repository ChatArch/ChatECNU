"""Installer acceptance: real files, never execute the Linux helper."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from chatenv import EnvStore, get_paths
from chatecnu.config import ECNUConfig


def installer():
    assert importlib.util.find_spec('chatecnu.network_install') is not None, 'missing importable network installer API'
    from chatecnu import network_install
    return network_install


def test_fresh_install_creates_executable_config_and_legacy_entries(tmp_path, monkeypatch):
    api = installer()
    monkeypatch.setattr(api.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(api.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('CHATARCH_HOME', str(tmp_path / 'chatarch'))

    result = api.install_network_auth()
    data = result.to_dict()
    paths = api.state_paths()
    assert paths.root == get_paths().home_dir / 'chatecnu'
    assert paths.auth_client.read_bytes() == (Path(__file__).parents[1] / 'src/chatecnu/bin/linux-x86_64/auth_client').read_bytes()
    assert paths.auth_client.stat().st_mode & 0o111 == 0o111
    assert paths.auth_client.read_bytes().startswith(b'\x7fELF')
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    assert tomllib.loads(paths.setting_file.read_text()) == {'host': 'login.ecnu.edu.cn', 'acid': 1, 'campus_url': '', 'campus_postfix': ''}
    assert paths.legacy_auth_client.is_symlink()
    assert paths.legacy_setting_file.is_symlink()
    assert paths.legacy_auth_client.resolve() == paths.auth_client
    assert paths.legacy_setting_file.resolve() == paths.setting_file
    assert data['success'] is True and data['dry_run'] is False
    assert data['auth_client'] == str(paths.auth_client)
    assert data['setting_file'] == str(paths.setting_file)
    assert data['source'] == 'bundled-linux-x86_64'
    assert json.loads(json.dumps(data)) == data
    values = EnvStore(get_paths().envs_dir).load_active(ECNUConfig)
    assert values == {'ECNU_AUTH_CLIENT': str(paths.auth_client), 'ECNU_AUTH_SETTING_FILE': str(paths.setting_file)}


import pytest


@pytest.fixture
def linux_home(tmp_path, monkeypatch):
    api = installer()
    monkeypatch.setattr(api.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(api.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('CHATARCH_HOME', str(tmp_path / 'chatarch'))
    return api


def snapshot(root):
    return {str(p.relative_to(root)): (p.lstat().st_mode, p.lstat().st_mtime_ns, str(p.readlink()) if p.is_symlink() else p.read_bytes() if p.is_file() else None) for p in root.rglob('*')}


def seed_legacy(api):
    paths = api.state_paths()
    paths.legacy_auth_client.parent.mkdir(parents=True)
    paths.legacy_auth_client.write_bytes(b'#!/bin/sh\nexit 0\n')
    paths.legacy_auth_client.chmod(0o751)
    paths.legacy_setting_file.write_text('# custom settings\nhost="custom.invalid"\nacid=3\ncampus_url=""\ncampus_postfix=""\n')
    return paths


def test_legacy_string_acid_config_is_preserved(linux_home):
    paths = seed_legacy(linux_home)
    paths.legacy_setting_file.write_text('host="login.ecnu.edu.cn"\nacid="1"\ncampus_url=""\ncampus_postfix=""\n')
    original = paths.legacy_setting_file.read_bytes()
    result = linux_home.install_network_auth()
    assert result.setting_file == str(paths.legacy_setting_file)
    assert paths.legacy_setting_file.read_bytes() == original


def test_repeat_install_is_byte_mode_and_mtime_idempotent(linux_home, tmp_path):
    linux_home.install_network_auth()
    before = snapshot(tmp_path)
    result = linux_home.install_network_auth()
    assert snapshot(tmp_path) == before
    assert all(item['action'] == 'preserve' for item in result.actions)


def test_existing_legacy_files_are_preserved_and_selected(linux_home):
    paths = seed_legacy(linux_home)
    original = (paths.legacy_auth_client.read_bytes(), paths.legacy_setting_file.read_bytes())
    result = linux_home.install_network_auth(host='other.invalid', ac_id=9)
    assert (paths.legacy_auth_client.read_bytes(), paths.legacy_setting_file.read_bytes()) == original
    assert paths.legacy_auth_client.stat().st_mode & 0o777 == 0o751
    assert not paths.auth_client.exists() and not paths.setting_file.exists()
    assert result.auth_client == str(paths.legacy_auth_client)
    assert result.setting_file == str(paths.legacy_setting_file)
    assert result.source == 'existing-legacy'


def test_existing_legacy_symlinks_are_not_moved_or_replaced(linux_home, tmp_path):
    paths = seed_legacy(linux_home)
    external = tmp_path / 'external'
    paths.legacy_setting_file.rename(external)
    paths.legacy_setting_file.symlink_to(external)
    before = snapshot(tmp_path)
    linux_home.install_network_auth()
    assert paths.legacy_setting_file.is_symlink()
    assert paths.legacy_setting_file.readlink() == external
    assert snapshot(tmp_path)[str(external.relative_to(tmp_path))] == before[str(external.relative_to(tmp_path))]


def test_existing_managed_files_are_reused_without_rewrite(linux_home):
    paths = linux_home.state_paths()
    paths.auth_client.parent.mkdir(parents=True)
    paths.setting_file.parent.mkdir(parents=True)
    paths.auth_client.write_bytes(b'#!/bin/sh\nexit 0\n')
    paths.auth_client.chmod(0o700)
    paths.setting_file.write_text('host="managed.invalid"\nacid=7\ncampus_url=""\ncampus_postfix=""\n')
    before = (paths.auth_client.read_bytes(), paths.setting_file.read_bytes())
    result = linux_home.install_network_auth()
    assert (paths.auth_client.read_bytes(), paths.setting_file.read_bytes()) == before
    assert result.source == 'existing-managed'


def test_force_backs_up_original_regular_files(linux_home):
    paths = seed_legacy(linux_home)
    originals = {str(p): p.read_bytes() for p in (paths.legacy_auth_client, paths.legacy_setting_file)}
    result = linux_home.install_network_auth(force=True, host='forced.invalid', ac_id=2)
    backups = [a for a in result.actions if a['action'] == 'backup']
    assert len(backups) == 2
    for item in backups:
        backup = Path(item['backup'])
        assert backup.is_relative_to(paths.backups)
        assert backup.read_bytes() == originals[item['path']]
    assert paths.legacy_auth_client.is_symlink()
    assert paths.legacy_setting_file.is_symlink()
    assert 'forced.invalid' in paths.setting_file.read_text()


def test_force_backs_up_symlink_without_touching_unknown_target(linux_home, tmp_path):
    paths = seed_legacy(linux_home)
    target = tmp_path / 'unknown-config'
    paths.legacy_setting_file.rename(target)
    paths.legacy_setting_file.symlink_to(target)
    before = target.read_bytes()
    result = linux_home.install_network_auth(force=True)
    backup = next(Path(a['backup']) for a in result.actions if a['action'] == 'backup' and a['path'] == str(paths.legacy_setting_file))
    assert backup.is_symlink() and backup.readlink() == target
    assert target.read_bytes() == before


def test_force_backs_up_managed_files_and_preserves_old_backup(linux_home):
    paths = linux_home.state_paths()
    linux_home.install_network_auth()
    before = paths.setting_file.read_bytes()
    first = linux_home.install_network_auth(force=True, host='forced.invalid')
    old_backup = next(Path(a['backup']) for a in first.actions if a['action'] == 'backup' and a['path'] == str(paths.setting_file))
    assert old_backup.read_bytes() == before
    linux_home.install_network_auth(force=True, host='again.invalid')
    assert old_backup.read_bytes() == before


@pytest.mark.parametrize('existing', [False, True])
def test_dry_run_has_no_filesystem_side_effects(linux_home, tmp_path, existing):
    if existing:
        seed_legacy(linux_home)
    before = snapshot(tmp_path)
    result = linux_home.install_network_auth(dry_run=True, force=existing)
    assert snapshot(tmp_path) == before
    assert result.success is True and result.dry_run is True
    assert result.actions
    assert result.env_file.endswith('/envs/ECNU/.env')


@pytest.mark.parametrize(('system', 'machine'), [('Darwin', 'arm64'), ('Linux', 'aarch64'), ('Windows', 'AMD64')])
def test_unsupported_platform_fails_before_any_write(linux_home, monkeypatch, tmp_path, system, machine):
    monkeypatch.setattr(linux_home.platform, 'system', lambda: system)
    monkeypatch.setattr(linux_home.platform, 'machine', lambda: machine)
    before = snapshot(tmp_path)
    with pytest.raises(linux_home.NetworkInstallError, match='Linux x86_64'):
        linux_home.install_network_auth(force=True)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('conflict', ['root', 'bin-parent', 'legacy-binary', 'legacy-config', 'broken-link', 'env-dir', 'env-parent', 'symlink-parent'])
def test_path_conflicts_fail_before_writing(linux_home, tmp_path, conflict):
    paths = linux_home.state_paths()
    targets = {'root': paths.root, 'bin-parent': paths.auth_client.parent, 'legacy-binary': paths.legacy_auth_client, 'legacy-config': paths.legacy_setting_file, 'broken-link': paths.legacy_setting_file, 'env-dir': get_paths().envs_dir / 'ECNU/.env', 'env-parent': get_paths().envs_dir / 'ECNU', 'symlink-parent': paths.auth_client.parent}
    path = targets[conflict]
    path.parent.mkdir(parents=True, exist_ok=True)
    if conflict in ['legacy-binary', 'legacy-config', 'env-dir']:
        path.mkdir()
    elif conflict == 'broken-link':
        path.symlink_to(tmp_path / 'missing')
    elif conflict == 'symlink-parent':
        external = tmp_path / 'external-dir'
        external.mkdir()
        path.symlink_to(external)
    else:
        path.write_bytes(b'conflict')
    before = snapshot(tmp_path)
    with pytest.raises(linux_home.NetworkInstallError):
        linux_home.install_network_auth()
    assert snapshot(tmp_path) == before


def test_force_does_not_replace_directories(linux_home, tmp_path):
    paths = linux_home.state_paths()
    paths.legacy_setting_file.mkdir(parents=True)
    before = snapshot(tmp_path)
    with pytest.raises(linux_home.NetworkInstallError):
        linux_home.install_network_auth(force=True)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('kind', ['binary', 'config'])
def test_unusable_legacy_file_requires_explicit_force(linux_home, tmp_path, kind):
    paths = seed_legacy(linux_home)
    if kind == 'binary':
        paths.legacy_auth_client.chmod(0o600)
    else:
        paths.legacy_setting_file.write_text('not TOML [')
    before = snapshot(tmp_path)
    with pytest.raises(linux_home.NetworkInstallError, match='--force'):
        linux_home.install_network_auth()
    assert snapshot(tmp_path) == before
    linux_home.install_network_auth(force=True)
    assert paths.legacy_setting_file.is_symlink()


def test_active_chatenv_credentials_and_unknown_values_preserved(linux_home, monkeypatch):
    store = EnvStore(get_paths().envs_dir)
    existing = {'ECNU_USERNAME': 'fixture-user', 'ECNU_PASSWORD': 'fixture-password', 'ECNU_VISITOR_PASSWORD1': 'fixture-visitor', 'ECNU_BASE_URL': 'https://example.invalid', 'OTHER_VALUE': 'keep'}
    store.save_active(ECNUConfig, existing)
    monkeypatch.setenv('ECNU_PASSWORD', 'must-not-write-process-secret')
    result = linux_home.install_network_auth()
    after = store.load_active(ECNUConfig)
    assert {k: after[k] for k in existing} == existing
    assert set(after) == set(existing) | {'ECNU_AUTH_CLIENT', 'ECNU_AUTH_SETTING_FILE'}
    assert 'fixture-password' not in json.dumps(result.to_dict())
    assert 'must-not-write-process-secret' not in json.dumps(result.to_dict())


def test_named_profile_is_updated_without_global_activation(linux_home):
    store = EnvStore(get_paths().envs_dir)
    store.save_active(ECNUConfig, {'ECNU_PASSWORD': 'active-fixture'})
    store.save_profile(ECNUConfig, 'named', {'ECNU_PASSWORD': 'named-fixture', 'EXTRA': 'keep'})
    active = store.active_path(ECNUConfig).read_bytes()
    result = linux_home.install_network_auth(env_profile='named')
    assert store.active_path(ECNUConfig).read_bytes() == active
    assert store.load_profile(ECNUConfig, 'named')['ECNU_PASSWORD'] == 'named-fixture'
    assert store.load_profile(ECNUConfig, 'named')['EXTRA'] == 'keep'
    assert result.env_profile == 'named'
    assert result.env_file == str(store.profile_path(ECNUConfig, 'named'))


def test_invalid_named_profile_fails_before_filesystem_writes(linux_home, tmp_path):
    before = snapshot(tmp_path)
    with pytest.raises((linux_home.NetworkInstallError, ValueError)):
        linux_home.install_network_auth(env_profile='../outside')
    assert snapshot(tmp_path) == before


def test_custom_endpoint_is_valid_toml(linux_home):
    result = linux_home.install_network_auth(host='custom.invalid:8080', ac_id=3, campus_url='https://example.invalid/a?q="text"', campus_postfix='@campus')
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    assert tomllib.loads(Path(result.setting_file).read_text()) == {'host': 'custom.invalid:8080', 'acid': 3, 'campus_url': 'https://example.invalid/a?q="text"', 'campus_postfix': '@campus'}


@pytest.mark.parametrize('kwargs', [{'host': ''}, {'host': 'https://example.invalid'}, {'host': 'user:secret@example.invalid'}, {'host': 'example.invalid/password'}, {'ac_id': 0}, {'ac_id': True}, {'campus_url': 'javascript:alert(1)'}, {'campus_postfix': '\nmalformed'}])
def test_bad_endpoint_input_fails_before_any_write(linux_home, tmp_path, kwargs):
    before = snapshot(tmp_path)
    with pytest.raises(linux_home.NetworkInstallError):
        linux_home.install_network_auth(**kwargs)
    assert snapshot(tmp_path) == before


def test_profile_readback_failure_restores_original_credentials(linux_home, monkeypatch):
    store = EnvStore(get_paths().envs_dir)
    store.save_active(ECNUConfig, {'ECNU_PASSWORD': 'fixture-preserve', 'EXTRA': 'keep'})
    target = store.active_path(ECNUConfig)
    original = target.read_bytes()
    original_mode = target.stat().st_mode
    real_save = EnvStore.save_active

    def broken_save(self, config_cls, values):
        altered = dict(values, ECNU_PASSWORD='fixture-corrupted')
        return real_save(self, config_cls, altered)

    monkeypatch.setattr(EnvStore, 'save_active', broken_save)
    with pytest.raises(linux_home.NetworkInstallError, match='readback'):
        linux_home.install_network_auth()
    assert target.read_bytes() == original
    assert target.stat().st_mode == original_mode


def test_profile_save_io_failure_restores_original_bytes(linux_home, monkeypatch):
    store = EnvStore(get_paths().envs_dir)
    target = store.save_active(ECNUConfig, {'ECNU_PASSWORD': 'fixture-preserve'})
    original = target.read_bytes()

    def failed_save(self, config_cls, values):
        self.active_path(config_cls).write_bytes(b'partial-write')
        raise OSError('fixture write failure')

    monkeypatch.setattr(EnvStore, 'save_active', failed_save)
    with pytest.raises(OSError, match='fixture write failure'):
        linux_home.install_network_auth()
    assert target.read_bytes() == original
