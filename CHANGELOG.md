# Changelog

## Unreleased

### Added

- Add API-first ECNU campus-network `auth_client` wrapper in `chatecnu.network_auth`.
- Add `chatecnu network-auth login` and `chatecnu network-auth ensure-login` CLI commands for Linux deployments that already provide the external `auth_client` binary; login is fail-closed by default and requires explicit `--allow-argv-password` for the legacy `auth_client -p PASSWORD` path.
- Add ChatEnv fields `ECNU_AUTH_CLIENT` and `ECNU_AUTH_SETTING_FILE`.

### Notes

- ChatECNU does not vendor or redistribute the Linux-only `auth_client` binary; callers pass the runtime path explicitly or configure it through ChatEnv.

## 0.1.0 - 2026-06-27

### Added

- Initial ChatECNU release extracted from the former ChatNet ECNU application layer.
- Add `chatecnu` CLI for ECNU self-service portal workflows:
  - login/session status;
  - home/user/log reads;
  - visitor account list/get/create/update/delete/default sync;
  - optional CAPTCHA-assisted login.
- Add ChatEnv config provider entries for `ecnu` and `chatecnu`.
- Add optional `captcha` extra for OCR-backed CAPTCHA automation.
- Add ECNU docs, README, CI, docs preview, and tag-driven PyPI publishing workflow.

### Changed

- Depend on the released generic network foundation package: `ChatNet>=0.2.0,<0.3.0`.
- Use `chatnet.portal` reusable browser/session/table helpers instead of keeping generic network code inside ChatECNU.

### Notes

- ChatECNU owns ECNU application-layer behavior. ChatNet owns generic network helpers.
- The PyPI pending Trusted Publisher is configured for project `ChatECNU`, repo `ChatArch/ChatECNU`, workflow `publish.yml`, environment `(Any)`.
