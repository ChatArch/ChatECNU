# 能力地图

这页回答“ChatECNU 负责什么”。命令调用方式见 [命令树](cli-tree.md)，Python 与命令行映射见 [接口树](interface-tree.md)。

## 当前能力

<div class="grid cards" markdown>

- **门户会话**

  登录、验证码初始化、会话状态、退出登录。

- **门户查询**

  首页摘要、用户信息、认证日志和详单日志读取。

- **访客账号**

  列表、查询、创建、默认账号维护、更新、删除。

- **校园网登录**

  包装外部 `auth_client`，提供状态检查、登录、离线再登录。

</div>

## 能力边界

| 能力 | 状态 | 入口 | 边界 |
| --- | --- | --- | --- |
| 门户登录 | 已实现 | `chatecnu login` | 需要 ECNU 账号和验证码流程 |
| 会话查询 | 已实现 | `status`、`home`、`user-info` | 依赖已登录会话或 Cookie |
| 访客账号 | 已实现 | `chatecnu visitor ...` | 修改类命令支持 `--dry-run` |
| 校园网在线检查 | 已实现 | `chatecnu auth check` | 不需要密码 |
| 校园网登录 | 已实现 | `auth login`、`auth ensure-login` | 默认拒绝 argv 密码 |
| ChatEnv 配置 | 已实现 | `ECNUConfig` | 密码和 Cookie 为敏感字段 |

## 安全默认值

- 不随包分发 Linux-only `auth_client`。
- 默认不把 ECNU 密码传入 `auth_client -p PASSWORD`。
- 只有显式 `--allow-argv-password` / `allow_argv_password=True` 才启用旧接口。
- stdout、stderr、JSON 输出和 redacted command 都会脱敏已解析密码。
- 进程环境优先于默认 ChatEnv；显式 `-e` / `--env-file` 才使用指定配置。

## 不在当前范围

| 项目 | 归属 |
| --- | --- |
| 通用网络基础能力 | ChatNet |
| DNS、证书、Nginx、域名入口 | ChatDNS / 运维项目 |
| 打包或再分发 `auth_client` | 不做 |
| 自动申请 ECNU 账号或变更学校系统 | 不做 |

## 验证入口

```bash
python -m pytest -q
mkdocs build --strict
chatecnu auth check --auth-client /usr/local/bin/auth_client --json
```
