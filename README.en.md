# ChatECNU

ChatECNU is the ChatArch ECNU portal and campus-network automation package. It owns ECNU login, session state, home/user reads, visitor accounts, and a safe wrapper for an external Linux `auth_client` binary. Generic network helpers belong to ChatNet.

Docs: https://arch.gh.wzhecnu.cn/ChatECNU/en/

Chinese README: [README.md](README.md).

## Documentation entry points

| Goal | Entry |
| --- | --- |
| Install and smoke test | https://arch.gh.wzhecnu.cn/ChatECNU/en/quickstart/ |
| Review commands | https://arch.gh.wzhecnu.cn/ChatECNU/en/cli-tree/ |
| Check package boundaries | https://arch.gh.wzhecnu.cn/ChatECNU/en/capability-map/ |
| Review Python / CLI interfaces | https://arch.gh.wzhecnu.cn/ChatECNU/en/interface-tree/ |
| Portal, visitor accounts, and network login | https://arch.gh.wzhecnu.cn/ChatECNU/en/ecnu/ |

## Quickstart

```bash
pip install -e ".[dev,docs]"
chatecnu --help
python -m pytest -q
```

Optional CAPTCHA recognition:

```bash
pip install -e ".[captcha]"
chatecnu login --username "$ECNU_USERNAME" -i
```

## Common commands

```bash
chatecnu status
chatecnu login -I
chatecnu home
chatecnu user-info
chatecnu visitor --help
```

Network login wrapper:

```bash
# Check status; no password needed.
chatecnu auth check --auth-client /usr/local/bin/auth_client --json

# Credentials come from env, ChatEnv, or prompts. Default login is fail-closed.
chatecnu auth ensure-login --auth-client /usr/local/bin/auth_client -I

# Enable the legacy argv-password path only after accepting local exposure.
chatecnu auth ensure-login --auth-client /usr/local/bin/auth_client --allow-argv-password -I
```

ChatECNU does not bundle `auth_client`. Use `--auth-client` or `ECNU_AUTH_CLIENT`. The old `network-auth` command remains as a hidden compatibility alias.

Do not print or commit passwords, cookies, SMS codes, or sessions.
