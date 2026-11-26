from __future__ import annotations

import json
import os
from pathlib import Path
import plistlib
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

from click.testing import CliRunner
import pytest

from chatecnu import network_watch as watch
from chatecnu.cli import main
from chatecnu.network_auth import NetworkAuthCredentials


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    monkeypatch.setattr(watch.platform, "system", lambda: "Darwin")
    info = {"interface": "en1", "source_ip": "192.0.2.2", "router_ip": "192.0.2.1", "dns_servers": ["192.0.2.53"]}
    monkeypatch.setattr(watch, "interface_info", lambda _: info.copy())
    monkeypatch.setattr(watch, "router_mac", lambda *a: "00:11:22:33:44:55")
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(watch, "interface_session", lambda _: session)
    client = Mock()
    client.check.return_value = SimpleNamespace(success=True, online=True, username="fixture")
    client.login.return_value = SimpleNamespace(success=True, online=True)
    monkeypatch.setattr(watch, "PythonNetworkAuthClient", lambda *a, **k: client)
    calls = []

    def launchctl(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1 if args[0] == "print" else 0)

    monkeypatch.setattr(watch, "launchctl", launchctl)
    return info, client, calls


def install(**kwargs):
    return watch.install_service(interface="en1", base_url="https://portal.example", ac_id=1,
                                 username="fixture", **kwargs)


def test_dry_run_is_write_free(setup, tmp_path):
    result = install(dry_run=True)
    assert result["dry_run"] and result["interval_seconds"] == 60
    assert list(tmp_path.iterdir()) == []
    assert setup[2] == []


def test_service_uses_package_and_preserves_named_profile(setup):
    result = install(env_profile="campus")
    job = plistlib.loads(Path(result["plist"]).read_bytes())
    assert job["ProgramArguments"][1:] == ["-m", "chatecnu", "-e", "campus", "net", "ensure-login", "--service-run", "--json", "-I"]
    assert job["StartInterval"] == 60 and job["RunAtLoad"]
    assert "password" not in json.dumps(job).lower()
    assert watch.paths()["config"].stat().st_mode & 0o777 == 0o600
    assert not (watch.paths()["root"] / "agent.py").exists()
    assert ("bootstrap", f"gui/{os.getuid()}", result["plist"]) in setup[2]


def test_old_standalone_job_is_backed_up_and_migrated(setup):
    target = watch.paths()
    target["root"].mkdir(parents=True)
    target["plist"].parent.mkdir(parents=True)
    old = {"Label": watch.LABEL, "ProgramArguments": ["python", str(target["root"] / "agent.py")]}
    target["plist"].write_bytes(plistlib.dumps(old))
    target["config"].write_text(json.dumps({"username": "fixture", "credentials_configured": True}))
    result = install()
    assert result["credentials_configured"]
    backups = list(target["root"].glob("service-backup-*"))
    assert len(backups) == 1
    assert plistlib.loads((backups[0] / target["plist"].name).read_bytes()) == old


def test_failed_bootstrap_restores_old_files(setup, monkeypatch):
    install()
    target = watch.paths()
    original = {name: target[name].read_bytes() for name in ["config", "plist"]}

    def fail(*args, **kwargs):
        if args[0] == "bootstrap":
            raise ValueError("fixture launch failure")
        return subprocess.CompletedProcess(args, 1)

    monkeypatch.setattr(watch, "launchctl", fail)
    with pytest.raises(ValueError, match="fixture launch failure"):
        install(interval=120)
    assert {name: target[name].read_bytes() for name in original} == original


def test_uninstall_preserves_credentials_and_configuration(setup):
    install()
    original = watch.paths()["config"].read_bytes()
    watch.uninstall_service()
    assert not watch.paths()["plist"].exists()
    assert watch.paths()["config"].read_bytes() == original


def test_unrelated_job_is_not_overwritten_or_removed(setup):
    path = watch.paths()["plist"]
    path.parent.mkdir(parents=True)
    path.write_bytes(plistlib.dumps({"Label": watch.LABEL, "ProgramArguments": ["unrelated"]}))
    original = path.read_bytes()
    for action in [install, watch.uninstall_service]:
        with pytest.raises(ValueError, match="unrelated"):
            action()
        assert path.read_bytes() == original


@pytest.mark.parametrize("url", ["http://portal.example", "https://user:secret@portal.example", "https://portal.example/?secret=canary"])
def test_service_requires_https_urls_without_embedded_credentials(setup, url):
    with pytest.raises(ValueError, match="HTTPS"):
        watch.install_service(interface="en1", base_url=url, ac_id=1, username="fixture")
    assert not watch.paths()["root"].exists()


@pytest.mark.parametrize("system", ["Linux", "Windows"])
def test_unsupported_platform_fails_before_writes(tmp_path, monkeypatch, system):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "missing"))
    monkeypatch.setattr(watch.platform, "system", lambda: system)
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--interface", "en1", "--json"])
    assert result.exit_code == 1 and "macOS" in json.loads(result.output)["error"]
    assert list(tmp_path.iterdir()) == []


def test_service_actions_are_mutually_exclusive():
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--service-status"])
    assert result.exit_code == 2 and "one service action" in result.output


