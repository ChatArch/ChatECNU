# ECNU Usage

ChatECNU splits ECNU capabilities into three groups: `home` for portal access, `net` for campus-network access, and `visitor` for visitor accounts.

## Portal {#portal}

Portal login creates an ECNU Web/API session used by home summary, user info, and visitor-account APIs. Sessions are stored in ChatEnv's runtime token store by default: `~/.chatarch/tokens/ECNU/<profile>.json`. `ecnu home status --json` returns only safe metadata such as cookie count, token file, and profile; it never prints raw cookies or CSRF values. `chatenv token refresh ECNU <profile>` can run a non-interactive OCR-backed auto-login from the matching stable env profile and fails closed when SMS or CAPTCHA retries are required.

```bash
ecnu home login --rounds 3 --topk 5 -I
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

SMS code flow:

```bash
ecnu home login --sms-code 123456 --rounds 3 --topk 5 -I
```

Manual CAPTCHA helpers remain hidden:

```bash
ecnu home login-init
ecnu home login --captcha ABCD -I
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

## Campus network access {#network-login}

`ECNU_NETWORK_BACKEND=python` is the default: SRun HTTP runs directly, without `auth_client` or password-bearing child-process argv. It reuses ChatEnv `ECNU_USERNAME` / `ECNU_PASSWORD` and native `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`; Python imports legacy settings only with explicit `--setting-file`; login/logout verify the resulting online state and JSON reports `backend=python`. Only explicit `ECNU_NETWORK_BACKEND=binary` uses the legacy binary, where login still requires `--allow-argv-password`; `--auth-client` / `ECNU_AUTH_CLIENT` apply only to binary. The default Python path does not require `net install`.

```bash
ecnu net check --json
ecnu net login -I
ecnu net logout -I
ecnu net ensure-login -I
```

`ECNU_NETWORK_BACKEND=python` is the default: SRun HTTP runs directly, without `auth_client` or password-bearing child-process argv. It reuses ChatEnv `ECNU_USERNAME` / `ECNU_PASSWORD` and native `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`; Python imports legacy settings only with explicit `--setting-file`; login/logout verify the resulting online state and JSON reports `backend=python`. Only explicit `ECNU_NETWORK_BACKEND=binary` uses the legacy binary, where login still requires `--allow-argv-password`; `--auth-client` / `ECNU_AUTH_CLIENT` apply only to binary. The default Python path does not require `net install`.

New settings contain only these four TOML fields, with no credentials:

```toml
host = "login.ecnu.edu.cn"
acid = 1
campus_url = ""
campus_postfix = ""
```

After installation, the wrapper reads the installer-configured `ECNU_AUTH_SETTING_FILE` and passes `-c` to the helper. `--host` accepts a hostname or IPv4 with an optional port, not a scheme/path/userinfo; `--ac-id` is a positive integer. Usable existing settings must be valid TOML containing all four fields. Preview backups/replacements with `--force --dry-run --json`, then remove `--dry-run` after review. Backups are not automatically restored. OS-level I/O failures can leave partial files; inspect paths/actions and retry safely.

## Visitor accounts {#visitor}

```bash
ecnu visitor list
ecnu visitor get --id 10256703
ecnu visitor create --remark GuestA --dry-run -I
ecnu visitor default -I
```

Mutation commands support `--dry-run`.
