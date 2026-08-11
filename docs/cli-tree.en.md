# CLI Tree

This page lists only visible implemented commands. Hidden diagnostics are not part of the main user tree. See [Capability Map](capability-map.md) for boundaries and [Interface Tree](interface-tree.md) for Python mappings.

## Current Visible Command Tree

The following tree comes from the current Click registry and can be read back with `ecnu --tree`:

```text
ecnu
├── --help  # Show this message and exit.
├── --version  # Show the installed ChatECNU version.
├── --tree  # Print this registered command tree and exit.
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

Hidden `debug`, `selftest`, `home login-init/login-auto/session-info`, and `visitor lock` entries remain available for diagnostics/internal flows, but are not part of the main user tree. `home cookie-header` is disabled to avoid raw cookie leaks.

## home {#home}

See the `home` subtree in the `ecnu --tree` output above.

## net {#net}

See the `net` subtree in the `ecnu --tree` output above.

## visitor {#visitor}

See the `visitor` subtree in the `ecnu --tree` output above.

## Update Rules

- Update this page and the `ecnu --tree` tests whenever a visible command changes.
- Do not list planned commands as implemented commands.
- Do not put old command names in the main tree.
