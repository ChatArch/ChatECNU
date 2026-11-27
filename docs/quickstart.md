# 快速开始

## 安装

```bash
pip install ChatECNU
```

需要验证码识别时安装：

```bash
pip install "ChatECNU[captcha]"
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

## 准备 ChatEnv

ChatECNU 的 ChatEnv 类型是 `ecnu`。

```bash
chatenv list
chatenv init -t ecnu -I
```

常用变量：

```text
ECNU_USERNAME=你的学号或账号
ECNU_PASSWORD=你的密码
```

完整变量见 [ChatEnv 变量](chatenv.md)。

## CLI 最小验证

```bash
ecnu --version
ecnu --tree
ecnu --tree-brief
```

## 门户最小验证

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
```

## 校园网最小验证

```bash
ecnu net check --json
ecnu net ensure-login -I
```

默认 `ECNU_NETWORK_BACKEND=python`：直接执行 SRun HTTP 协议，不运行 `auth_client`，不通过外部进程 argv 传密码。复用 ChatEnv 的 `ECNU_USERNAME` / `ECNU_PASSWORD` 及原生 `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`；Python 仅在显式 `--setting-file` 时导入旧格式；登录/退出后重新检查实际在线状态，JSON 返回 `backend=python`。只有显式选择 `ECNU_NETWORK_BACKEND=binary` 才使用旧二进制，且登录仍需 `--allow-argv-password`；`--auth-client` / `ECNU_AUTH_CLIENT` 也仅作用于 binary。默认 Python 路径不需要 `net install`。

## macOS 定时自动重登

自动重登属于现有 `ecnu net ensure-login`（兼容入口 `chatecnu net ensure-login`），不新增 CLI。

```bash
# 只预览，不写配置或启动任务
ecnu net ensure-login --install-service --interval 60 --dry-run --json
# 安装并启动当前用户 LaunchAgent
ecnu net ensure-login --install-service --interval 60
# 查看服务与最近一次检测结果
ecnu net ensure-login --service-status --json
# 停止并卸载任务，保留 ChatEnv 配置
ecnu net ensure-login --uninstall-service
```

服务遵循 macOS 当前系统路由。系统选择哪张网卡，检测、登录和自动重登就使用哪张网卡；CLI 不保存或指定网卡。`--probe-url` 默认使用 `https://www.baidu.com/`，通过 HTTPS 检测外网，不依赖 ICMP ping。

服务每隔 `--interval` 秒（默认 60）运行一次，直接调用安装包 `python -m chatecnu net ensure-login`。只有连续两次外网检测失败且校园网明确返回未认证才尝试登录；未知认证状态、已认证但外网故障、缺少 ChatEnv 凭据均不会盲目重登。重试间隔至少五分钟，检测加锁以防并发。

凭据始终从选定的 ChatEnv ECNU profile 的 `ECNU_USERNAME` / `ECNU_PASSWORD` 加载；没有 `-e` 时使用 active profile。服务配置不保存账号或密码，每次后台检查都会重新读取 ChatEnv。安装前请先用 `chatenv` 配置 ECNU profile；无需在 `ensure-login` 命令中输入账号密码。

配置与状态在 `$CHATARCH_HOME/chatecnu/wifi-autologin/`，任务文件在 `~/Library/LaunchAgents/com.chatarch.ecnu.wifi-autologin.plist`。重装会备份旧配置与任务文件，旧服务配置中的账号快照会被清除。服务运行在这台 Mac 上，关机、休眠或退出用户会话期间不检测。
