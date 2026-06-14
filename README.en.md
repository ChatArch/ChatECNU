<div align="center">
    <a href="https://pypi.python.org/pypi/ChatNet">
        <img src="https://img.shields.io/pypi/v/ChatNet.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/OWNER/REPO/actions/workflows/ci.yml">
        <img src="https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://OWNER.github.io/REPO">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatNet

ChatNet package

## Quick Start

```bash
pip install -e ".[dev]"
chatnet hello ChatArch
chatnet ecnu selftest
python -m pytest -q
python -m build
```

## ECNU CLI

ECNU self-service portal commands live under `chatnet ecnu`:

The default config follows chatenv and lives in `~/.chatarch/envs/ECNU/.env`:

```bash
chatenv cat -t ecnu
```

```bash
chatnet ecnu login-init
chatnet ecnu login --username "$ECNU_USERNAME" --password "$ECNU_PASSWORD" --captcha ABCD
chatnet ecnu home
chatnet ecnu visitor list
chatnet ecnu visitor create --remark GuestB
chatnet ecnu visitor update --id 10256703 --remark GuestB --password 'Temp!235'
```

OCR-backed captcha login is optional:

```bash
pip install -e ".[captcha]"
chatnet ecnu login-auto --username "$ECNU_USERNAME" --password "$ECNU_PASSWORD"
```

Full usage guide: [`docs/ecnu.md`](docs/ecnu.md).

## CLI Contract

This template depends on `chatstyle>=0.1.0` and `chatenv>=0.1.1`. New commands should prefer:

- `CommandSchema` / `CommandField` for inputs.
- `add_interactive_option()` for the shared `-i/-I` switch.
- `resolve_command_inputs()` for missing args, defaults, TTY behavior, and validation.

## Layout

- `src/`: package source code
- `tests/code-tests/`: code tests and migrated historical tests
- `tests/cli-tests/`: real CLI tests, doc-first
- `tests/mock-cli-tests/`: mock/fake CLI tests, doc-first
- `docs/`: long-lived project docs built by mkdocs

## Development Notes

See `DEVELOP.md` and `AGENTS.md` before expanding the scaffold.
