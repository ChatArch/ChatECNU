# Capability Map

## Current Capabilities

| Capability | Status | Entry | Boundary |
| --- | --- | --- | --- |
| Portal login | Implemented | `ecnu home login` | Creates an ECNU Web/API session |
| Portal reads | Implemented | `ecnu home info/status/user` | Requires a logged-in portal session in the token store |
| Visitor accounts | Implemented | `ecnu visitor ...` | Mutation commands support `--dry-run` |
| Network check | Implemented | `ecnu net check` | Does not need a password |
| Campus network access | Implemented | `ecnu net login/logout/ensure-login` | Bundles Linux x86_64 `auth_client`; refuses argv passwords by default |
| ChatEnv config | Implemented | `ecnu` type | Passwords live in stable env; portal sessions/cookies live in the runtime token store |

## Boundaries

- Portal login is not campus-network access; it only manages the ECNU portal session.
- `net` is not portal login; it only manages local campus-network access.
- ChatECNU distributes the Linux x86_64 `auth_client` in PyPI wheel/sdist; `--auth-client` / `ECNU_AUTH_CLIENT` can still override the path.
- stdout, stderr, JSON payloads, and redacted commands mask resolved passwords.
- Portal sessions, cookies, and CSRF state are written to `tokens/ECNU/<profile>.json`, not to a stable `ECNU_COOKIE` env field.
- Process env wins over default ChatEnv; explicit `-e` / `--env-file` selects a specific config.

## Verification Entry Points

```bash
python -m pytest -q
mkdocs build --strict
ecnu net check --json
```
