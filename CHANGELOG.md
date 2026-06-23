# Changelog

## Unreleased

### Changed

- Trim the default `chatnet ecnu --help` surface by hiding advanced/sensitive diagnostics such as `login-init`, `cookie-header`, `selftest`, low-level state/cookie options, and `visitor lock`.
- Add `chatnet ecnu status` as the user-facing redacted session/status command while keeping `session-info` as a hidden compatibility alias.
- Refactor ECNU login input resolution so manual and auto login share the same credential handling path.

## 2026-06-15

### Added

- Add `chatnet ecnu` commands for ECNU portal login, session inspection, log queries, and visitor account management.
- Add optional `captcha` extra for OCR-backed `chatnet ecnu login-auto`.
- Add ECNU CLI documentation and a local selftest command.
- Add ChatEnv provider metadata and `ECNUConfig` for `~/.chatarch/envs/ECNU/.env`.

### Changed

- 准备 `0.1.1` 发版，用于验证 PyPI Trusted Publishing 免 token 发布流程。

- 发布 workflow 改为显式 `v*` tag / `workflow_dispatch` 触发，使用 PyPI Trusted Publishing（`id-token: write` + `environment: pypi`），不再依赖仓库级 PyPI token secret。

- Load ECNU CLI defaults from chatenv and move default ECNU session/cache paths under `~/.chatarch/cache/chatnet/`.

### Fixed
