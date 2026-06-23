<div align="center">
    <a href="https://pypi.python.org/pypi/ChatNet">
        <img src="https://img.shields.io/pypi/v/ChatNet.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatNet/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatNet/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://ChatArch.github.io/ChatNet">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatNet

ChatNet 是 ChatArch 系列的网络与校园网 CLI，当前提供 ECNU 自助服务平台登录、查询和访客管理能力。

## 快速开始

```bash
pip install -e ".[dev]"
chatnet ecnu --help
python -m pytest -q
python -m build
```

## ECNU CLI

ECNU 自助服务平台能力统一挂在 `chatnet ecnu` 下，覆盖登录、会话、日志查询和访客管理。

默认配置使用 chatenv 规范，位于 `~/.chatarch/envs/ECNU/.env`：

```bash
chatenv cat -t ecnu
```

```bash
chatnet ecnu login --username "$ECNU_USERNAME" --password "$ECNU_PASSWORD"
chatnet ecnu status
chatnet ecnu home
chatnet ecnu visitor list
chatnet ecnu visitor create --remark GuestB
chatnet ecnu visitor update --id 10256703 --remark GuestB --password 'Temp!235'
```

默认 `login` 会走自动验证码登录；自动识别依赖可选 OCR extra：

```bash
pip install -e ".[captcha]"
chatnet ecnu login --username "$ECNU_USERNAME" --password "$ECNU_PASSWORD"
```

缺少可恢复参数时，命令会按 ChatArch 规范进入交互补问；`-i` 强制交互，`-I` 禁止交互并快速失败。默认输出为人类可读摘要，显式传 `--json` 才输出原始 JSON。密码、Cookie、短信验证码等敏感值不要写入文档或提交记录。
默认 help 只展示常用命令；`login-init`、`login-auto`、`cookie-header`、`selftest` 和日志类 debug 命令仍可直接调用，但不在常规帮助中暴露。

完整使用文档见 [`docs/ecnu.md`](docs/ecnu.md)。

## CLI 规范

这个模板默认依赖 `chatstyle>=0.1.0` 和 `chatenv>=0.1.1`，新的命令应优先使用：

- `CommandSchema` / `CommandField` 描述输入。
- `add_interactive_option()` 提供统一 `-i/-I`。
- `resolve_command_inputs()` 统一缺参补问、默认值、TTY 与校验。

## 目录结构

- `src/`：包源码
- `tests/code-tests/`：代码测试和历史测试迁移
- `tests/cli-tests/`：真实 CLI 测试，doc-first
- `tests/mock-cli-tests/`：mock/fake CLI 测试，doc-first
- `docs/`：长期维护文档，由 mkdocs 构建

## 开发说明

扩展脚手架前，先阅读 `DEVELOP.md` 和 `AGENTS.md`。
