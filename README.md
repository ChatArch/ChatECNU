# ChatECNU

ChatECNU is the ChatArch ECNU campus portal and campus-network automation package extracted from ChatNet.

It owns ECNU application-layer behavior: login/session handling, home/user/log reads, visitor account operations, ECNU ChatEnv schema, optional CAPTCHA automation, and a fail-closed wrapper around the external ECNU campus-network `auth_client` binary. Generic browser/session/table helpers are imported from `ChatNet`.

## Quick start

```bash
pip install -e ".[dev]"
chatecnu --help
python -m pytest -q
```

Optional CAPTCHA automation:

```bash
pip install -e ".[captcha]"
chatecnu login --username "$ECNU_USERNAME" -i
```

Network login:

```bash
# Check status; no password needed.
chatecnu auth check \
  --auth-client /usr/local/bin/auth_client \
  --json

# Use env/ChatEnv or -i. Default login is fail-closed.
chatecnu auth ensure-login \
  --auth-client /usr/local/bin/auth_client \
  -I

# Legacy opt-in after accepting argv exposure:
chatecnu auth ensure-login \
  --auth-client /usr/local/bin/auth_client \
  --allow-argv-password \
  -I
```

ChatECNU does not vendor the Linux-only `auth_client`. Pass `--auth-client` or set `ECNU_AUTH_CLIENT`. Set `ECNU_AUTH_SETTING_FILE` only when needed; otherwise checks use bare `auth_client check`. Login refuses argv passwords unless `--allow-argv-password` / `allow_argv_password=True` is set. Old `network-auth` still works as a hidden alias for `auth`.

Sensitive values such as passwords, cookies, SMS codes, and session tokens must not be printed or committed.
