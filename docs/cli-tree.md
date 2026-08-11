# 命令树

这页只列当前已实现的可见命令。隐藏诊断命令不放进主树。能力边界见 [能力地图](capability-map.md)，Python 映射见 [接口树](interface-tree.md)。

## 当前可见命令树

以下内容来自 `ecnu --tree` 的当前 Click 注册表输出：

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

隐藏的 `debug`、`selftest`、`home login-init/login-auto/session-info/cookie-header` 和 `visitor lock` 仍保留给诊断/内部流程，不作为主用户树展示。

## home {#home}

见上方 `ecnu --tree` 中的 `home` 子树。

## net {#net}

见上方 `ecnu --tree` 中的 `net` 子树。

## visitor {#visitor}

见上方 `ecnu --tree` 中的 `visitor` 子树。

## 更新规则

- 新增可见命令时，同步更新本页和 `ecnu --tree` 测试。
- 计划中但未实现的能力不要写入命令树。
- 本页只列当前可用入口。
