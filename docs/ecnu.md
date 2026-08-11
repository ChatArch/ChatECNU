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

## 校园网联网 {#network-login}

校园网联网管理本机网络出口认证，底层优先使用 PyPI 包内置的 Linux x86_64 `auth_client`。

```bash
ecnu net check --json
ecnu net login -I --allow-argv-password
ecnu net logout -I
ecnu net ensure-login -I --allow-argv-password
```

`check` 不需要密码。`login` 和门户登录共用 `ECNU_USERNAME` / `ECNU_PASSWORD`；`logout` 只需要用户名。默认不传 `-c`，只有配置 `--setting-file` 或 `ECNU_AUTH_SETTING_FILE` 时才使用设置文件。

## 访客账号 {#visitor}

```bash
ecnu visitor list
ecnu visitor get --id 10256703
ecnu visitor create --remark GuestA --dry-run -I
ecnu visitor default -I
```

修改类命令支持 `--dry-run`。
