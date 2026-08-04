# 接口树

这页列当前已实现的命令行入口和 Python 接口。计划能力不放进接口树。

## 命令行入口

```text
chatecnu
├── auth
│   ├── check
│   ├── login
│   └── ensure-login
├── home
├── login
├── logout
├── status
├── user-info
└── visitor
    ├── list
    ├── get
    ├── create
    ├── default
    ├── update
    └── delete
```

隐藏兼容入口：`network-auth` → `auth`。隐藏诊断入口在 `debug` 下，不属于主用户接口。

## Python 模块

```text
chatecnu
├── cli.main
├── config.ECNUConfig
├── network_auth
│   ├── NetworkAuthClient
│   ├── NetworkAuthCredentials
│   ├── NetworkAuthResult
│   ├── redact_command
│   └── redact_text
└── ecnu
    ├── portal.PortalClient
    └── captcha.recognize_captcha_topk
```

## `chatecnu.network_auth`

| 接口 | 用途 |
| --- | --- |
| `NetworkAuthClient.check()` | 执行 `auth_client check` 并解析在线状态 |
| `NetworkAuthClient.login(credentials)` | 登录校园网；默认拒绝 argv 密码 |
| `NetworkAuthClient.ensure_login(credentials)` | 先检查，离线时再登录 |
| `NetworkAuthCredentials` | 用户名和密码结构 |
| `NetworkAuthResult` | 结构化结果、returncode、stdout/stderr、在线状态 |

## `chatecnu.ecnu.portal.PortalClient`

| 接口 | 命令行映射 |
| --- | --- |
| `login_init()` | `chatecnu login-init`（隐藏） |
| `login()` / `login_auto()` | `chatecnu login` |
| `logout()` | `chatecnu logout` |
| `home_summary()` | `chatecnu home` |
| `user_info()` | `chatecnu user-info` |
| `auth_logs()` / `detail_logs()` | `chatecnu debug ...` |
| `list_visitors()` | `chatecnu visitor list` |
| `get_visitor()` | `chatecnu visitor get` |
| `create_visitor()` | `chatecnu visitor create` |
| `update_visitor()` | `chatecnu visitor update` |
| `delete_visitor()` | `chatecnu visitor delete` |

## ChatEnv 接口

```text
ECNU_USERNAME
ECNU_PASSWORD
ECNU_COOKIE
ECNU_BASE_URL
ECNU_VISITOR_PASSWORD1
ECNU_VISITOR_PASSWORD2
ECNU_VISITOR_REMARK
ECNU_AUTH_CLIENT
ECNU_AUTH_SETTING_FILE
```

敏感字段由 ChatEnv 和 CLI 输出侧脱敏处理。
