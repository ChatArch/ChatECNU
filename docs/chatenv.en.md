# ChatEnv Variables

ChatECNU registers the ChatEnv type `ecnu`. Portal access and campus-network access share the same ECNU username and password. Stable configuration is stored in `~/.chatarch/envs/ECNU/<profile>.env`; dynamic portal Web/API session state, cookies, and CSRF payloads are stored in ChatEnv's runtime token store at `~/.chatarch/tokens/ECNU/<profile>.json`.

## Common Commands

```bash
chatenv list
chatenv init -t ecnu -I
```

`-e/--env` selects a ChatEnv profile for the current command without switching the global active profile. Explicit profile values take precedence to avoid cross-account leakage.

## Variables

| Variable | Purpose | Sensitive |
| --- | --- | --- |
| `ECNU_USERNAME` | Shared portal and network username | No |
| `ECNU_PASSWORD` | Shared portal and network password | Yes |
| `ECNU_BASE_URL` | Portal base URL | No |
| `ECNU_AUTH_CLIENT` | Optional auth_client override path; defaults to the PyPI-bundled binary | No |
| `ECNU_AUTH_SETTING_FILE` | Optional setting file | No |
| `ECNU_VISITOR_PASSWORD1` | First default visitor password | Yes |
| `ECNU_VISITOR_PASSWORD2` | Second default visitor password | Yes |
| `ECNU_VISITOR_REMARK` | Default visitor remark | No |

## Examples

```bash
ecnu -e default home status
chatenv token status -s ECNU -p default
chatenv token refresh ECNU default
ecnu -e default net check --json
ecnu -e default visitor default -I
```

`chatenv token refresh ECNU <profile>` runs one non-interactive OCR-backed auto-login using `ECNU_USERNAME` / `ECNU_PASSWORD` from the matching stable env profile, then lets ChatEnv write the runtime token-store record. It fails closed when the portal requires SMS verification or rejects all CAPTCHA candidates; use `ecnu -e <profile> home login ...` first for interactive login.
