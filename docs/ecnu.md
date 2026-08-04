# ChatECNU ECNU 使用文档

`chatecnu` 用于脚本化访问 ECNU 自助服务平台，覆盖登录、会话、首页与日志查询，以及访客账号管理。

## 1. 安装

基础功能需要 HTTP 请求与 RSA 加密依赖：

```bash
pip install -e .
```

如果要使用自动验证码登录，需要安装可选 OCR extra：

```bash
pip install -e ".[captcha]"
```

安装后先确认 CLI 可用：

```bash
chatecnu --help
chatecnu --help
```

默认帮助只展示日常使用命令。`selftest` 等诊断命令仍可直接调用，但不会出现在常规帮助中。

## 2. 配置

ECNU 配置遵循 chatenv typed env 规范，默认 active 配置文件为：

```text
~/.chatarch/envs/ECNU/.env
```

支持字段：

```bash
ECNU_USERNAME='your-ecnu-username'
ECNU_PASSWORD='your-ecnu-password'
ECNU_COOKIE=''
ECNU_BASE_URL='https://login.ecnu.edu.cn:8800'
ECNU_VISITOR_PASSWORD1=''
ECNU_VISITOR_PASSWORD2=''
ECNU_VISITOR_REMARK='default'
ECNU_AUTH_CLIENT='auth_client'
ECNU_AUTH_SETTING_FILE='auth_setting'
```

查看配置时默认会 mask 敏感字段：

```bash
chatenv cat -t ecnu
```

验证 provider 是否可被 chatenv 发现：

```bash
chatenv test -t ecnu
```

`chatenv test -t ecnu` 只做本地配置 schema/provider 检查，不访问 ECNU 站点。

如果需要维护多个 profile：

```bash
chatenv save work -t ecnu
chatenv use work -t ecnu
chatecnu -e work status
```

也可以用临时 env 文件覆盖：

```bash
chatecnu --env-file ./ecnu.env status
```

## 3. 默认文件位置

默认会话文件：

```text
~/.chatarch/cache/chatecnu/ecnu-session.json
```

默认验证码图片：

```text
~/.chatarch/cache/chatecnu/ecnu-login-captcha.png
```

如需隔离会话，可显式指定：

```bash
chatecnu --state-file ./ecnu-session.json status
```

## 4. 登录

### 默认登录

推荐使用：

```bash
chatecnu login --rounds 3 --topk 5 -I
```

默认逻辑：

- 每轮下载一张验证码。
- OCR 生成 top-k 候选。
- 候选失败后继续尝试，全部失败后刷新验证码。
- 如果服务端要求短信验证码，需要通过 `--sms-code` 提供。
- 默认输出人类可读摘要；如果要原始结构，显式加 `--json`。

```bash
chatecnu login --sms-code 123456 --rounds 3 --topk 5 -I
```

### 手动验证码登录（高级）

自动 OCR 不可用时，可以直接调用隐藏的 `login-init` 诊断命令下载验证码：

```bash
chatecnu login-init
```

查看默认验证码图片后提交：

```bash
chatecnu login --captcha ABCD -I
```

如果不使用 chatenv，也可以显式传参：

```bash
chatecnu login --username "your-ecnu-username" --password "your-password" --captcha ABCD -I
```

### 查看会话

```bash
chatecnu status
```

`status` 默认输出摘要。需要原始结构时使用 `--json`。需要本地调试时，仍可直接调用隐藏的 `cookie-header` 命令导出 Cookie header：

```bash
chatecnu cookie-header
```

`cookie-header` 会输出敏感会话信息，只用于本地调试。

退出登录：

```bash
chatecnu logout
```

## 5. 校园网登录

ChatECNU 只包装外部 Linux `auth_client`，不打包它。默认不把密码传给 `auth_client -p PASSWORD`。

检查状态，不需要密码：

```bash
chatecnu auth check \
  --auth-client /usr/local/bin/auth_client \
  --json
```

替代定时脚本：

```bash
# 凭据来自 env/ChatEnv 或 -i。默认 fail-closed。
chatecnu auth ensure-login \
  --auth-client /usr/local/bin/auth_client \
  -I
```

接受 argv 暴露风险后，才开 legacy 兼容：

```bash
chatecnu auth ensure-login \
  --auth-client /usr/local/bin/auth_client \
  --allow-argv-password \
  -I
```

`ensure-login` 先 `check`，在线就跳过。默认不传 `-c`，除非配置 `--setting-file` / `ECNU_AUTH_SETTING_FILE`。调用使用 argv list + `shell=False`，输出会 redact 密码。显式 `-e/--env-file` 时优先读对应配置。旧 `network-auth` 仍是 `auth` 的隐藏兼容别名。

如果固定部署路径，可写入 ChatEnv：

```bash
ECNU_AUTH_CLIENT='/usr/local/bin/auth_client'
ECNU_USERNAME='<your-ecnu-id>'
ECNU_PASSWORD='<your-ecnu-password>'
# Optional, only if this deployment uses a setting file:
# ECNU_AUTH_SETTING_FILE='auth_setting'
```

