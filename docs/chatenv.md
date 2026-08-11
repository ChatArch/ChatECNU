# ChatEnv 变量

ChatECNU 注册的 ChatEnv 类型是 `ecnu`。门户和校园网共用同一个 ECNU 账号密码，不拆两套变量。稳定配置保存在 `~/.chatarch/envs/ECNU/<profile>.env`；门户 Web/API 会话、Cookie 和 CSRF 等动态状态保存在 ChatEnv runtime token-store：`~/.chatarch/tokens/ECNU/<profile>.json`。

## 常用命令

```bash
chatenv list
chatenv new default -t ecnu -I --yes
```

`-e/--env` 只选择本次命令使用的 ChatEnv profile，不切换全局 active profile。显式 profile 内的值优先，避免不同账号串用。

## 变量

| 变量 | 用途 | 敏感 |
| --- | --- | --- |
| `ECNU_USERNAME` | 门户和校园网共用用户名 | 否 |
| `ECNU_PASSWORD` | 门户和校园网共用密码 | 是 |
| `ECNU_BASE_URL` | 门户基地址 | 否 |
| `ECNU_AUTH_CLIENT` | 可选 auth_client 覆盖路径；默认使用 PyPI 内置二进制 | 否 |
| `ECNU_AUTH_SETTING_FILE` | 可选设置文件 | 否 |
| `ECNU_VISITOR_PASSWORD1` | 默认访客账号一密码 | 是 |
| `ECNU_VISITOR_PASSWORD2` | 默认访客账号二密码 | 是 |
| `ECNU_VISITOR_REMARK` | 默认访客备注 | 否 |

## 使用示例

```bash
ecnu -e default home status
chatenv token status -s ECNU -p default
ecnu -e default net check --json
ecnu -e default visitor default -I
```
