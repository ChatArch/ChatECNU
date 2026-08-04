# ChatECNU

ChatECNU is the ECNU campus portal and campus-network automation package extracted from ChatNet.

It includes the ECNU portal CLI plus an API-first, fail-closed wrapper for the external Linux `auth_client` campus-network binary. The binary is not vendored; pass its path with `--auth-client` or configure `ECNU_AUTH_CLIENT`.

```bash
# Check status; no password needed.
chatecnu auth check --auth-client /usr/local/bin/auth_client --json

# Use env/ChatEnv or -i. Default login is fail-closed.
chatecnu auth ensure-login --auth-client /usr/local/bin/auth_client -I

# Legacy opt-in after accepting argv exposure:
chatecnu auth ensure-login --auth-client /usr/local/bin/auth_client --allow-argv-password -I
```

Set `ECNU_AUTH_SETTING_FILE` only when needed; otherwise checks use bare `auth_client check`. Old `network-auth` still works as a hidden alias for `auth`.
