# Quickstart

## Install

```bash
pip install ChatECNU
```

Install CAPTCHA OCR support when needed:

```bash
pip install "ChatECNU[captcha]"
```

### Explicit campus-network setup

`pip install` does not modify user files. The default Python backend needs no auth_client installation. The following explicit offline installer prepares only the Linux x86_64 binary compatibility backend:

```bash
ecnu net install --dry-run --json
ecnu net install --json
# Update only this ChatEnv profile without activating it:
ecnu -e campus net install --json
# Customize a new endpoint configuration; never pass credentials or tokens:
ecnu net install --host login.ecnu.edu.cn --ac-id 1 --campus-url "" --campus-postfix ""
```

Managed files default to `$CHATARCH_HOME/chatecnu/` (`~/.chatarch/chatecnu/` when unset): `bin/auth_client` and `config/auth-setting.toml`. The legacy entries `~/.local/bin/auth_client` and `~/.auth-setting` are thin symlinks. Usable existing legacy files are preserved byte-for-byte and selected as-is, never relocated; repeated installation does not rewrite files. Endpoint options affect newly generated settings only; replacing existing settings requires explicit `--force`. Replaced files/symlinks are backed up under `chatecnu/backups/<id>/`; unknown symlink targets stay untouched, and directory conflicts always fail.

`--dry-run` creates no directories or ChatEnv profiles. `--json` reads back paths, sources and actions, not profile values. Only `ECNU_AUTH_CLIENT` / `ECNU_AUTH_SETTING_FILE` are updated through EnvStore; credentials and other values are preserved. No login, restart, daemon installation or download occurs. Mac, Windows and Linux ARM fail before writes, including dry-run.

## Prepare ChatEnv

ChatECNU registers the ChatEnv type `ecnu`.

```bash
chatenv list
chatenv init -t ecnu -I
```

Common variables:

```text
ECNU_USERNAME=your account
ECNU_PASSWORD=your password
```

See [ChatEnv Variables](chatenv.md) for the full schema.

## CLI Smoke

```bash
ecnu --version
ecnu --tree
ecnu --tree-brief
```

## Portal Smoke

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
```

## Campus Network Smoke

```bash
ecnu net check --json
ecnu net ensure-login -I
```

`ECNU_NETWORK_BACKEND=python` is the default: SRun HTTP runs directly, without `auth_client` or password-bearing child-process argv. It reuses ChatEnv `ECNU_USERNAME` / `ECNU_PASSWORD` and native `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`; Python imports legacy settings only with explicit `--setting-file`; login/logout verify the resulting online state and JSON reports `backend=python`. Only explicit `ECNU_NETWORK_BACKEND=binary` uses the legacy binary, where login still requires `--allow-argv-password`; `--auth-client` / `ECNU_AUTH_CLIENT` apply only to binary. The default Python path does not require `net install`.

## Scheduled automatic login on macOS

Automatic recovery extends `ecnu net ensure-login` (`chatecnu net ensure-login`
is the compatibility entrypoint); no additional CLI is installed.

```bash
# Preview without writing files or starting a job
ecnu net ensure-login --interface en1 --install-service --interval 60 --dry-run --json
# Install and start the current user's LaunchAgent
ecnu net ensure-login --interface en1 --install-service --interval 60
# Enter the service account password privately and save it in macOS Keychain
ecnu net ensure-login --save-password
# Inspect the service and latest check
ecnu net ensure-login --service-status --json
# Stop and remove the job, retaining configuration and credentials
ecnu net ensure-login --uninstall-service
```

`--interface` also works with `net check/login/logout`, currently on macOS with
the Python backend. Use `ecnu net check --interface en1 --json` for Wi-Fi or
`ecnu net check --interface en0 --json` for Ethernet. DNS, reachability and
portal sockets stay bound to that interface, with TLS verification enabled;
there is no fallback to another interface or proxy, or system route/priority change.
`--probe-url` defaults to `https://www.baidu.com/`; HTTPS reachability replaces ICMP ping.

The service runs at user sign-in and every `--interval` seconds (default 60),
calling the installed package through `python -m chatecnu net ensure-login`.
It records the router address and MAC at installation and skips other networks.
Login requires two consecutive failed probes and an explicit offline portal response.
Unknown status, an authenticated network outage or unavailable credentials do not
cause blind logins. Attempts have a five-minute cooldown; a lock prevents concurrent checks.

Credentials come from matching `ECNU_USERNAME` / `ECNU_PASSWORD` in the selected
ChatEnv profile (`-e campus`), or from the macOS login Keychain. `--save-password`
requires a local interactive terminal. Passwords are absent from plist/JSON files
and command arguments. Without credentials, the service monitors but cannot restore
expired authentication. Background jobs do not inherit one-off shell credentials;
use a ChatEnv profile or Keychain.

Configuration and state live in `$CHATARCH_HOME/chatecnu/wifi-autologin/` and the
job in `~/Library/LaunchAgents/com.chatarch.ecnu.wifi-autologin.plist`.
Reinstallation backs up the old configuration and job, including migration from the
earlier standalone agent; the installer leaves old script files in place. Failed
installation restores the previous files. This is a per-user Mac service, inactive
during shutdown, sleep or user logout, not a router service.
