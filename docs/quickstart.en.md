# Quickstart

## Install

```bash
pip install ChatECNU
```

Install CAPTCHA OCR support when needed:

```bash
pip install "ChatECNU[captcha]"
```

## Prepare ChatEnv

ChatECNU registers the ChatEnv type `ecnu`.

```bash
chatenv list
chatenv new default -t ecnu -I --yes
```

Common variables:

```text
ECNU_USERNAME=your account
ECNU_PASSWORD=your password
```

See [ChatEnv Variables](chatenv.md) for the full schema.

## Portal Smoke

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
```

## Campus Network Smoke

```bash
ecnu net check --json
ecnu net ensure-login -I --allow-argv-password
```

`check` does not need a password. `login` / `ensure-login` do not pass passwords through external process argv by default. Use `--allow-argv-password` only after accepting local process-list exposure.
