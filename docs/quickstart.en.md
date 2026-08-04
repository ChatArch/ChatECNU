# Quickstart

## Install

```bash
pip install -e ".[dev,docs]"
chatecnu --help
```

Optional CAPTCHA recognition:

```bash
pip install -e ".[captcha]"
```

## Configure

ChatECNU uses the ChatEnv `ecnu` type:

```bash
chatenv test -t ecnu
chatenv cat -t ecnu
```

Common fields:

```text
ECNU_USERNAME
ECNU_PASSWORD
ECNU_COOKIE
ECNU_AUTH_CLIENT
ECNU_AUTH_SETTING_FILE
```

Sensitive fields are masked.

## Small checks

```bash
chatecnu status
chatecnu home
chatecnu user-info
```

Network status checks do not need a password:

```bash
chatecnu auth check --auth-client /usr/local/bin/auth_client --json
```

## Safety default

The legacy `auth_client` login path puts the password in process arguments. ChatECNU refuses that path by default. Add this flag only after accepting local process-list exposure:

```bash
--allow-argv-password
```
