# 命令树

这页只列当前已实现的可见命令。隐藏诊断命令和旧别名不放进主树。能力边界见 [能力地图](capability-map.md)，Python 映射见 [接口树](interface-tree.md)。

## 顶层命令

```text
chatecnu
├── auth          # 校园网登录
├── home          # 首页摘要
├── login         # 门户登录
├── logout        # 退出登录
├── status        # 会话状态
├── user-info     # 用户信息
└── visitor       # 访客账号
```

旧命令 `network-auth` 仍可用，但只作为 `auth` 的隐藏兼容别名。

## 校园网登录

```text
chatecnu auth
├── check         # 检查在线状态，不需要密码
├── login         # 登录校园网，默认拒绝 argv 密码
└── ensure-login  # 离线时再登录
```

安全边界：默认不把密码传给 `auth_client -p PASSWORD`。确需兼容旧接口时，显式加 `--allow-argv-password`。

## 门户和会话

```text
chatecnu login     # 登录 ECNU 门户
chatecnu status    # 查看本地会话
chatecnu logout    # 退出门户会话
chatecnu home      # 首页摘要
chatecnu user-info # 用户信息
```

`login` 默认使用验证码识别；需要短信验证码时传 `--sms-code`。

## 访客账号

```text
chatecnu visitor
├── list           # 列表
├── get            # 查询单个账号
├── create         # 创建
├── default        # 维护默认访客账号
├── update         # 改备注或密码
└── delete         # 删除
```

修改类命令支持 `--dry-run`。

## 更新规则

- 新增可见命令时，同步更新本页。
- 计划中但未实现的能力不要写入命令树。
- 兼容别名只在说明里提，不放入主树。
