# Interface Tree

## Package Structure

```text
chatecnu
├── cli.main                 # Click entrypoint; installation provides ecnu
├── config.ECNUConfig        # ChatEnv ecnu type
├── ecnu.session_tokens      # ChatEnv token-store adapter for ECNU portal sessions
├── network_auth             # Campus-network auth_client wrapper
└── ecnu.portal              # ECNU portal client
```

## Command to Python Mapping

| Python API | Command mapping |
| --- | --- |
| `chatecnu.ecnu.cli.render_cli_tree()` | `ecnu --tree` |
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

See [ChatEnv Variables](chatenv.md) for the full schema. Stable sensitive fields are managed by ChatEnv profiles; portal cookie/CSRF session state is managed by ChatEnv's token store, and command output shows only safe metadata.
