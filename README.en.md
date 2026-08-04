# ChatECNU

ChatECNU is the ECNU campus portal and campus-network automation package extracted from ChatNet.

It includes the ECNU portal CLI plus an API-first, fail-closed wrapper for the external Linux `auth_client` campus-network binary. The binary is not vendored; pass its path with `--auth-client` or configure `ECNU_AUTH_CLIENT`.

```bash
# Check current auth_client login state; this does not require a password.
chatecnu network-auth check --auth-client /usr/local/bin/auth_client --json

# Put ECNU_USERNAME/ECNU_PASSWORD in process env or ChatEnv, or use -i to prompt.
# Default login refuses to pass passwords through auth_client process argv.
chatecnu network-auth ensure-login --auth-client /usr/local/bin/auth_client -I

# Legacy opt-in only after accepting same-host process-list exposure:
chatecnu network-auth ensure-login --auth-client /usr/local/bin/auth_client --allow-argv-password -I
```

Set `ECNU_AUTH_SETTING_FILE` only when your deployment needs an auth_client setting file; otherwise ChatECNU runs the same bare `auth_client check` shape as the legacy Precision scripts.
