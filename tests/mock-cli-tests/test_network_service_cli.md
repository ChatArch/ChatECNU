# Network recovery through the existing CLI

- `ecnu net ensure-login --install-service --interval 60` installs a per-user macOS LaunchAgent invoking the package.
- `--dry-run` performs read-only validation; it creates no files or jobs.
- `--service-status` reports the latest safe state and current system-selected interface; `--uninstall-service` removes only the owned job.
- The service follows the macOS routing table and does not accept an interface selector.
- Each run reloads `ECNU_USERNAME` and `ECNU_PASSWORD` from the selected ChatEnv ECNU profile. No account snapshot, password file, separate credential fallback, or explicit credential option is used.
- Two failed HTTPS probes plus an explicit offline portal result trigger a login. Unknown status and missing ChatEnv values do not.
- Failed attempts have a five-minute cooldown and concurrent ticks do not overlap.
