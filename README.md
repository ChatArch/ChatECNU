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

Campus-network `auth_client` wrapper:

```bash
# Put ECNU_USERNAME/ECNU_PASSWORD in process env or ChatEnv, or use -i to prompt.
# Default login is fail-closed: it will not pass a password to auth_client argv.
chatecnu network-auth ensure-login \
  --auth-client /usr/local/bin/auth_client \
  --setting-file auth_setting \
  -I

# Legacy opt-in only after accepting same-host process-list exposure:
chatecnu network-auth ensure-login \
  --auth-client /usr/local/bin/auth_client \
  --setting-file auth_setting \
  --allow-argv-password \
  -I
```

ChatECNU does not vendor or redistribute the Linux-only `auth_client` binary. Pass its runtime path explicitly or set `ECNU_AUTH_CLIENT` in ChatEnv. The upstream binary appears to accept passwords only through `-p PASSWORD`; therefore ChatECNU refuses login by default and requires `--allow-argv-password` / `allow_argv_password=True` for the legacy wrapper path.

Sensitive values such as passwords, cookies, SMS codes, and session tokens must not be printed or committed.
