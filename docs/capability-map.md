# 能力地图

## 当前能力

| 能力 | 状态 | 入口 | 边界 |
| --- | --- | --- | --- |
| 门户登录 | 已实现 | `ecnu home login` | 建立 ECNU Web/API 会话 |
| 门户读取 | 已实现 | `ecnu home info/status/user` | 依赖已登录会话或 Cookie |
| 访客账号 | 已实现 | `ecnu visitor ...` | 修改类命令支持 `--dry-run` |
| 校园网在线检查 | 已实现 | `ecnu net check` | 不需要密码 |
| 校园网联网 | 已实现 | `ecnu net login/logout/ensure-login` | 内置 Linux x86_64 `auth_client`；默认拒绝 argv 密码 |
| ChatEnv 配置 | 已实现 | `ecnu` 类型 | 密码和 Cookie 为敏感字段 |

## 边界

- 门户登录不是校园网联网；它只管理 ECNU 门户会话。
- `net` 不是门户登录；它只管理本机校园网出口认证。
- ChatECNU 通过 PyPI wheel/sdist 分发 Linux x86_64 `auth_client`；`--auth-client` / `ECNU_AUTH_CLIENT` 仍可覆盖路径。
- stdout、stderr、JSON 输出和 redacted command 都会脱敏已解析密码。
- 进程环境优先于默认 ChatEnv；显式 `-e` / `--env-file` 才使用指定配置。

## 验证入口

```bash
python -m pytest -q
mkdocs build --strict
ecnu net check --json
```
