# Changelog

## Unreleased

### Changed

- 命令面重整为三组：`ecnu home ...`、`ecnu net ...`、`ecnu visitor ...`。
- 门户相关动作从顶层移入 `home`：`home login/info/status/user/logout`。
- 校园网联网只保留 `net`：`net check/login/logout/ensure-login`；不再注册 `auth` 或 `network-auth`。
- ChatEnv 对外类型收敛为 `ecnu`；门户和校园网共用 `ECNU_USERNAME` / `ECNU_PASSWORD`。
- 文档和命令树同步改为新结构。

## 0.1.1

### Added

- 新增 `chatecnu.network_auth`，提供 API 优先的 ECNU 校园网 `auth_client` 包装。
- 新增校园网检查、登录、退出和离线再登录能力；`check` 不需要凭据，`logout` 只需要用户名，登录默认拒绝执行，只有显式 `--allow-argv-password` 才使用旧的 `auth_client -p PASSWORD` 路径。
- 外部 `auth_client` 即使退出码为 0，只要输出缺设置文件等错误日志，也会转成结构化失败。
- 新增 ChatEnv 字段 `ECNU_AUTH_CLIENT` 和 `ECNU_AUTH_SETTING_FILE`；门户和校园网共用 `ECNU_USERNAME` / `ECNU_PASSWORD`。

## 0.1.0

- Initial package release.
