# Network recovery through the existing CLI

## Interface selection

- `ecnu net check/login/logout/ensure-login --interface en1` binds DNS and
  authentication to the selected macOS interface, without changing routes.
- The binary backend and unsupported platforms reject interface selection.

## Explicit user service

- `ecnu net ensure-login --interface en1 --install-service --interval 60`
  installs a per-user macOS LaunchAgent invoking `python -m chatecnu`.
- `--dry-run` performs read-only validation; it creates no files or jobs.
- `--service-status` reports the latest safe state; `--uninstall-service`
  removes only the owned job, retaining credentials and configuration.
- `--save-password` requires a local terminal and saves hidden input in the
  login Keychain. Passwords never appear in the plist, config or status output.
- There is no additional console-script entrypoint or copied agent script.

## Recovery boundaries

- DNS, reachability and authentication use the selected interface; another
  router or a disconnected interface never causes a login.
- Two failed HTTPS probes plus an explicit offline portal result trigger a
  login. An online portal, unknown status or missing/locked password does not.
- Failed attempts have a five-minute cooldown. Concurrent ticks do not overlap.
- Migrating an old job backs up its config/plist and restores them on failure.