## 6. 查询

首页摘要：

```bash
chatecnu home
```

用户信息：

```bash
chatecnu user-info
```

认证日志和上网明细已经下沉到隐藏的 debug 路径，不在常规 help 中展示：

```bash
chatecnu debug auth-log --limit 10
chatecnu debug auth-log --start "2026-06-01 00:00:00" --end "2026-06-15 23:59:59" --limit 10
chatecnu debug detail-log --limit 10
chatecnu debug detail-log --start "2026-06-01 00:00:00" --end "2026-06-15 23:59:59" --limit 10
```

## 7. 访客管理

### 列表与查询

```bash
chatecnu visitor list
chatecnu visitor get --id 10256703
chatecnu visitor get --account 20260000000m2
```

### 创建访客

访客创建是账号签发步骤，服务端会生成访客账号和初始密码：

```bash
chatecnu visitor create --remark GuestA -I
```

备注约束来自页面校验：2-14 位中文或英文字符。

### 默认访客账号

如果希望固定维护当前账号下的默认访客账号，可以配置：

```bash
ECNU_VISITOR_PASSWORD1='Temp!235'
ECNU_VISITOR_PASSWORD2='Temp!236'
ECNU_VISITOR_REMARK='default'
```

然后运行：

```bash
chatecnu visitor default -I
```

行为规则：

- 只有 `ECNU_VISITOR_PASSWORD1` 时，维护 `<ECNU_USERNAME>m1`
- 同时存在 `ECNU_VISITOR_PASSWORD1` 和 `ECNU_VISITOR_PASSWORD2` 时，维护 `<ECNU_USERNAME>m1` 与 `<ECNU_USERNAME>m2`
- 如果目标账号不存在，命令会先创建，再按对应密码更新
- 也可以用参数覆盖：

```bash
chatecnu visitor default --password1 'Temp!235' --password2 'Temp!236' --remark default -I
```

### 编辑访客密码

如果要设置最终密码，需要对创建后的访客 `id` 执行编辑：

```bash
chatecnu visitor update --id 10256703 --remark GuestA --password 'Temp!235' -I
```

密码约束：

- 8-20 位。
- 包含字母、数字和特殊字符。

标准验收流程是：

```bash
chatecnu login --rounds 3 --topk 5 -I
chatecnu visitor create --remark GuestA -I
chatecnu visitor list
chatecnu visitor update --id <created-id> --remark GuestA --password '<final-password>' -I
chatecnu visitor list
```

### 删除

```bash
chatecnu visitor delete --id 10256703 -I
```

修改类命令支持 `--dry-run`：

```bash
chatecnu visitor create --remark GuestA --dry-run -I
chatecnu visitor update --id 10256703 --remark GuestA --password 'Temp!235' --dry-run -I
chatecnu visitor delete --id 10256703 --dry-run -I
```

`visitor lock` 属于低频管理动作，仍可直接调用，但默认不在 `visitor --help` 中展示。

## 8. 交互规范

命令遵循 ChatArch CLI 规范：

- 缺少可恢复参数时，TTY 下会进入交互补问。
- `-i` 强制交互。
- `-I` 禁止交互并快速失败。
- 密码类字段在交互中使用敏感输入。

CI 或脚本中建议使用 `-I`，避免意外等待输入。

## 9. 故障排查

### 缺少 OCR 依赖

如果 `login` 报缺少验证码依赖：

```bash
pip install -e ".[captcha]"
```

### 登录后跳回登录页

通常表示会话失效，重新登录：

```bash
chatecnu login --rounds 3 --topk 5 -I
```

### 服务端要求短信验证码

补充 `--sms-code`：

```bash
chatecnu login --sms-code 123456 -I
```

### 访客创建没有新增记录

先查看当前数量：

```bash
chatecnu visitor list
```

如果平台限制访客数量，需要删除旧访客后再创建：

```bash
chatecnu visitor delete --id <old-id> -I
chatecnu visitor create --remark GuestA -I
```

### 查看请求规格但不提交

使用 `--dry-run`：

```bash
chatecnu visitor create --remark GuestA --dry-run -I
```

## 10. 安全注意事项

- 不要把真实账号、密码、Cookie、短信验证码、访客密码写入代码、测试或公开文档。
- 本仓库示例统一使用虚构账号，例如 `20260000000m2`。
- `~/.chatarch/envs/ECNU/.env` 和 session 文件应只保存在本机。
- `cookie-header` 输出是敏感信息，使用后不要贴到 issue、PR 或日志。
- `--cookie`、`--state-file`、`--env-file`、`--base-url` 等高级选项仍可用于本地调试/隔离验证，但默认不在 help 中暴露。
- `login-auto`、`auth-log`、`detail-log` 仍保留为隐藏兼容/debug 路径，但普通使用应优先走 `login` 与其余顶层摘要命令。
- `visitor default` 依赖 `ECNU_USERNAME` 与 `ECNU_VISITOR_PASSWORD1`；如果要维护第二个默认访客，再加 `ECNU_VISITOR_PASSWORD2`。
