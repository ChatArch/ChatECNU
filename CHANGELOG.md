# Changelog

## Unreleased

### Changed

- 可见校园网命令缩短为 `chatecnu auth ...`，旧 `network-auth` 保留为隐藏兼容别名。
- 按 ChatArch MkDocs 规范重组文档：补齐中英文后缀式站点、首页导航、快速开始、命令树、能力地图、接口树和公共域名预览链接。
- 中文 README 和中文文档保持中文语境，英文内容移入 `.en.md` 文件。

## 0.1.1 - 2026-08-04

### Added

- 新增 `chatecnu.network_auth`，提供 API 优先的 ECNU 校园网 `auth_client` 包装。
- 新增 `chatecnu network-auth check`、`login`、`ensure-login`，用于已有外部 `auth_client` 的 Linux 部署；`check` 不需要凭据并默认执行裸 `auth_client check`，登录默认拒绝执行，只有显式 `--allow-argv-password` 才使用旧的 `auth_client -p PASSWORD` 路径。
- 外部 `auth_client` 即使退出码为 0，只要输出缺设置文件等错误日志，也会转成结构化失败。
- 新增 ChatEnv 字段 `ECNU_AUTH_CLIENT` 和 `ECNU_AUTH_SETTING_FILE`。

### Notes

- ChatECNU 不打包、不再分发 Linux-only `auth_client`；调用方通过参数或 ChatEnv 配置运行时路径。

## 0.1.0 - 2026-06-27

### Added

- 从原 ChatNet ECNU 应用层拆出首个 ChatECNU 版本。
- 新增 `chatecnu` CLI，覆盖 ECNU 门户流程：
  - 登录和会话状态；
  - 首页、用户信息和日志读取；
  - 访客账号列表、查询、创建、更新、删除和默认账号维护；
  - 可选验证码识别登录。
- 新增 ChatEnv 配置 provider：`ecnu` 和 `chatecnu`。
- 新增可选 `captcha` extra，用于 OCR 验证码自动化。
- 新增 ECNU 文档、README、CI、文档预览和 tag 驱动 PyPI 发布流程。

### Changed

- 依赖已发布的通用网络基础包：`ChatNet>=0.2.0,<0.3.0`。
- 使用 `chatnet.portal` 的浏览器、会话和表格基础能力，不再在 ChatECNU 内保留通用网络代码。

### Notes

- ChatECNU 负责 ECNU 应用层行为；ChatNet 负责通用网络基础能力。
- PyPI Trusted Publisher 已配置到项目 `ChatECNU`、仓库 `ChatArch/ChatECNU`、工作流 `publish.yml`。
