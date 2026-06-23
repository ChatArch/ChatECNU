# ChatNet ECNU 使用文档

`chatnet ecnu` 用于脚本化访问 ECNU 自助服务平台，覆盖登录、会话、首页与日志查询，以及访客账号管理。

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
chatnet --help
chatnet ecnu --help
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
chatnet ecnu -e work status
```

也可以用临时 env 文件覆盖：

```bash
chatnet ecnu --env-file ./ecnu.env status
```

## 3. 默认文件位置

默认会话文件：

```text
~/.chatarch/cache/chatnet/ecnu-session.json
```

默认验证码图片：

```text
~/.chatarch/cache/chatnet/ecnu-login-captcha.png
```

如需隔离会话，可显式指定：

```bash
chatnet ecnu --state-file ./ecnu-session.json status
```

## 4. 登录

### 默认登录

推荐使用：

```bash
chatnet ecnu login --rounds 3 --topk 5 -I
```

默认逻辑：

- 每轮下载一张验证码。
- OCR 生成 top-k 候选。
- 候选失败后继续尝试，全部失败后刷新验证码。
- 如果服务端要求短信验证码，需要通过 `--sms-code` 提供。
- 默认输出人类可读摘要；如果要原始结构，显式加 `--json`。

```bash
chatnet ecnu login --sms-code 123456 --rounds 3 --topk 5 -I
```

### 手动验证码登录（高级）

自动 OCR 不可用时，可以直接调用隐藏的 `login-init` 诊断命令下载验证码：

```bash
chatnet ecnu login-init
```

查看默认验证码图片后提交：

```bash
chatnet ecnu login --captcha ABCD -I
```

如果不使用 chatenv，也可以显式传参：

```bash
chatnet ecnu login --username "your-ecnu-username" --password "your-password" --captcha ABCD -I
```

### 查看会话

```bash
chatnet ecnu status
```

`status` 默认输出摘要。需要原始结构时使用 `--json`。需要本地调试时，仍可直接调用隐藏的 `cookie-header` 命令导出 Cookie header：

```bash
chatnet ecnu cookie-header
```

`cookie-header` 会输出敏感会话信息，只用于本地调试。

退出登录：

```bash
chatnet ecnu logout
```

## 5. 查询

首页摘要：

```bash
chatnet ecnu home
```

用户信息：

```bash
chatnet ecnu user-info
```

认证日志和上网明细已经下沉到隐藏的 debug 路径，不在常规 help 中展示：

```bash
chatnet ecnu debug auth-log --limit 10
chatnet ecnu debug auth-log --start "2026-06-01 00:00:00" --end "2026-06-15 23:59:59" --limit 10
chatnet ecnu debug detail-log --limit 10
chatnet ecnu debug detail-log --start "2026-06-01 00:00:00" --end "2026-06-15 23:59:59" --limit 10
```

## 6. 访客管理

### 列表与查询

```bash
chatnet ecnu visitor list
chatnet ecnu visitor get --id 10256703
chatnet ecnu visitor get --account 20260000000m2
```

### 创建访客

访客创建是账号签发步骤，服务端会生成访客账号和初始密码：

```bash
chatnet ecnu visitor create --remark GuestA -I
```

备注约束来自页面校验：2-14 位中文或英文字符。

### 编辑访客密码

如果要设置最终密码，需要对创建后的访客 `id` 执行编辑：

```bash
chatnet ecnu visitor update --id 10256703 --remark GuestA --password 'Temp!235' -I
```

密码约束：

- 8-20 位。
- 包含字母、数字和特殊字符。

标准验收流程是：

```bash
chatnet ecnu login --rounds 3 --topk 5 -I
chatnet ecnu visitor create --remark GuestA -I
chatnet ecnu visitor list
chatnet ecnu visitor update --id <created-id> --remark GuestA --password '<final-password>' -I
chatnet ecnu visitor list
```

### 删除

```bash
chatnet ecnu visitor delete --id 10256703 -I
```

修改类命令支持 `--dry-run`：

```bash
chatnet ecnu visitor create --remark GuestA --dry-run -I
chatnet ecnu visitor update --id 10256703 --remark GuestA --password 'Temp!235' --dry-run -I
chatnet ecnu visitor delete --id 10256703 --dry-run -I
```

`visitor lock` 属于低频管理动作，仍可直接调用，但默认不在 `visitor --help` 中展示。

## 7. 交互规范

命令遵循 ChatArch CLI 规范：

- 缺少可恢复参数时，TTY 下会进入交互补问。
- `-i` 强制交互。
- `-I` 禁止交互并快速失败。
- 密码类字段在交互中使用敏感输入。

CI 或脚本中建议使用 `-I`，避免意外等待输入。

## 8. 故障排查

### 缺少 OCR 依赖

如果 `login` 报缺少验证码依赖：

```bash
pip install -e ".[captcha]"
```

### 登录后跳回登录页

通常表示会话失效，重新登录：

```bash
chatnet ecnu login --rounds 3 --topk 5 -I
```

### 服务端要求短信验证码

补充 `--sms-code`：

```bash
chatnet ecnu login --sms-code 123456 -I
```

### 访客创建没有新增记录

先查看当前数量：

```bash
chatnet ecnu visitor list
```

如果平台限制访客数量，需要删除旧访客后再创建：

```bash
chatnet ecnu visitor delete --id <old-id> -I
chatnet ecnu visitor create --remark GuestA -I
```

### 查看请求规格但不提交

使用 `--dry-run`：

```bash
chatnet ecnu visitor create --remark GuestA --dry-run -I
```

## 9. 安全注意事项

- 不要把真实账号、密码、Cookie、短信验证码、访客密码写入代码、测试或公开文档。
- 本仓库示例统一使用虚构账号，例如 `20260000000m2`。
- `~/.chatarch/envs/ECNU/.env` 和 session 文件应只保存在本机。
- `cookie-header` 输出是敏感信息，使用后不要贴到 issue、PR 或日志。
- `--cookie`、`--state-file`、`--env-file`、`--base-url` 等高级选项仍可用于本地调试/隔离验证，但默认不在 help 中暴露。
- `login-auto`、`auth-log`、`detail-log` 仍保留为隐藏兼容/debug 路径，但普通使用应优先走 `login` 与其余顶层摘要命令。
