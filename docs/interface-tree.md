# 接口树

## 包结构

```text
chatecnu
├── cli.main                 # Click 入口；安装后提供 ecnu 与兼容别名 chatecnu
├── config.ECNUConfig        # ChatEnv ecnu 类型
├── ecnu.session_tokens      # ECNU 门户会话的 ChatEnv token-store adapter
├── network_auth             # 校园网 auth_client 包装
└── ecnu.portal              # ECNU 门户客户端
```

## 命令到 Python 映射

| Python 接口 | 命令行映射 |
| --- | --- |
| `chatstyle.add_tree_option()` | `ecnu --tree` / `ecnu --tree-brief` |
| `PortalClient.login_init()` | `ecnu home login-init`（隐藏） |
| `PortalClient.login()` / `login_auto()` | `ecnu home login` |
| `PortalClient.logout()` | `ecnu home logout` |
| `PortalClient.home_summary()` | `ecnu home info` |
| `PortalClient.user_info()` | `ecnu home user` |
| `PortalClient.auth_logs()` / `detail_logs()` | `ecnu debug ...`（隐藏） |
| `NetworkAuthClient.check()` | `ecnu net check` |
| `NetworkAuthClient.login()` | `ecnu net login` |
| `NetworkAuthClient.logout()` / `logout_current()` | `ecnu net logout` |
| `NetworkAuthClient.ensure_login()` | `ecnu net ensure-login` |
| `PortalClient.list_visitors()` | `ecnu visitor list` |
| `PortalClient.get_visitor()` | `ecnu visitor get` |
| `PortalClient.create_visitor()` | `ecnu visitor create` |
| `PortalClient.update_visitor()` | `ecnu visitor update` |
| `PortalClient.delete_visitor()` | `ecnu visitor delete` |

## ChatEnv 接口

完整变量说明见 [ChatEnv 变量](chatenv.md)。稳定敏感字段由 ChatEnv profile 管理；门户 Cookie/CSRF 会话状态由 ChatEnv token-store 管理，命令输出只显示安全摘要。
