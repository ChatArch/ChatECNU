# ChatECNU

ChatECNU is a tool package for ECNU portal access and campus-network access. The package name remains `ChatECNU`; the daily command is `ecnu`.
The installed `chatecnu` command remains a compatibility alias. Both entry points share the same Click object, whose tree uses the canonical `ecnu` root.

## Documentation

| Task | Link |
| --- | --- |
| Installation and smoke checks | https://arch.gh.wzhecnu.cn/ChatECNU/en/quickstart/ |
| CLI tree | https://arch.gh.wzhecnu.cn/ChatECNU/en/cli-tree/ |
| ChatEnv variables | https://arch.gh.wzhecnu.cn/ChatECNU/en/chatenv/ |
| ECNU usage | https://arch.gh.wzhecnu.cn/ChatECNU/en/ecnu/ |

## Install

```bash
pip install ChatECNU
```

For CAPTCHA OCR support:

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

## Command Shape

The current command surface can be read back from the Click registry with `ecnu --tree`, which includes parameter signatures by default. `ecnu --tree-brief` keeps command nodes and descriptions while omitting parameter signatures:

```text
ecnu
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── --env ENV-PROFILE  # ChatEnv 配置名。
├── home  # ECNU 门户。
│   ├── info [--json]  # 门户首页摘要。
│   ├── login [--username USERNAME] [--password PASSWORD] [--sms-code SMS-CODE] [--json] [--interactive]  # 登录门户。
│   ├── logout [--json]  # 退出门户会话。
│   ├── status [--json]  # 门户会话状态。
│   └── user [--json]  # 门户用户信息。
├── net  # 校园网联网。
│   ├── check [--auth-client AUTH-CLIENT-PATH] [--setting-file SETTING-FILE] [--json]  # 检查在线状态。
│   ├── ensure-login [--auth-client AUTH-CLIENT-PATH] [--setting-file SETTING-FILE] [--username USERNAME] [--password PASSWORD] [--allow-argv-password] [--json] [--interactive]  # 离线时登录。
│   ├── install [--host HOST] [--ac-id AC-ID] [--campus-url CAMPUS-URL] [--campus-postfix CAMPUS-POSTFIX] [--force] [--dry-run] [--json]  # 离线准备联网工具与设置，不登录。
│   ├── login [--auth-client AUTH-CLIENT-PATH] [--setting-file SETTING-FILE] [--username USERNAME] [--password PASSWORD] [--allow-argv-password] [--json] [--interactive]  # 登录。
│   └── logout [--auth-client AUTH-CLIENT-PATH] [--setting-file SETTING-FILE] [--username USERNAME] [--json] [--interactive]  # 退出校园网。
└── visitor  # 访客账号。
    ├── create [--remark REMARK] [--dry-run] [--json] [--interactive]  # 创建访客账号。
    ├── default [--password1 PASSWORD1] [--password2 PASSWORD2] [--remark REMARK] [--json] [--interactive]  # 维护默认访客账号。
    ├── delete [--id VISITOR-ID] [--dry-run] [--json] [--interactive]  # 删除访客账号。
    ├── get [--id VISITOR-ID] [--account ACCOUNT] [--json]  # 查询访客账号。
    ├── list [--json]  # 列出访客账号。
    └── update [--id VISITOR-ID] [--remark REMARK] [--password PASSWORD] [--dry-run] [--json] [--interactive]  # 更新访客备注和密码。
```

Portal commands live under `home`:

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

Portal sessions are stored in ChatEnv's runtime token store by default: `~/.chatarch/tokens/ECNU/<profile>.json`. `ecnu home status --json` reads back only safe metadata and never prints raw cookies or CSRF values. `chatenv token refresh ECNU <profile>` can run a non-interactive OCR-backed auto-login from the matching stable env profile, then lets ChatEnv write the runtime token-store record; it fails closed when SMS verification or CAPTCHA retries are required.

Campus-network commands live under `net`:

```bash
ecnu net check --json
ecnu net login -I --allow-argv-password
ecnu net logout -I
ecnu net ensure-login -I --allow-argv-password
```

ChatECNU bundles the Linux x86_64 `auth_client` in the PyPI wheel/sdist. Use `--auth-client` or `ECNU_AUTH_CLIENT` to override it. Portal access and campus-network access share `ECNU_USERNAME` / `ECNU_PASSWORD`.

Do not print or commit passwords, cookies, SMS codes, or session values.
