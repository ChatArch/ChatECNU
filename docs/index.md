# ChatECNU 文档

ChatECNU 提供 ECNU 门户和校园网联网的 Python API 与命令行工具。日常命令主推 `ecnu`。

<div class="grid cards" markdown>

-   :material-home: **门户**

    ---

    登录门户、查看首页摘要、会话状态和用户信息。

    [`ecnu home ...`](cli-tree.md#home)

-   :material-lan-connect: **校园网联网**

    ---

    使用 PyPI 包内置的 Linux x86_64 `auth_client`，检查、登录、退出或确保本机在线。

    [`ecnu net ...`](cli-tree.md#net)

-   :material-account-group: **访客账号**

    ---

    管理 ECNU 访客账号，修改类命令支持预演。

    [`ecnu visitor ...`](cli-tree.md#visitor)

-   :material-key: **ChatEnv 配置**

    ---

    使用 `ecnu` 类型保存账号、密码、Cookie 和本机联网配置。

    [查看变量](chatenv.md)

</div>

## 快速入口

| 目标 | 入口 |
| --- | --- |
| 安装并验证 | [快速开始](quickstart.md) |
| 查看完整命令树 | [命令树](cli-tree.md) |
| 区分能力边界 | [能力地图](capability-map.md) |
| 对照 Python API | [接口树](interface-tree.md) |
| 门户与校园网用法 | [ECNU 使用](ecnu.md) |
