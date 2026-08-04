# 命令树

这页只列当前已实现的可见命令。隐藏诊断命令不放进主树。能力边界见 [能力地图](capability-map.md)，Python 映射见 [接口树](interface-tree.md)。

## 顶层命令

```text
ecnu
├── home      # ECNU 门户
├── net       # 校园网联网
└── visitor   # 访客账号
```

## home {#home}

```text
ecnu home
├── info      # 门户首页摘要
├── login     # 登录门户
├── logout    # 退出门户会话
├── status    # 门户会话状态
└── user      # 门户用户信息
```

门户状态是 ECNU Web/API 会话状态，用于 `info`、`user`、`visitor` 等门户接口。

## net {#net}

```text
ecnu net
├── check         # 检查在线状态，不需要密码
├── login         # 登录校园网
├── logout        # 退出校园网
└── ensure-login  # 离线时再登录
```

`net` 管理本机校园网出口认证。它默认使用 PyPI 包内置的 Linux x86_64 `auth_client`，也可通过 `--auth-client` / `ECNU_AUTH_CLIENT` 覆盖。

## visitor {#visitor}

```text
ecnu visitor
├── list      # 列表
├── get       # 查询单个账号
├── create    # 创建
├── default   # 维护默认访客账号
├── update    # 改备注或密码
└── delete    # 删除
```

修改类命令支持 `--dry-run`。

## 更新规则

- 新增可见命令时，同步更新本页。
- 计划中但未实现的能力不要写入命令树。
- 本页只列当前可用入口。
