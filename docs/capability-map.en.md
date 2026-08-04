# Capability Map

This page answers “what does ChatECNU own?”. Invocation details live in [CLI Tree](cli-tree.md); Python / CLI mapping lives in [Interface Tree](interface-tree.md).

## Current capabilities

<div class="grid cards" markdown>

- **Portal session**

  Login, CAPTCHA bootstrap, session status, and logout.

- **Portal reads**

  Home summary, user info, auth logs, and detail logs.

- **Visitor accounts**

  List, get, create, maintain defaults, update, and delete.

- **Network login**

  Wrap an external `auth_client` with check, login, and ensure-login flows.

</div>

## Capability boundaries

| Capability | Status | Entry | Boundary |
| --- | --- | --- | --- |
| Portal login | Implemented | `chatecnu login` | Requires ECNU credentials and CAPTCHA flow |
| Session reads | Implemented | `status`, `home`, `user-info` | Requires a session or Cookie |
| Visitor accounts | Implemented | `chatecnu visitor ...` | Mutation commands support `--dry-run` |
| Network check | Implemented | `chatecnu auth check` | Does not need a password |
| Network login | Implemented | `auth login`, `auth ensure-login` | Refuses argv passwords by default |
| ChatEnv config | Implemented | `ECNUConfig` | Passwords and Cookies are sensitive fields |

## Safety defaults

- ChatECNU does not bundle the Linux-only `auth_client` binary.
- ChatECNU does not pass ECNU passwords to `auth_client -p PASSWORD` by default.
- The legacy path requires explicit `--allow-argv-password` / `allow_argv_password=True`.
- stdout, stderr, JSON payloads, and redacted commands mask resolved passwords.
- Process env wins over default ChatEnv; explicit `-e` / `--env-file` selects a specific config.

## Out of scope

| Item | Owner |
| --- | --- |
| Generic network foundations | ChatNet |
| DNS, certificates, Nginx, domain entry | ChatDNS / operations projects |
| Bundling or redistributing `auth_client` | Not supported |
| Provisioning ECNU accounts or changing school systems | Not supported |

## Verification entry points

```bash
python -m pytest -q
mkdocs build --strict
chatecnu auth check --auth-client /usr/local/bin/auth_client --json
```