def test_install_requires_interface_without_resolving_credentials():
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service"])
    assert result.exit_code == 2 and "requires --interface" in result.output


def test_save_password_refuses_noninteractive_input(setup):
    install()
    result = CliRunner().invoke(main, ["net", "ensure-login", "--save-password", "-I"])
    assert result.exit_code == 2 and "local interactive terminal" in result.output


def test_service_cannot_accept_argv_password():
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--interface", "en1", "--password", "SECRET_CANARY"])
    assert result.exit_code == 2 and "SECRET_CANARY" not in result.output


@pytest.mark.parametrize("online,internet,success,previous,expected", [
    (True, True, True, {}, "online"),
    (True, False, True, {}, "authenticated_network_problem"),
    (False, True, True, {}, "online"),
    (False, False, True, {}, "offline_confirming"),
    (None, False, False, {"failed_checks": 3}, "authentication_status_unknown"),
    (False, False, True, {"failed_checks": 1, "last_login_attempt": 990}, "login_cooldown"),
])
def test_recovery_does_not_login_without_confirmed_outage(setup, monkeypatch, online, internet, success, previous, expected):
    install()
    config = watch.load_json(watch.paths()["config"])
    client = setup[1]
    client.check.return_value = SimpleNamespace(success=success, online=online, username="fixture" if online else None)
    monkeypatch.setattr(watch.time, "time", lambda: 1000)
    monkeypatch.setattr(watch, "internet_probe", lambda *a: internet)
    loader = Mock()
    result = watch.check_once(config, previous, loader, state_path=watch.paths()["state"])
    assert result["status"] == expected
    client.login.assert_not_called()
    loader.assert_not_called()


@pytest.mark.parametrize("password,expected", [(None, "credentials_missing"), ("SECRET_CANARY", "reconnected")])
def test_confirmed_outage_uses_credentials_without_exposing_them(setup, monkeypatch, password, expected):
    install()
    config = watch.load_json(watch.paths()["config"])
    client = setup[1]
    client.check.return_value = SimpleNamespace(success=True, online=False, username=None)
    monkeypatch.setattr(watch, "internet_probe", Mock(side_effect=[False, True]))
    result = watch.check_once(config, {"failed_checks": 1}, lambda _: password, state_path=watch.paths()["state"])
    assert result["status"] == expected
    assert "SECRET_CANARY" not in json.dumps(result)
    if password:
        client.login.assert_called_once_with(NetworkAuthCredentials("fixture", password))
        assert watch.load_json(watch.paths()["state"])["status"] == "login_in_progress"
    else:
        client.login.assert_not_called()


def test_another_router_is_ignored_before_network_or_credentials(setup, monkeypatch):
    install()
    setup[1].reset_mock()
    config = watch.load_json(watch.paths()["config"])
    monkeypatch.setattr(watch, "router_mac", lambda *a: "00:00:00:00:00:01")
    loader = Mock()
    result = watch.check_once(config, {}, loader, state_path=watch.paths()["state"])
    assert result["status"] == "different_network"
    setup[1].check.assert_not_called()
    loader.assert_not_called()


def test_locked_keychain_does_not_attempt_login(setup, monkeypatch):
    install()
    config = watch.load_json(watch.paths()["config"])
    setup[1].check.return_value = SimpleNamespace(success=True, online=False, username=None)
    monkeypatch.setattr(watch, "internet_probe", lambda *a: False)
    loader = Mock(side_effect=watch.KeychainError("locked"))
    result = watch.check_once(config, {"failed_checks": 1}, loader, state_path=watch.paths()["state"])
    assert result["status"] == "credentials_locked"
    setup[1].login.assert_not_called()


def test_authentication_exception_retains_retry_cooldown(setup, monkeypatch):
    install()
    setup[1].check.return_value = SimpleNamespace(success=True, online=False, username=None)
    setup[1].login.side_effect = RuntimeError("SECRET_CANARY")
    monkeypatch.setattr(watch, "internet_probe", lambda *a: False)
    watch.write_json(watch.paths()["state"], {"failed_checks": 1})
    result = watch.run_service(lambda _: "SECRET_CANARY")
    assert result["status"] == "check_error" and result["last_login_attempt"] > 0
    assert "SECRET_CANARY" not in json.dumps(result)


def test_options_for_install_are_not_silently_ignored():
    result = CliRunner().invoke(main, ["net", "ensure-login", "--interval", "60"])
    assert result.exit_code == 2 and "require --install-service" in result.output


def test_lock_prevents_overlapping_service_runs(setup):
    import fcntl

    install()
    with (watch.paths()["root"] / "check.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert watch.run_service(Mock())["status"] == "already_checking"


def test_service_docs_use_existing_command_without_new_entrypoint():
    for name in ["README.md", "README.en.md", "docs/ecnu.md", "docs/ecnu.en.md"]:
        text = Path(name).read_text()
        for term in ["--install-service", "--interface en1", "--service-status", "--save-password", "--uninstall-service"]:
            assert term in text, (name, term)
    manifest = Path("pyproject.toml").read_text()
    assert "ecnu-wifi-autologin" not in manifest
