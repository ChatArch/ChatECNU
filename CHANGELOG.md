# Changelog

## 0.2.6

### Changed

- Migrate the top-level Click tree to `chatstyle.add_tree_option()`: `ecnu --tree` includes parameter signatures, while `ecnu --tree-brief` keeps nodes and descriptions without signatures.
- Raise the shared runtime bounds to `chatstyle>=0.2.0,<0.3.0` and `chatenv>=0.2.10,<0.3.0`.
- Keep `chatecnu` as a compatibility alias while using canonical `ecnu` as the tree root, with matching docs, package tests, and installed CLI smoke coverage.

## 0.2.5

### Changed

- Broaden the docs extra to the current ChatArch `mkdocs-material>=9.5,<10.0` window while preserving the existing Material icon renderer.
- Harden package publishing with a default-branch ancestry guard and an explicitly named OIDC PyPI publish step.
- Expand CI to Python 3.10/3.11/3.12 and add installed `ecnu --version` / `ecnu --tree` smoke checks.
- Point package homepage metadata at the ChatArch docs domain.
- This release only changes packaging, docs, and workflow guardrails; it does not change ECNU portal, campus-network, token-store, visitor-account, or `auth_client` runtime behavior.

## 0.2.4

### Changed

- 门户 Web/API 会话从 ChatEnv stable profile 中迁出，默认保存到 ChatEnv runtime token-store：`~/.chatarch/tokens/ECNU/<profile>.json`。
- 将 ChatEnv 依赖下界提高到 `chatenv>=0.2.7,<0.3.0`，并注册 `chatenv.token_refreshers` provider：`chatenv token refresh ECNU <profile>` 使用同名 stable env profile 发起非交互 OCR 自动登录，由 ChatEnv 写 runtime token-store；短信验证码或验证码候选失败时 fail closed。
- `ECNU_COOKIE` 不再作为 `ecnu` ChatEnv 类型的稳定变量；账号、密码、Base URL 和本机 `auth_client` 配置仍保留在 `envs/ECNU/<profile>.env`。
- `ecnu home status --json` 现在返回 token-store 路径、profile、token 类型和脱敏会话摘要；原始 Cookie 值不会输出。
- 隐藏的 `home cookie-header` raw Cookie 输出已禁用。

## 0.2.3

### Fixed

- 修复 MkDocs 首页 Material 图标没有渲染、裸露 `:material-*:` 文本的问题。
- 新增文档渲染回归测试，要求中英文首页生成 HTML 中不再出现 literal `:material-` token。

## 0.2.2

### Added

- 新增顶层 `ecnu --tree`，从当前 Click 注册命令面生成可回读命令树。

### Changed

- README、quickstart、命令树、接口树与 `ecnu --tree` 输出同步；隐藏诊断命令不进入主用户树。
- 将 ChatEnv 依赖下界提高到已发布的 `chatenv>=0.2.4,<0.3.0`。

## 0.2.1

### Fixed

- 内置 Linux x86_64 `auth_client` 到 PyPI wheel/sdist，默认 `ecnu net ...` 不再依赖内网下载或机器预装 PATH。
- `ecnu net check` 现在解析 `auth_client check` 的 stdout/stderr，JSON 和 human 输出都会显示 `online`、`account`、`username`。
- `ecnu net logout` 未提供用户名时会先执行 `auth_client check` 并从 `Username=...` 提取当前登录账号，再执行退出，和 `/nas/resources/ecnu_login.sh` 的 `mylogout` 逻辑一致。

## 0.2.0

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
