# ChatECNU

ChatECNU 是 ECNU 门户与校园网联网工具包。安装包名仍是 `ChatECNU`，日常命令主推 `ecnu`。

## 文档入口

| 任务 | 链接 |
| --- | --- |
| 安装和最小验证 | https://arch.gh.wzhecnu.cn/ChatECNU/quickstart/ |
| 命令树 | https://arch.gh.wzhecnu.cn/ChatECNU/cli-tree/ |
| ChatEnv 变量 | https://arch.gh.wzhecnu.cn/ChatECNU/chatenv/ |
| ECNU 使用 | https://arch.gh.wzhecnu.cn/ChatECNU/ecnu/ |

## 安装

```bash
pip install ChatECNU
```

如需验证码识别能力：

```bash
pip install "ChatECNU[captcha]"
```

## 命令结构

ChatECNU 的命令面可用 `ecnu --tree` 从当前 Click 注册表直接回读：

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

门户命令统一放在 `home` 下：

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

校园网联网统一放在 `net` 下：

```bash
ecnu net check --json
ecnu net login -I --allow-argv-password
ecnu net logout -I
ecnu net ensure-login -I --allow-argv-password
```

ChatECNU 的 PyPI wheel/sdist 内置 Linux x86_64 `auth_client`，默认 `ecnu net ...` 会优先使用该内置二进制；如需覆盖，可用 `--auth-client` 或 `ECNU_AUTH_CLIENT` 指定路径。账号密码使用同一组 `ECNU_USERNAME` / `ECNU_PASSWORD`。`net check` 会显示当前 `online/account/username`；`net logout` 未提供用户名时会先从 `auth_client check` 的 `Username=...` 自动提取。

敏感值（密码、Cookie、短信码、会话）不要打印或提交。
