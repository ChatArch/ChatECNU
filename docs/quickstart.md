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

`pip install` 不会改用户文件；Linux x86_64 需显式执行下面的离线安装器（`chatecnu net install` 与 `ecnu net install` 为同一入口）：

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
ecnu net ensure-login -I --allow-argv-password
```

`check` 不需要密码。`login` / `ensure-login` 默认不把密码放入外部进程参数；只有明确接受本机进程列表暴露风险后才使用 `--allow-argv-password`。
