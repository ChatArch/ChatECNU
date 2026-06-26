# ChatECNU

ChatECNU is the ChatArch ECNU campus portal automation package extracted from ChatNet.

It owns ECNU application-layer behavior: login/session handling, home/user/log reads, visitor account operations, ECNU ChatEnv schema, and optional CAPTCHA automation. Generic browser/session/table helpers are imported from `ChatNet`.

## Quick start

```bash
pip install -e ".[dev]"
chatecnu --help
python -m pytest -q
```

Optional CAPTCHA automation:

```bash
pip install -e ".[captcha]"
chatecnu login --username "$ECNU_USERNAME" --password "$ECNU_PASSWORD"
```

Sensitive values such as passwords, cookies, SMS codes, and session tokens must not be printed or committed.
