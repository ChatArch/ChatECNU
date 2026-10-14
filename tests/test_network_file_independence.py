"""The native backend must not depend on legacy binary/settings files."""
from pathlib import Path

import click
import pytest

from chatecnu.config import ECNUConfig
import chatecnu.ecnu.cli as cli
from chatecnu.network_http import PythonNetworkAuthClient


def prepare(monkeypatch):
    monkeypatch.setenv('ECNU_NETWORK_BACKEND', 'python')
    for name in ['ECNU_NETWORK_BACKEND', 'ECNU_AUTH_SETTING_FILE']:
        monkeypatch.setattr(getattr(ECNUConfig, name), 'value', None)
    for name in ['ECNU_NETWORK_BASE_URL', 'ECNU_NETWORK_AC_ID']:
        monkeypatch.delenv(name, raising=False)
        if hasattr(ECNUConfig, name):
            monkeypatch.setattr(getattr(ECNUConfig, name), 'value', None)


def test_native_default_ignores_missing_legacy_profile_setting(monkeypatch):
    prepare(monkeypatch)
    monkeypatch.setenv('ECNU_AUTH_SETTING_FILE', '/missing/legacy-auth-setting')
    monkeypatch.setattr(PythonNetworkAuthClient, 'from_setting_file', lambda *a, **k: pytest.fail('implicit legacy file read'))
    client = cli.make_network_auth_client(auth_client_path=None, setting_file=None)
    assert client.base_url == 'https://login.ecnu.edu.cn' and client.acid == 1


def test_native_default_ignores_existing_legacy_home_setting(monkeypatch, tmp_path):
    prepare(monkeypatch)
    monkeypatch.delenv('ECNU_AUTH_SETTING_FILE', raising=False)
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    (tmp_path/'.auth-setting').write_text('host="untrusted.example"\nacid="99"\n')
    client = cli.make_network_auth_client(auth_client_path=None, setting_file=None)
    assert client.base_url == 'https://login.ecnu.edu.cn' and client.acid == 1


def test_native_endpoint_uses_chatenv_values_without_legacy_import(monkeypatch):
    prepare(monkeypatch)
    monkeypatch.setenv('ECNU_AUTH_SETTING_FILE', '/missing/legacy-auth-setting')
    monkeypatch.setenv('ECNU_NETWORK_BASE_URL', 'https://portal.example')
    monkeypatch.setenv('ECNU_NETWORK_AC_ID', '7')
    client = cli.make_network_auth_client(auth_client_path=None, setting_file=None)
    assert client.base_url == 'https://portal.example' and client.acid == 7


@pytest.mark.parametrize('acid', ['0','-1','garbage','1.5'])
def test_native_invalid_ac_id_fails_before_network(monkeypatch, acid):
    prepare(monkeypatch)
    monkeypatch.setenv('ECNU_NETWORK_AC_ID', acid)
    with pytest.raises(click.ClickException):
        cli.make_network_auth_client(auth_client_path=None, setting_file=None)


def test_explicit_legacy_import_requires_filename():
    with pytest.raises(ValueError):
        PythonNetworkAuthClient.from_setting_file(None)
