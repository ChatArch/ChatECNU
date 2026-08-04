# ECNU Usage

ChatECNU splits ECNU capabilities into three groups: `home` for portal access, `net` for campus-network access, and `visitor` for visitor accounts.

## Portal {#portal}

Portal login creates an ECNU Web/API session used by home summary, user info, and visitor-account APIs.

```bash
ecnu home login --rounds 3 --topk 5 -I
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

SMS code flow:

```bash
ecnu home login --sms-code 123456 --rounds 3 --topk 5 -I
```

Manual CAPTCHA helpers remain hidden:

```bash
ecnu home login-init
ecnu home login --captcha ABCD -I
```

## Campus network access {#network-login}

Campus-network access manages local network authentication through the Linux x86_64 `auth_client` binary bundled in the PyPI package by default.

```bash
ecnu net check --json
ecnu net login -I --allow-argv-password
ecnu net logout -I
ecnu net ensure-login -I --allow-argv-password
```

`check` does not need a password. `login` shares `ECNU_USERNAME` / `ECNU_PASSWORD` with portal login; `logout` only needs the username. The wrapper does not pass `-c` by default; it uses a setting file only when `--setting-file` or `ECNU_AUTH_SETTING_FILE` is configured.

## Visitor accounts {#visitor}

```bash
ecnu visitor list
ecnu visitor get --id 10256703
ecnu visitor create --remark GuestA --dry-run -I
ecnu visitor default -I
```

Mutation commands support `--dry-run`.
