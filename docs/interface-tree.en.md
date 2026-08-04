# Interface Tree

This page lists implemented user entry points and Python interfaces only. Planned capabilities stay out of the interface tree.

## CLI entry points

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

Hidden compatibility entry: `network-auth` → `auth`. Hidden diagnostics live under `debug` and are not part of the main user interface.

## Python modules

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

| Interface | Purpose |
| --- | --- |
| `NetworkAuthClient.check()` | Run `auth_client check` and parse online state |
| `NetworkAuthClient.login(credentials)` | Log in; argv passwords are refused by default |
| `NetworkAuthClient.ensure_login(credentials)` | Check first, then log in only when offline |
| `NetworkAuthCredentials` | Username and password structure |
| `NetworkAuthResult` | Structured result, returncode, stdout/stderr, online state |

## `chatecnu.ecnu.portal.PortalClient`

| Interface | CLI mapping |
| --- | --- |
| `login_init()` | `chatecnu login-init` hidden command |
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

## ChatEnv interface

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

Sensitive fields are masked by ChatEnv and CLI output code.
