# 快速开始

## 安装

```bash
pip install ChatECNU
```

需要验证码识别时安装：

```bash
pip install "ChatECNU[captcha]"
```

## 准备 ChatEnv

ChatECNU 的 ChatEnv 类型是 `ecnu`。

```bash
chatenv list
chatenv new default -t ecnu -I --yes
```

常用变量：

```text
ECNU_USERNAME=你的学号或账号
ECNU_PASSWORD=你的密码
```

完整变量见 [ChatEnv 变量](chatenv.md)。

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
