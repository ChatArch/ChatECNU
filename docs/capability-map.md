# 能力地图

## 当前能力

| 能力 | 状态 | 入口 | 边界 |
| --- | --- | --- | --- |
| 门户登录 | 已实现 | `ecnu home login` | 建立 ECNU Web/API 会话 |
| 门户读取 | 已实现 | `ecnu home info/status/user` | 依赖 token-store 中的已登录门户会话 |
| 访客账号 | 已实现 | `ecnu visitor ...` | 修改类命令支持 `--dry-run` |
| 离线联网准备 | 已实现 | `ecnu net install` | Native Linux x86_64；不登录/下载；dry-run 与 force 备份 |
| 校园网在线检查 | 已实现 | `ecnu net check` | 不需要密码 |
| 校园网联网 | 已实现 | `ecnu net login/logout/ensure-login` | 默认纯 Python HTTP；binary 兼容后端必须显式选择 |
| ChatEnv 配置 | 已实现 | `ecnu` 类型 | 密码在 stable env，门户会话/Cookie 在 runtime token-store |

## 边界

- 门户登录不是校园网联网；它只管理 ECNU 门户会话。
- `net` 不是门户登录；它只管理本机校园网出口认证。
- 默认 `ECNU_NETWORK_BACKEND=python`：直接执行 SRun HTTP 协议，不运行 `auth_client`，不通过外部进程 argv 传密码。复用 ChatEnv 的 `ECNU_USERNAME` / `ECNU_PASSWORD` 及原生 `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`；Python 仅在显式 `--setting-file` 时导入旧格式；登录/退出后重新检查实际在线状态，JSON 返回 `backend=python`。只有显式选择 `ECNU_NETWORK_BACKEND=binary` 才使用旧二进制，且登录仍需 `--allow-argv-password`；`--auth-client` / `ECNU_AUTH_CLIENT` 也仅作用于 binary。默认 Python 路径不需要 `net install`。
- stdout、stderr、JSON 输出和 redacted command 都会脱敏已解析密码。
- 门户会话、Cookie、CSRF 这类动态状态写入 `tokens/ECNU/<profile>.json`，不写入 `ECNU_COOKIE` stable env 字段。
- 进程环境优先于默认 ChatEnv；显式 `-e` / `--env-file` 才使用指定配置。

## 验证入口

```bash
python -m pytest -q
mkdocs build --strict
ecnu net check --json
```
