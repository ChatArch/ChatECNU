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

`pip install` does not change user files. On Linux x86_64, explicitly run the offline installer (`chatecnu net install` and `ecnu net install` are the same entrypoint):

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
ecnu net ensure-login -I --allow-argv-password
```

`check` does not need a password. `login` / `ensure-login` do not pass passwords through external process argv by default. Use `--allow-argv-password` only after accepting local process-list exposure.
