"""macOS user service for automatic campus-network reauthentication.

Credentials are read from the selected ChatEnv ECNU profile on every run. The
service follows the system routing table; it does not pin a network interface.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

import requests
from chatenv.paths import get_paths

from .network_auth import NetworkAuthCredentials
from .network_http import PythonNetworkAuthClient

LABEL = "com.chatarch.ecnu.wifi-autologin"


def paths() -> dict[str, Path]:
    root = get_paths().home_dir / "chatecnu/wifi-autologin"
    return {"root": root, "config": root / "config.json", "state": root / "state.json",
            "plist": Path.home() / "Library/LaunchAgents" / (LABEL + ".plist")}


def require_macos() -> None:
    if platform.system() != "Darwin":
        raise ValueError("Automatic login user services currently support macOS only.")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, OSError, ValueError):
        return {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise ValueError("Refusing a symlink service file.")
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".update-")
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(data, output, indent=2, sort_keys=True)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def current_route_interface() -> str | None:
    """Return the interface selected by macOS for the default route."""
    try:
        result = subprocess.run(["/sbin/route", "-n", "get", "default"],
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    match = re.search(r"^\s*interface:\s*(\S+)", result.stdout, re.MULTILINE)
    return match.group(1) if match else None


def login_decision(internet: bool, success: bool, online, failures: int,
                   required: int, last_attempt: float, now: float, cooldown: int) -> str:
    if internet:
        return "online"
    if not success:
        return "authentication_status_unknown"
    if online is True:
        return "authenticated_network_problem"
    if online is not False:
        return "authentication_status_unknown"
    if failures < required:
        return "offline_confirming"
    if last_attempt and now - last_attempt < cooldown:
        return "login_cooldown"
    return "login_needed"


def internet_probe(session, config: dict) -> bool:
    try:
        with session.get(config["probe_url"], timeout=(3, config["request_timeout"]),
                         allow_redirects=False, stream=True) as response:
            return 200 <= response.status_code < 400
    except requests.RequestException:
        return False


def check_once(config: dict, previous: dict, credentials_loader, *, state_path: Path) -> dict:
    now = time.time()
    result = {"checked_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
              "interface": current_route_interface(),
              "last_login_attempt": previous.get("last_login_attempt", 0),
              "failed_checks": 0, "login_attempted": False}
    session = requests.Session()
    session.trust_env = False
    client = PythonNetworkAuthClient(config["base_url"], acid=config["ac_id"],
                                     session=session, timeout=config["request_timeout"])
    try:
        status = client.check()
        internet = internet_probe(session, config)
        failures = previous.get("failed_checks", 0) + 1 if status.success and status.online is False and not internet else 0
        result.update(campus_authenticated=status.online if status.success else None,
                      external_reachable=internet, failed_checks=failures,
                      account_present=bool(status.username))
        decision = login_decision(internet, status.success, status.online, failures,
                                  config["required_failed_checks"], result["last_login_attempt"],
                                  now, config["retry_cooldown_seconds"])
        if decision != "login_needed":
            return dict(result, status=decision)
        try:
            credentials = credentials_loader(config)
        except (KeyError, TypeError, ValueError):
            credentials = None
        if not credentials or not credentials[0] or not credentials[1]:
            return dict(result, status="credentials_missing")
        username, password = credentials
        result.update(login_attempted=True, last_login_attempt=now)
        write_json(state_path, dict(result, status="login_in_progress"))
        login = client.login(NetworkAuthCredentials(username=username, password=password))
        if not login.success or login.online is not True:
            return dict(result, status="login_failed", campus_authenticated=login.online)
        result.update(campus_authenticated=True, failed_checks=0,
                      external_reachable=internet_probe(session, config))
        return dict(result, status="reconnected" if result["external_reachable"] else "authenticated_network_problem")
    finally:
        session.close()


def run_service(credentials_loader) -> dict:
    require_macos()
    import fcntl

    target = paths()
    config = load_json(target["config"])
    if not config:
        raise ValueError("No automatic login service is installed.")
    with (target["root"] / "check.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"success": True, "status": "already_checking"}
        previous = load_json(target["state"])
        try:
            result = check_once(config, previous, credentials_loader, state_path=target["state"])
        except Exception as exc:
            result = dict(load_json(target["state"]) or previous, status="check_error",
                          login_attempted=False, error_type=type(exc).__name__,
                          checked_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        write_json(target["state"], result)
        return result


def launchctl(*args: str, allow_missing: bool = False) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(["/bin/launchctl", *args], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        raise ValueError("User service operation timed out.") from None
    if result.returncode and not allow_missing:
        raise ValueError("User service operation failed; inspect launchctl for details.")
    return result


def service_status() -> dict:
    require_macos()
    target = paths()
    loaded = launchctl("print", f"gui/{os.getuid()}/{LABEL}", allow_missing=True).returncode == 0
    config = load_json(target["config"])
    return {"success": True, "installed": target["plist"].is_file(), "loaded": loaded,
            "interval_seconds": config.get("check_interval_seconds"),
            "credential_source": "ChatEnv ECNU profile",
            "chat_env_profile": config.get("env_profile") or "active",
            "current_interface": current_route_interface(),
            "last_check": load_json(target["state"])}


def owned_plist(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return False
    if not path.exists():
        return True
    try:
        data = plistlib.loads(path.read_bytes())
        args = data.get("ProgramArguments", [])
        return data.get("Label") == LABEL and (
            args[1:] == [str(root / "agent.py")] or
            (args[1:3] == ["-m", "chatecnu"] and "--service-run" in args))
    except (OSError, ValueError, plistlib.InvalidFileException):
        return False


def install_service(*, base_url: str, ac_id: int, env_profile: str | None = None,
                    interval: int = 60, probe_url: str = "https://www.baidu.com/",
                    dry_run: bool = False) -> dict:
    require_macos()
    if type(interval) is not int or not 15 <= interval <= 86400:
        raise ValueError("Service interval must be between 15 and 86400 seconds.")
    for url in [base_url, probe_url]:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
            raise ValueError("Service URLs must use HTTPS without credentials, query or fragment.")
    target = paths()
    for path in target.values():
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError("Refusing a symlink service path.")
    if not owned_plist(target["plist"], target["root"]):
        raise ValueError("An unrelated service file exists; it was not replaced.")
    config = {"base_url": base_url, "ac_id": ac_id, "probe_url": probe_url,
              "request_timeout": 5, "retry_cooldown_seconds": 300,
              "check_interval_seconds": interval, "required_failed_checks": 2,
              "env_profile": env_profile}
    arguments = [sys.executable, "-m", "chatecnu"]
    if env_profile:
        arguments += ["-e", env_profile]
    arguments += ["net", "ensure-login", "--service-run", "--json", "-I"]
    job = {"Label": LABEL, "ProgramArguments": arguments, "RunAtLoad": True,
           "StartInterval": interval, "ProcessType": "Background", "ThrottleInterval": 30,
           "StandardOutPath": "/dev/null", "StandardErrorPath": "/dev/null",
           "EnvironmentVariables": {"CHATARCH_HOME": str(get_paths().home_dir)}}
    result = {"success": True, "dry_run": dry_run, "label": LABEL,
              "interval_seconds": interval, "plist": str(target["plist"]),
              "credential_source": "ChatEnv ECNU profile",
              "chat_env_profile": env_profile or "active"}
    if dry_run:
        return result
    target["root"].mkdir(parents=True, exist_ok=True, mode=0o700)
    target["plist"].parent.mkdir(parents=True, exist_ok=True)
    existing = [target[key] for key in ("config", "plist") if target[key].exists()]
    backup = None
    if existing:
        backup = Path(tempfile.mkdtemp(prefix="service-backup-", dir=target["root"]))
        for old in existing:
            shutil.copy2(old, backup / old.name)
    loaded = launchctl("print", f"gui/{os.getuid()}/{LABEL}", allow_missing=True).returncode == 0
    if loaded:
        launchctl("bootout", f"gui/{os.getuid()}/{LABEL}")
    try:
        write_json(target["config"], config)
        target["plist"].write_bytes(plistlib.dumps(job, sort_keys=False))
        target["plist"].chmod(0o600)
        launchctl("bootstrap", f"gui/{os.getuid()}", str(target["plist"]))
    except Exception:
        for key in ("config", "plist"):
            old = target[key]
            if old in existing and backup is not None:
                shutil.copy2(backup / old.name, old)
            else:
                old.unlink(missing_ok=True)
        if loaded:
            launchctl("bootstrap", f"gui/{os.getuid()}", str(target["plist"]), allow_missing=True)
        raise
    return dict(result, loaded=True)


def uninstall_service(*, dry_run: bool = False) -> dict:
    require_macos()
    target = paths()
    if not owned_plist(target["plist"], target["root"]):
        raise ValueError("An unrelated service file exists; it was not removed.")
    if not dry_run:
        if launchctl("print", f"gui/{os.getuid()}/{LABEL}", allow_missing=True).returncode == 0:
            launchctl("bootout", f"gui/{os.getuid()}/{LABEL}")
        target["plist"].unlink(missing_ok=True)
    return {"success": True, "dry_run": dry_run, "label": LABEL,
            "action": "uninstall", "credential_source": "ChatEnv ECNU profile"}
