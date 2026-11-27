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
    monkeypatch.setattr(watch, "current_route_interface", lambda: "en1")
    session = Mock()
    client = Mock()
    client.check.return_value = SimpleNamespace(success=True, online=True, username="fixture")
    client.login.return_value = SimpleNamespace(success=True, online=True)
    monkeypatch.setattr(watch.requests, "Session", lambda: session)
    monkeypatch.setattr(watch, "PythonNetworkAuthClient", lambda *a, **k: client)
    calls = []

    def launchctl(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1 if args[0] == "print" else 0)

    monkeypatch.setattr(watch, "launchctl", launchctl)
    return session, client, calls


def install(**kwargs):
    return watch.install_service(base_url="https://portal.example", ac_id=1, **kwargs)


def test_dry_run_is_write_free(setup, tmp_path):
    result = install(dry_run=True)
    assert result["dry_run"] and result["interval_seconds"] == 60
    assert result["credential_source"] == "ChatEnv ECNU profile"
    assert list(tmp_path.iterdir()) == []
    assert setup[2] == []


def test_service_uses_package_and_named_profile(setup):
    result = install(env_profile="rex")
    job = plistlib.loads(Path(result["plist"]).read_bytes())
    assert job["ProgramArguments"][1:] == ["-m", "chatecnu", "-e", "rex", "net", "ensure-login", "--service-run", "--json", "-I"]
    assert job["StartInterval"] == 60 and job["RunAtLoad"]
    assert "password" not in json.dumps(job).lower()
    config = watch.load_json(watch.paths()["config"])
    assert set(config) == {"ac_id", "base_url", "check_interval_seconds", "env_profile", "probe_url", "request_timeout", "required_failed_checks", "retry_cooldown_seconds"}
    assert not (watch.paths()["root"] / "agent.py").exists()
    assert ("bootstrap", f"gui/{os.getuid()}", result["plist"]) in setup[2]


def test_old_standalone_job_is_backed_up_and_migrated(setup):
    target = watch.paths()
    target["root"].mkdir(parents=True)
    target["plist"].parent.mkdir(parents=True)
    old = {"Label": watch.LABEL, "ProgramArguments": ["python", str(target["root"] / "agent.py")]}
    target["plist"].write_bytes(plistlib.dumps(old))
    target["config"].write_text(json.dumps({"username": "stale", "keychain_service": watch.LABEL}))
    result = install()
    assert result["credential_source"] == "ChatEnv ECNU profile"
    config = watch.load_json(target["config"])
    assert "username" not in config and "keychain_service" not in config
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


def test_uninstall_preserves_configuration(setup):
    install()
    original = watch.paths()["config"].read_bytes()
    result = watch.uninstall_service()
    assert not watch.paths()["plist"].exists()
    assert watch.paths()["config"].read_bytes() == original
    assert result["credential_source"] == "ChatEnv ECNU profile"


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
        watch.install_service(base_url=url, ac_id=1)
    assert not watch.paths()["root"].exists()


@pytest.mark.parametrize("system", ["Linux", "Windows"])
def test_unsupported_platform_fails_before_writes(tmp_path, monkeypatch, system):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "missing"))
    monkeypatch.setattr(watch.platform, "system", lambda: system)
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--json"])
    assert result.exit_code == 1 and "macOS" in json.loads(result.output)["error"]
    assert list(tmp_path.iterdir()) == []


def test_service_actions_are_mutually_exclusive():
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--service-status"])
    assert result.exit_code == 2 and "one service action" in result.output


def test_install_no_longer_requires_interface_or_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    monkeypatch.setattr(watch.platform, "system", lambda: "Linux")
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--dry-run", "--json"])
    assert result.exit_code == 1
    assert "macOS" in json.loads(result.output)["error"]


def test_service_cannot_accept_explicit_credentials():
    result = CliRunner().invoke(main, ["net", "ensure-login", "--install-service", "--username", "SECRET_CANARY", "--password", "SECRET_PASSWORD"])
    assert result.exit_code == 2
    assert "SECRET_CANARY" not in result.output and "SECRET_PASSWORD" not in result.output


def test_service_does_not_store_a_username_snapshot(setup):
    result = install(env_profile="rex")
    config = watch.load_json(watch.paths()["config"])
    assert result["credential_source"] == "ChatEnv ECNU profile"
    assert "username" not in config and "keychain_service" not in config


@pytest.mark.parametrize("online,internet,success,previous,expected", [
    (True, True, True, {}, "online"),
    (True, False, True, {}, "authenticated_network_problem"),
    (False, True, True, {}, "online"),
    (False, False, True, {}, "offline_confirming"),
    (None, False, False, {"failed_checks": 3}, "authentication_status_unknown"),
    (False, False, True, {"failed_checks": 1, "last_login_attempt": 990}, "login_cooldown"),
])
def test_recovery_decisions_do_not_login_without_confirmed_outage(setup, monkeypatch, online, internet, success, previous, expected):
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


@pytest.mark.parametrize("credentials,expected", [(None, "credentials_missing"), (("fixture", "SECRET_CANARY"), "reconnected")])
def test_confirmed_outage_uses_chat_env_credentials(setup, monkeypatch, credentials, expected):
    install()
    config = watch.load_json(watch.paths()["config"])
    client = setup[1]
    client.check.return_value = SimpleNamespace(success=True, online=False, username=None)
    monkeypatch.setattr(watch, "internet_probe", Mock(side_effect=[False, True]))
    result = watch.check_once(config, {"failed_checks": 1}, lambda _: credentials, state_path=watch.paths()["state"])
    assert result["status"] == expected
    assert "SECRET_CANARY" not in json.dumps(result)
    if credentials:
        client.login.assert_called_once_with(NetworkAuthCredentials("fixture", "SECRET_CANARY"))
        assert watch.load_json(watch.paths()["state"])["status"] == "login_in_progress"
    else:
        client.login.assert_not_called()


def test_service_status_reports_system_route_and_chat_env(setup):
    install(env_profile="rex")
    result = watch.service_status()
    assert result["credential_source"] == "ChatEnv ECNU profile"
    assert result["chat_env_profile"] == "rex"
    assert result["current_interface"] == "en1"


def test_authentication_exception_retains_retry_cooldown(setup, monkeypatch):
    install()
    setup[1].check.return_value = SimpleNamespace(success=True, online=False, username=None)
    setup[1].login.side_effect = RuntimeError("SECRET_CANARY")
    monkeypatch.setattr(watch, "internet_probe", lambda *a: False)
    watch.write_json(watch.paths()["state"], {"failed_checks": 1})
    result = watch.run_service(lambda _: ("fixture", "SECRET_CANARY"))
    assert result["status"] == "check_error"
    assert "SECRET_CANARY" not in json.dumps(result)


def test_lock_prevents_overlapping_service_runs(setup):
    import fcntl

    install()
    with (watch.paths()["root"] / "check.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert watch.run_service(Mock())["status"] == "already_checking"
