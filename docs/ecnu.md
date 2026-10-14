# ECNU 使用

ChatECNU 把 ECNU 相关能力分成三组：`home` 管门户，`net` 管校园网联网，`visitor` 管访客账号。

## 门户 {#portal}

门户登录建立 ECNU Web/API 会话，供首页摘要、用户信息和访客账号接口使用。
会话默认保存到 ChatEnv token-store：`~/.chatarch/tokens/ECNU/<profile>.json`；`ecnu home status --json` 只输出 Cookie 数量、token 文件、profile 等安全摘要，不输出原始 Cookie/CSRF。也可以用 `chatenv token refresh ECNU <profile>` 从同名 stable env profile 发起非交互 OCR 自动登录；遇到短信验证码或验证码候选失败时会安全失败。

```bash
ecnu home login --rounds 3 --topk 5 -I
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

短信验证码：

```bash
ecnu home login --sms-code 123456 --rounds 3 --topk 5 -I
```

手动验证码流程保留为隐藏 helper：

```bash
ecnu home login-init
ecnu home login --captcha ABCD -I
```

### 显式准备校园网工具

`pip install` 不会改用户文件。默认 Python 后端无需安装 auth_client；下面的显式离线安装器只准备 Linux x86_64 binary 兼容后端：

```bash
ecnu net install --dry-run --json
ecnu net install --json
# 只更新指定 ChatEnv profile，不激活它：
ecnu -e campus net install --json
# 新配置可定制认证端点；不要传账号、密码或 token：
ecnu net install --host login.ecnu.edu.cn --ac-id 1 --campus-url "" --campus-postfix ""
```

实体默认在 `$CHATARCH_HOME/chatecnu/`（未设置时 `~/.chatarch/chatecnu/`）：`bin/auth_client`、`config/auth-setting.toml`；兼容入口为 `~/.local/bin/auth_client`、`~/.auth-setting` 薄链接。既有可用 legacy 文件会原样保留并被选用，不迁移、不覆盖；重复安装不重写。端点选项只影响新生成的设置；修改既有设置须显式 `--force`。替换前原文件/链接备份到 `chatecnu/backups/<id>/`，未知链接目标不修改；目录冲突始终失败。

`--dry-run` 连目录和 ChatEnv profile 都不创建；`--json` 回读路径、来源与动作，不输出 profile 值。只通过 EnvStore 更新 `ECNU_AUTH_CLIENT` / `ECNU_AUTH_SETTING_FILE`，保留凭据和其他值。安装器不登录、不重启、不安装 daemon、无下载；Mac、Windows、Linux ARM 在写入前失败（包括 dry-run）。

## 校园网联网 {#network-login}

默认 `ECNU_NETWORK_BACKEND=python`：直接执行 SRun HTTP 协议，不运行 `auth_client`，不通过外部进程 argv 传密码。复用 ChatEnv 的 `ECNU_USERNAME` / `ECNU_PASSWORD` 及原生 `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`；Python 仅在显式 `--setting-file` 时导入旧格式；登录/退出后重新检查实际在线状态，JSON 返回 `backend=python`。只有显式选择 `ECNU_NETWORK_BACKEND=binary` 才使用旧二进制，且登录仍需 `--allow-argv-password`；`--auth-client` / `ECNU_AUTH_CLIENT` 也仅作用于 binary。默认 Python 路径不需要 `net install`。

```bash
ecnu net check --json
ecnu net login -I
ecnu net logout -I
ecnu net ensure-login -I
```

默认 `ECNU_NETWORK_BACKEND=python`：直接执行 SRun HTTP 协议，不运行 `auth_client`，不通过外部进程 argv 传密码。复用 ChatEnv 的 `ECNU_USERNAME` / `ECNU_PASSWORD` 及原生 `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`；Python 仅在显式 `--setting-file` 时导入旧格式；登录/退出后重新检查实际在线状态，JSON 返回 `backend=python`。只有显式选择 `ECNU_NETWORK_BACKEND=binary` 才使用旧二进制，且登录仍需 `--allow-argv-password`；`--auth-client` / `ECNU_AUTH_CLIENT` 也仅作用于 binary。默认 Python 路径不需要 `net install`。

新生成设置只有以下四个 TOML 字段，不含凭据：

```toml
host = "login.ecnu.edu.cn"
acid = 1
campus_url = ""
campus_postfix = ""
```

安装后 wrapper 会读取 installer 写入的 `ECNU_AUTH_SETTING_FILE`，并向 helper 传 `-c`。`--host` 接受主机名或 IPv4（可带端口，不含 scheme/path/userinfo）；`--ac-id` 为正整数。可用既有设置需要合法 TOML 和这四个字段。`--force --dry-run --json` 可预览备份/替换计划；确认后去掉 `--dry-run`。备份不会自动还原；系统 I/O 失败可能留下部分文件，可检查 JSON/路径后重试。

## 访客账号 {#visitor}

```bash
ecnu visitor list
ecnu visitor get --id 10256703
ecnu visitor create --remark GuestA --dry-run -I
ecnu visitor default -I
```

修改类命令支持 `--dry-run`。
