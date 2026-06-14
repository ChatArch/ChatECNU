# Changelog

## YYYY-MM-DD

### Added

- Add `chatnet ecnu` commands for ECNU portal login, session inspection, log queries, and visitor account management.
- Add optional `captcha` extra for OCR-backed `chatnet ecnu login-auto`.
- Add ECNU CLI documentation and a local selftest command.
- Add ChatEnv provider metadata and `ECNUConfig` for `~/.chatarch/envs/ECNU/.env`.

### Changed

- Load ECNU CLI defaults from chatenv and move default ECNU session/cache paths under `~/.chatarch/cache/chatnet/`.

### Fixed
