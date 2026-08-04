# ChatECNU 文档

ChatECNU 是 ECNU 门户和校园网登录包装工具。它只做 ECNU 相关能力；通用网络能力归 ChatNet。

## 按场景选择

| 场景 | 入口 |
| --- | --- |
| 新机器安装与最小验证 | [快速开始](quickstart.md) |
| 查看当前可见命令 | [命令树](cli-tree.md) |
| 判断 ChatECNU / ChatNet / `auth_client` 边界 | [能力地图](capability-map.md) |
| 查看 Python 接口和命令行映射 | [接口树](interface-tree.md) |
| 门户登录、会话和访客账号 | [ECNU 使用](ecnu.md) |
| 校园网 `auth_client` 状态检查 | [校园网登录](ecnu.md#network-login) |

## 文档栏目

<div class="grid cards" markdown>

- **入门**

  [快速开始](quickstart.md)：安装、配置、最小验证。

- **命令与接口**

  [命令树](cli-tree.md) 看真实命令面；[能力地图](capability-map.md) 看责任边界；[接口树](interface-tree.md) 看 Python / CLI 映射。

- **使用指南**

  [ECNU 使用](ecnu.md)：门户登录、会话查询、访客账号、校园网登录。

</div>

## 当前边界

| 组件 | 责任 |
| --- | --- |
| ChatECNU | ECNU 门户、访客账号、校园网 `auth_client` 包装 |
| ChatNet | 通用网络、浏览器、表格和会话基础能力 |
| `auth_client` | 外部 Linux 程序，不随包分发 |
| ChatDNS / 证书 / Nginx | 不属于本包 |

## 常用入口

```bash
chatecnu --help
chatecnu auth check --auth-client /usr/local/bin/auth_client --json
chatecnu visitor --help
```
