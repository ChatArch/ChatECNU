# Capability Map

## Current Capabilities

| Capability | Status | Entry | Boundary |
| --- | --- | --- | --- |
| Portal login | Implemented | `ecnu home login` | Creates an ECNU Web/API session |
| Portal reads | Implemented | `ecnu home info/status/user` | Requires a logged-in portal session in the token store |
| Visitor accounts | Implemented | `ecnu visitor ...` | Mutation commands support `--dry-run` |
| Offline network setup | Implemented | `ecnu net install` | Native Linux x86_64; no login/download; dry-run and backed-up force |
| Network check | Implemented | `ecnu net check` | Does not need a password |
| Campus network access | Implemented | `ecnu net login/logout/ensure-login` | Native Python HTTP by default; explicit binary compatibility only |
| ChatEnv config | Implemented | `ecnu` type | Passwords live in stable env; portal sessions/cookies live in the runtime token store |

## Boundaries

- Portal login is not campus-network access; it only manages the ECNU portal session.
- `net` is not portal login; it only manages local campus-network access.
- `ECNU_NETWORK_BACKEND=python` is the default: SRun HTTP runs directly, without `auth_client` or password-bearing child-process argv. It reuses ChatEnv `ECNU_USERNAME` / `ECNU_PASSWORD` and native `ECNU_NETWORK_BASE_URL` / `ECNU_NETWORK_AC_ID`; Python imports legacy settings only with explicit `--setting-file`; login/logout verify the resulting online state and JSON reports `backend=python`. Only explicit `ECNU_NETWORK_BACKEND=binary` uses the legacy binary, where login still requires `--allow-argv-password`; `--auth-client` / `ECNU_AUTH_CLIENT` apply only to binary. The default Python path does not require `net install`.
- stdout, stderr, JSON payloads, and redacted commands mask resolved passwords.
- Portal sessions, cookies, and CSRF state are written to `tokens/ECNU/<profile>.json`, not to a stable `ECNU_COOKIE` env field.
- Process env wins over default ChatEnv; explicit `-e` / `--env-file` selects a specific config.

## Verification Entry Points

```bash
python -m pytest -q
mkdocs build --strict
ecnu net check --json
```
