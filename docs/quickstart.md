# 快速开始

## 安装

```bash
pip install -e ".[dev,docs]"
chatecnu --help
```

可选验证码识别：

```bash
pip install -e ".[captcha]"
```

## 配置

ChatECNU 使用 ChatEnv 的 `ecnu` 类型：

```bash
chatenv test -t ecnu
chatenv cat -t ecnu
```

常用字段：

```text
ECNU_USERNAME
ECNU_PASSWORD
ECNU_COOKIE
ECNU_AUTH_CLIENT
ECNU_AUTH_SETTING_FILE
```

敏感字段会脱敏显示。

## 最小检查

```bash
chatecnu status
chatecnu home
chatecnu user-info
```

校园网状态检查不需要密码：

```bash
chatecnu auth check --auth-client /usr/local/bin/auth_client --json
```

## 安全默认值

`auth_client` 的旧登录接口需要把密码放入进程参数。ChatECNU 默认拒绝这条路径。只有明确接受本机进程列表暴露风险时，才加：

```bash
--allow-argv-password
```
