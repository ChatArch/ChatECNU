"""Offline, non-starting installation of ECNU's bundled network helper.

No subprocess, login, daemon, or credential input is involved. All predictable
platform/input/path conflicts are checked before writes. Installation is not a
transaction: an OS-level I/O failure can leave partial files; retry is safe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
import json
import os
import platform
import re
import shutil
from urllib.parse import urlsplit
from uuid import uuid4

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

from chatenv import EnvStore, get_paths
from chatecnu.config import ECNUConfig


class NetworkInstallError(ValueError):
    """Unsupported platform, invalid settings, or unsafe path conflict."""


@dataclass(frozen=True)
class NetworkInstallPaths:
    root: Path
    auth_client: Path
    setting_file: Path
    legacy_auth_client: Path
    legacy_setting_file: Path
    backups: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


def state_paths(*, home: str | Path | None = None, user_home: str | Path | None = None) -> NetworkInstallPaths:
    """Return managed and legacy paths without creating anything.

    ``home`` overrides ChatArch home; ``user_home`` overrides the two legacy
    entrypoints (normally the current user's HOME). Neither changes profiles.
    """
    root = get_paths(home).home_dir / 'chatecnu'
    legacy_home = Path(user_home).expanduser().absolute() if user_home else Path.home()
    return NetworkInstallPaths(
        root, root / 'bin/auth_client', root / 'config/auth-setting.toml',
        legacy_home / '.local/bin/auth_client', legacy_home / '.auth-setting',
        root / 'backups',
    )


@dataclass(frozen=True)
class NetworkInstallResult:
    success: bool
    dry_run: bool
    auth_client: str
    setting_file: str
    source: str
    paths: dict[str, str]
    actions: list[dict[str, str]]
    env_profile: str | None
    env_file: str

    def to_dict(self) -> dict[str, object]:
        """Return paths/actions only; never expose profile values."""
        return asdict(self)


def _validate_settings(host: str, ac_id: int, campus_url: str, campus_postfix: str) -> None:
    if not isinstance(host, str) or not re.fullmatch(r'[A-Za-z0-9._-]+(?::[0-9]+)?', host):
        raise NetworkInstallError('host must be a hostname or IPv4 address, optionally with :port (no scheme/path/credentials).')
    if ':' in host and not 1 <= int(host.rsplit(':', 1)[1]) <= 65535:
        raise NetworkInstallError('host port must be between 1 and 65535.')
    if type(ac_id) is not int or ac_id < 1:
        raise NetworkInstallError('ac_id must be a positive integer.')
    for name, value in (('campus_url', campus_url), ('campus_postfix', campus_postfix)):
        if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise NetworkInstallError(f'{name} must be text without control characters.')
    if campus_url:
        try:
            url = urlsplit(campus_url)
            valid = url.scheme in {'http', 'https'} and bool(url.hostname) and not url.username and not url.password
            url.port
        except ValueError:
            valid = False
        if not valid:
            raise NetworkInstallError('campus_url must be empty or an HTTP(S) URL without credentials.')


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _check_parents(path: Path) -> None:
    for parent in path.parents:
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise NetworkInstallError(f'Unsafe parent path: {parent}')


def _usable(path: Path, kind: str) -> bool:
    if not path.is_file():
        return False
    if kind == 'binary':
        return path.stat().st_size > 0 and os.access(path, os.X_OK)
    try:
        values = tomllib.loads(path.read_text(encoding='utf-8'))
        ac_id = values['acid']
        # Older auth_client helpers write acid as a quoted TOML string.
        # Accept its numeric equivalent without rewriting the user's file.
        if isinstance(ac_id, str):
            if not re.fullmatch(r'[0-9]+', ac_id):
                return False
            ac_id = int(ac_id)
        if not isinstance(ac_id, int) or isinstance(ac_id, bool):
            return False
        _validate_settings(values['host'], ac_id, values['campus_url'], values['campus_postfix'])
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return False
    return True


def _plan_resource(managed: Path, legacy: Path, kind: str, force: bool, backup_dir: Path, actions: list[dict[str, str]]) -> tuple[Path, str]:
    # Directories/special files are never replaced, including with --force.
    for path in (managed, legacy):
        if _present(path) and not path.is_file() and not path.is_symlink():
            raise NetworkInstallError(f'Path is not a regular file or symlink: {path}')
    managed_link = legacy.is_symlink() and legacy.resolve() == managed
    if not force and _present(legacy) and not managed_link:
        if not _usable(legacy, kind):
            raise NetworkInstallError(f'Unusable existing file: {legacy}; inspect it or use --force to back up and replace.')
        actions.append({'action': 'preserve', 'path': str(legacy)})
        return legacy, 'existing-legacy'
    if not force and _present(managed):
        if not _usable(managed, kind):
            raise NetworkInstallError(f'Unusable existing file: {managed}; inspect it or use --force to back up and replace.')
        actions.append({'action': 'preserve', 'path': str(managed)})
        source = 'existing-managed'
    else:
        if _present(managed):
            actions.append({'action': 'backup', 'path': str(managed), 'backup': str(backup_dir / ('managed-' + kind))})
        actions.append({'action': 'install-binary' if kind == 'binary' else 'write-config', 'path': str(managed)})
        source = 'bundled-linux-x86_64' if kind == 'binary' else 'generated'
    if force and _present(legacy):
        actions.append({'action': 'backup', 'path': str(legacy), 'backup': str(backup_dir / ('legacy-' + kind))})
    if force or not _present(legacy):
        actions.append({'action': 'symlink', 'path': str(legacy), 'target': str(managed)})
    else:
        actions.append({'action': 'preserve', 'path': str(legacy)})
    return managed, source


def install_network_auth(
    *, home: str | Path | None = None, user_home: str | Path | None = None,
    env_profile: str | None = None, host: str = 'login.ecnu.edu.cn', ac_id: int = 1,
    campus_url: str = '', campus_postfix: str = '', force: bool = False,
    dry_run: bool = False,
) -> NetworkInstallResult:
    """Prepare a Linux x86_64 helper/config and update only two ChatEnv keys.

    Existing usable legacy files are selected as-is, never relocated. Otherwise
    managed files are reused/created and missing legacy entries are symlinks.
    Endpoint options affect newly generated config only unless ``force=True``.
    Force backs up replaced files/symlinks under the service's backups directory;
    unknown symlink targets are never modified. Named profiles are not activated.
    Dry-run returns the plan with no writes (including no profile/root creation).
    Platform detection is native and enforced even for dry-run. The binary is
    copied from package resources and never executed or fetched from the network.
    """
    if platform.system() != 'Linux' or platform.machine().lower() not in {'x86_64', 'amd64'}:
        raise NetworkInstallError('net install supports Linux x86_64 only; no files were written.')
    _validate_settings(host, ac_id, campus_url, campus_postfix)
    paths = state_paths(home=home, user_home=user_home)
    store = EnvStore(get_paths(home).envs_dir)
    try:
        env_file = store.profile_path(ECNUConfig, env_profile) if env_profile is not None else store.active_path(ECNUConfig)
    except ValueError as exc:
        raise NetworkInstallError('Invalid ChatEnv profile name.') from exc
    if env_profile is not None and (env_file.parent != store.config_dir(ECNUConfig) or env_file == store.active_path(ECNUConfig)):
        raise NetworkInstallError('Named ChatEnv profile must stay inside the ECNU profile directory and cannot be the active .env file.')
    for path in (paths.auth_client, paths.setting_file, paths.legacy_auth_client, paths.legacy_setting_file, env_file):
        _check_parents(path)
    if env_file.is_symlink() or (_present(env_file) and not env_file.is_file()):
        raise NetworkInstallError(f'Unsafe ChatEnv profile path: {env_file}')
    if force:
        _check_parents(paths.backups / 'probe')
    backup_dir = paths.backups / uuid4().hex
    actions: list[dict[str, str]] = []
    auth_client, source = _plan_resource(paths.auth_client, paths.legacy_auth_client, 'binary', force, backup_dir, actions)
    setting_file, _ = _plan_resource(paths.setting_file, paths.legacy_setting_file, 'config', force, backup_dir, actions)
    values = store.load_profile(ECNUConfig, env_profile) if env_profile is not None else store.load_active(ECNUConfig)
    updates = {'ECNU_AUTH_CLIENT': str(auth_client), 'ECNU_AUTH_SETTING_FILE': str(setting_file)}
    env_changed = any(values.get(key) != value for key, value in updates.items())
    actions.append({'action': 'update-env' if env_changed else 'preserve', 'path': str(env_file)})
    # Resolve the packaged source before writing, including dry-run validation.
    binary = files('chatecnu').joinpath('bin/linux-x86_64/auth_client').read_bytes()
    settings = {'host': host, 'acid': ac_id, 'campus_url': campus_url, 'campus_postfix': campus_postfix}
    config_text = ''.join(f'{key} = {json.dumps(value, ensure_ascii=False)}\n' for key, value in settings.items())
    if not dry_run:
        for item in actions:
            path = Path(item['path'])
            action = item['action']
            if action == 'preserve' or action == 'update-env':
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if action == 'backup':
                backup = Path(item['backup'])
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup, follow_symlinks=False)
                if path.is_symlink():
                    verified = backup.is_symlink() and backup.readlink() == path.readlink()
                else:
                    verified = backup.read_bytes() == path.read_bytes() and backup.stat().st_mode == path.stat().st_mode
                if not verified:
                    raise NetworkInstallError(f'Backup verification failed: {backup}')
                path.unlink()
            elif action == 'install-binary':
                with path.open('xb') as output:
                    output.write(binary)
                path.chmod(0o755)
            elif action == 'write-config':
                with path.open('x', encoding='utf-8') as output:
                    output.write(config_text)
            elif action == 'symlink':
                path.symlink_to(item['target'])
        if not _usable(auth_client, 'binary') or not _usable(setting_file, 'config'):
            raise NetworkInstallError('Installed helper/config readback failed.')
        if env_changed:
            # The store owns parsing/serialization. On a failed store write or
            # readback, restore only the original bytes (no leaf dotenv logic),
            # so credential values cannot be silently damaged by partial I/O.
            original = env_file.read_bytes() if env_file.exists() else None
            original_mode = env_file.stat().st_mode if original is not None else 0o600
            values.update(updates)
            try:
                if env_profile is not None:
                    store.save_profile(ECNUConfig, env_profile, values)
                else:
                    store.save_active(ECNUConfig, values)
                readback = store.load_profile(ECNUConfig, env_profile) if env_profile is not None else store.load_active(ECNUConfig)
                if readback != values:
                    raise NetworkInstallError('ChatEnv profile readback failed (values not printed).')
            except Exception:
                if original is not None:
                    env_file.write_bytes(original)
                    env_file.chmod(original_mode)
                elif env_file.is_file():
                    env_file.unlink()
                raise
    return NetworkInstallResult(True, dry_run, str(auth_client), str(setting_file), source, paths.to_dict(), actions, env_profile, str(env_file))
