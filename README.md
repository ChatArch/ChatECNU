# ChatECNU

ChatECNU 是 ECNU 门户与校园网联网工具包。安装包名仍是 `ChatECNU`，日常命令主推 `ecnu`。

## 文档入口

| 任务 | 链接 |
| --- | --- |
| 安装和最小验证 | https://arch.gh.wzhecnu.cn/ChatECNU/quickstart/ |
| 命令树 | https://arch.gh.wzhecnu.cn/ChatECNU/cli-tree/ |
| ChatEnv 变量 | https://arch.gh.wzhecnu.cn/ChatECNU/chatenv/ |
| ECNU 使用 | https://arch.gh.wzhecnu.cn/ChatECNU/ecnu/ |

## 安装

```bash
pip install ChatECNU
```

如需验证码识别能力：

```bash
pip install "ChatECNU[captcha]"
```

## 命令结构

```text
ecnu
├── home      # ECNU 门户
├── net       # 校园网联网
└── visitor   # 访客账号
```

门户命令统一放在 `home` 下：

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

校园网联网统一放在 `net` 下：

```bash
ecnu net check --json
ecnu net login -I --allow-argv-password
ecnu net logout -I
ecnu net ensure-login -I --allow-argv-password
```

ChatECNU 的 PyPI wheel/sdist 内置 Linux x86_64 `auth_client`，默认 `ecnu net ...` 会优先使用该内置二进制；如需覆盖，可用 `--auth-client` 或 `ECNU_AUTH_CLIENT` 指定路径。账号密码使用同一组 `ECNU_USERNAME` / `ECNU_PASSWORD`。`net check` 会显示当前 `online/account/username`；`net logout` 未提供用户名时会先从 `auth_client check` 的 `Username=...` 自动提取。

敏感值（密码、Cookie、短信码、会话）不要打印或提交。
