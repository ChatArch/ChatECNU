# Interface Tree

## Package Structure

```text
chatecnu
├── cli.main                 # Click entrypoint; installs ecnu and the chatecnu compatibility alias
├── config.ECNUConfig        # ChatEnv ecnu type
├── ecnu.session_tokens      # ChatEnv token-store adapter for ECNU portal sessions
├── network_auth             # Campus-network auth_client wrapper
├── network_install          # Offline helper/config installer
└── ecnu.portal              # ECNU portal client
```

## Command to Python Mapping

| Python API | Command mapping |
| --- | --- |
| `chatstyle.add_tree_option()` | `ecnu --tree` / `ecnu --tree-brief` |
| `PortalClient.login_init()` | `ecnu home login-init` (hidden) |
| `PortalClient.login()` / `login_auto()` | `ecnu home login` |
| `PortalClient.logout()` | `ecnu home logout` |
| `PortalClient.home_summary()` | `ecnu home info` |
| `PortalClient.user_info()` | `ecnu home user` |
| `PortalClient.auth_logs()` / `detail_logs()` | `ecnu debug ...` (hidden) |
| `chatecnu.network_install.install_network_auth()` | `ecnu net install` |
| `chatecnu.network_install.state_paths()` | Managed/legacy paths in install JSON |
| `NetworkAuthClient.check()` | `ecnu net check` |
| `NetworkAuthClient.login()` | `ecnu net login` |
| `NetworkAuthClient.logout()` | `ecnu net logout` |
| `NetworkAuthClient.ensure_login()` | `ecnu net ensure-login` |
| `PortalClient.list_visitors()` | `ecnu visitor list` |
| `PortalClient.get_visitor()` | `ecnu visitor get` |
| `PortalClient.create_visitor()` | `ecnu visitor create` |
| `PortalClient.update_visitor()` | `ecnu visitor update` |
| `PortalClient.delete_visitor()` | `ecnu visitor delete` |

## Installer Python API

```python
from chatecnu.network_install import install_network_auth, state_paths

paths = state_paths()  # No writes; uses ChatEnv get_paths().home_dir.
plan = install_network_auth(dry_run=True, env_profile="campus")
print(plan.to_dict())  # Paths/actions only, never profile values.
```

The keyword-only API accepts `home` (ChatArch home), `user_home` (legacy entrypoints), `env_profile`, `host`, `ac_id`, `campus_url`, `campus_postfix`, `force` and `dry_run`. Returns `NetworkInstallResult`; `NetworkInstallError` reports platform/settings/path errors and OS errors may propagate. Native Linux x86_64 is required even for planning. It never executes the helper.

## ChatEnv Interface

See [ChatEnv Variables](chatenv.md) for the full schema. Stable sensitive fields are managed by ChatEnv profiles; portal cookie/CSRF session state is managed by ChatEnv's token store, and command output shows only safe metadata.
