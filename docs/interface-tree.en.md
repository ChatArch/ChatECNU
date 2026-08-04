# Interface Tree

## Package Structure

```text
chatecnu
├── cli.main                 # Click entrypoint; installation provides ecnu
├── config.ECNUConfig        # ChatEnv ecnu type
├── network_auth             # Campus-network auth_client wrapper
└── ecnu.portal              # ECNU portal client
```

## Command to Python Mapping

| Python API | Command mapping |
| --- | --- |
| `PortalClient.login_init()` | `ecnu home login-init` (hidden) |
| `PortalClient.login()` / `login_auto()` | `ecnu home login` |
| `PortalClient.logout()` | `ecnu home logout` |
| `PortalClient.home_summary()` | `ecnu home info` |
| `PortalClient.user_info()` | `ecnu home user` |
| `PortalClient.auth_logs()` / `detail_logs()` | `ecnu debug ...` (hidden) |
| `NetworkAuthClient.check()` | `ecnu net check` |
| `NetworkAuthClient.login()` | `ecnu net login` |
| `NetworkAuthClient.logout()` | `ecnu net logout` |
| `NetworkAuthClient.ensure_login()` | `ecnu net ensure-login` |
| `PortalClient.list_visitors()` | `ecnu visitor list` |
| `PortalClient.get_visitor()` | `ecnu visitor get` |
| `PortalClient.create_visitor()` | `ecnu visitor create` |
| `PortalClient.update_visitor()` | `ecnu visitor update` |
| `PortalClient.delete_visitor()` | `ecnu visitor delete` |

## ChatEnv Interface

See [ChatEnv Variables](chatenv.md) for the full schema. Sensitive fields are masked by ChatEnv and command renderers.
