# 接口树

## 包结构

```text
chatecnu
├── cli.main                 # Click 入口；安装后提供 ecnu 命令
├── config.ECNUConfig        # ChatEnv ecnu 类型
├── network_auth             # 校园网 auth_client 包装
└── ecnu.portal              # ECNU 门户客户端
```

## 命令到 Python 映射

| Python 接口 | 命令行映射 |
| --- | --- |
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

完整变量说明见 [ChatEnv 变量](chatenv.md)。敏感字段由 ChatEnv 和命令输出侧脱敏处理。
