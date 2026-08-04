# ChatECNU

ChatECNU 是 ChatArch 的 ECNU 门户和校园网自动化包。它负责 ECNU 登录、会话、首页、用户信息、访客账号，以及外部 Linux `auth_client` 的安全包装。通用网络能力归 ChatNet。

文档：https://arch.gh.wzhecnu.cn/ChatECNU/

英文版见 [README.en.md](README.en.md)。

## 文档入口

| 场景 | 入口 |
| --- | --- |
| 安装和最小验证 | https://arch.gh.wzhecnu.cn/ChatECNU/quickstart/ |
| 查看命令面 | https://arch.gh.wzhecnu.cn/ChatECNU/cli-tree/ |
| 判断包能力边界 | https://arch.gh.wzhecnu.cn/ChatECNU/capability-map/ |
| 查看 Python 与命令行接口 | https://arch.gh.wzhecnu.cn/ChatECNU/interface-tree/ |
| 门户、访客账号、校园网登录 | https://arch.gh.wzhecnu.cn/ChatECNU/ecnu/ |

## 快速开始

```bash
pip install -e ".[dev,docs]"
chatecnu --help
python -m pytest -q
```

可选验证码识别：

```bash
pip install -e ".[captcha]"
chatecnu login --username "$ECNU_USERNAME" -i
```

## 常用命令

```bash
chatecnu status
chatecnu login -I
chatecnu home
chatecnu user-info
chatecnu visitor --help
```

校园网登录包装：

```bash
# 查状态，不需要密码。
chatecnu auth check --auth-client /usr/local/bin/auth_client --json

# 凭据来自环境变量、ChatEnv 或交互输入；默认不把密码传给 auth_client。
chatecnu auth ensure-login --auth-client /usr/local/bin/auth_client -I

# 明确接受 argv 暴露风险后才启用旧接口。
chatecnu auth ensure-login --auth-client /usr/local/bin/auth_client --allow-argv-password -I
```

ChatECNU 不打包 `auth_client`。请用 `--auth-client` 或 `ECNU_AUTH_CLIENT` 指定路径。旧命令 `network-auth` 仍作为隐藏兼容别名可用。

敏感值（密码、Cookie、短信码、会话）不要打印或提交。
